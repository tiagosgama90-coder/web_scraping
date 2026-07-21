from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

import requests

from cnpj_extractor.antibot import AntibotClient
from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sitemap import discover_sitemap_urls, fetch_all_company_urls, parse_urlset
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.sector_filters import matches_sector
from cnpj_extractor.utils import is_valid_email, normalize_email

CORPORATION_TYPES = {"Corporation", "LocalBusiness", "Organization"}


class GenericSitemapSource(BaseSource):
    """Scraper genérico para qualquer site com sitemap XML semelhante."""

    name = "Sitemap Genérico (Anti-Bot)"
    description = (
        "Sitemap XML com bypass anti-bot. Descobre todas as páginas automaticamente."
    )
    country = "GLOBAL"

    def __init__(self, delay_seconds: float = 0.4, max_workers: int = 4, aggressive_antibot: bool = True):
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.aggressive_antibot = aggressive_antibot
        self._client = AntibotClient(
            delay_seconds=delay_seconds,
            aggressive=aggressive_antibot,
            use_playwright_fallback=aggressive_antibot,
        )
        self.session = self._client  # compatível com sitemap.py

    def _parse_json_ld(self, html: str, source_url: str) -> CompanyEmail | None:
        for match in re.finditer(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
        ):
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") not in CORPORATION_TYPES:
                    continue

                email = normalize_email(item.get("email", ""))
                if not is_valid_email(email):
                    continue

                tax_id = (
                    str(item.get("taxID", ""))
                    or str(item.get("vatID", "")).replace("PT", "")
                    or ""
                )
                address = item.get("address") or {}
                if isinstance(address, list):
                    address = address[0] if address else {}

                return CompanyEmail(
                    cnpj=tax_id,
                    email=email,
                    razao_social=(item.get("legalName") or item.get("name") or "").strip(),
                    nome_fantasia=(item.get("name") or "").strip(),
                    telefone=(item.get("telephone") or "").strip(),
                    municipio=(address.get("addressLocality") or "").strip(),
                    uf=(address.get("postalCode") or "")[:4],
                    cnae=(item.get("isicV4") or "").strip(),
                    situacao="",
                    pais="",
                    fonte=source_url,
                    website=(item.get("url") or "").strip(),
                )

        emails = re.findall(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html
        )
        for raw in emails:
            email = normalize_email(raw)
            if is_valid_email(email):
                return CompanyEmail(
                    cnpj="",
                    email=email,
                    fonte=source_url,
                )
        return None

    def fetch_company(self, url: str) -> CompanyEmail | None:
        result = self._client.fetch(url)
        if result.blocked or not result.text:
            return None
        time.sleep(self.delay_seconds)
        return self._parse_json_ld(result.text, url)

    def extract(
        self,
        *,
        sitemap_url: str,
        auto_discover: bool = True,
        include_all_sitemaps: bool = False,
        aggressive_antibot: bool = True,
        only_with_email: bool = True,
        max_records: int | None = 500,
        sector_filter: str | None = None,
        progress_callback: ProgressCallback = None,
    ) -> Iterator[CompanyEmail]:
        self.aggressive_antibot = aggressive_antibot
        if aggressive_antibot != self._client.aggressive:
            self._client = AntibotClient(
                delay_seconds=self.delay_seconds,
                aggressive=aggressive_antibot,
                use_playwright_fallback=aggressive_antibot,
            )
            self.session = self._client

        self._report(progress_callback, 0.0, "A descobrir sitemaps (anti-bot)...")

        if auto_discover:
            all_sitemaps = discover_sitemap_urls(sitemap_url, session=self.session)
            if include_all_sitemaps:
                sitemap_urls = all_sitemaps or [sitemap_url]
            else:
                sitemap_urls = [u for u in all_sitemaps if "/empresas" in u.lower() or not all_sitemaps]
                if not sitemap_urls:
                    sitemap_urls = all_sitemaps or [sitemap_url]
            urls: list[str] = []
            for index, sm_url in enumerate(sitemap_urls):
                result = self._client.fetch(sm_url)
                if result.text:
                    urls.extend(parse_urlset(result.text))
                if progress_callback:
                    progress_callback(
                        (index + 1) / len(sitemap_urls) * 0.35,
                        f"Sitemap {index + 1}/{len(sitemap_urls)} — {len(urls):,} URLs",
                    )
        else:
            result = self._client.fetch(sitemap_url)
            urls = parse_urlset(result.text) if result.text else []

        self._report(
            progress_callback,
            0.35,
            f"{len(urls):,} URLs encontrados — a extrair e-mails...",
        )

        seen: set[tuple[str, str]] = set()
        found = 0
        total = len(urls)
        completed = 0

        def worker(company_url: str) -> CompanyEmail | None:
            try:
                return self.fetch_company(company_url)
            except requests.RequestException:
                return None

        workers = 2 if self.aggressive_antibot else self.max_workers
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(worker, url): url for url in urls}
            for future in as_completed(futures):
                completed += 1
                record = future.result()
                if record and sector_filter and not matches_sector(record.cnae, sector_filter):
                    record = None
                if record:
                    key = (record.cnpj or record.email, record.email)
                    if key not in seen:
                        seen.add(key)
                        if not only_with_email or is_valid_email(record.email):
                            yield record
                            found += 1
                            if max_records and found >= max_records:
                                executor.shutdown(wait=False, cancel_futures=True)
                                return

                if completed % 25 == 0 or completed == total:
                    self._report(
                        progress_callback,
                        0.35 + (completed / max(total, 1)) * 0.65,
                        f"{completed:,}/{total:,} páginas — {found:,} e-mails",
                    )
