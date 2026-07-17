from __future__ import annotations

import json
import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.utils import clean_cnpj, is_valid_email, normalize_email

SITE_BASE = "https://dadosbrasil.net/pt/cnpj/"
API_JSON_LINK_PATTERN = re.compile(r"https://api\.dadosbrasil\.net/api/v1/companies/\d+")


class DadosBrasilScraperSource(BaseSource):
    name = "DadosBrasil (Web Scraper)"
    description = (
        "Extrai dados via páginas HTML do dadosbrasil.net. Usa a API JSON embutida "
        "nas páginas quando disponível."
    )

    def __init__(self, delay_seconds: float = 0.3):
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; CNPJ-Email-Extractor/1.0; +https://dadosbrasil.net)"
                ),
                "Accept-Language": "pt-BR,pt;q=0.9",
            }
        )

    def _fetch_page(self, cnpj_base: str) -> str:
        url = f"{SITE_BASE}{clean_cnpj(cnpj_base)[:8]}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        time.sleep(self.delay_seconds)
        return response.text

    def _extract_api_url(self, html: str) -> str | None:
        match = API_JSON_LINK_PATTERN.search(html)
        return match.group(0) if match else None

    def _parse_from_api(self, api_url: str, legal_name_hint: str = "") -> list[CompanyEmail]:
        response = self.session.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        legal_name = (data.get("legal_name") or legal_name_hint or "").strip()
        records: list[CompanyEmail] = []

        establishment = data.get("establishment") or {}
        email = normalize_email(establishment.get("email", ""))
        if is_valid_email(email):
            tax_id = clean_cnpj(establishment.get("tax_id", ""))
            state = establishment.get("state") or {}
            city = establishment.get("city") or {}
            records.append(
                CompanyEmail(
                    cnpj=tax_id,
                    email=email,
                    razao_social=legal_name,
                    nome_fantasia=(establishment.get("trade_name") or "").strip(),
                    telefone="",
                    uf=(state.get("code") or "").strip(),
                    municipio=(city.get("name") or "").strip(),
                    cnae="",
                    situacao=str(establishment.get("registration_status", "")),
                    fonte=self.name,
                )
            )
        return records

    def _parse_from_html(self, html: str, cnpj_base: str) -> list[CompanyEmail]:
        soup = BeautifulSoup(html, "lxml")
        legal_name = ""
        title = soup.find("h1")
        if title:
            legal_name = title.get_text(strip=True)

        records: list[CompanyEmail] = []
        text = soup.get_text(" ", strip=True)
        emails = set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text))
        for email in emails:
            normalized = normalize_email(email)
            if is_valid_email(normalized):
                records.append(
                    CompanyEmail(
                        cnpj=clean_cnpj(cnpj_base)[:8] + "000101",
                        email=normalized,
                        razao_social=legal_name,
                        fonte=self.name,
                    )
                )
        return records

    def scrape_cnpj(self, cnpj: str) -> list[CompanyEmail]:
        base = clean_cnpj(cnpj)[:8]
        html = self._fetch_page(base)
        api_url = self._extract_api_url(html)
        if api_url:
            try:
                return self._parse_from_api(api_url)
            except (requests.RequestException, json.JSONDecodeError):
                pass
        return self._parse_from_html(html, base)

    def extract(
        self,
        *,
        cnpj_list: list[str],
        max_records: int | None = None,
        progress_callback: ProgressCallback = None,
    ) -> Iterator[CompanyEmail]:
        seen: set[tuple[str, str]] = set()
        found = 0
        total = len(cnpj_list)
        for index, cnpj in enumerate(cnpj_list):
            for record in self.scrape_cnpj(cnpj):
                key = (record.cnpj, record.email)
                if key in seen:
                    continue
                seen.add(key)
                yield record
                found += 1
                if max_records and found >= max_records:
                    return
            self._report(
                progress_callback,
                (index + 1) / max(total, 1),
                f"Scraping {index + 1}/{total}",
            )
