from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from cnpj_extractor.antibot import AntibotClient
from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sitemap import discover_sitemap_urls, fetch_all_company_urls, parse_urlset
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.utils import is_valid_email, normalize_email

FIZ_SITEMAP_INDEX = "https://diretorio.fiz.co/sitemap.xml"
FIZ_SITEMAP_PAGE = "https://diretorio.fiz.co/api/sitemap/empresas/1"
FIZ_BASE = "https://diretorio.fiz.co"


class FizPortugalSource(BaseSource):
    name = "Diretório FIZ (Portugal)"
    description = (
        "Base portuguesa com ~490.000 empresas via sitemap automático "
        "(diretorio.fiz.co). Descobre todas as páginas sozinho — sem inserir 1, 2, 3..."
    )
    country = "PT"

    def __init__(self, delay_seconds: float = 0.3, max_workers: int = 4, aggressive_antibot: bool = True):
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.aggressive_antibot = aggressive_antibot
        self._client = AntibotClient(
            delay_seconds=delay_seconds,
            aggressive=aggressive_antibot,
            use_playwright_fallback=aggressive_antibot,
        )
        self.session = self._client

    def discover_total_pages(self) -> int:
        result = self._client.fetch(FIZ_SITEMAP_PAGE)
        # Header não disponível via fetch — pedido extra leve
        try:
            resp = self._client.get(FIZ_SITEMAP_PAGE, timeout=30)
            total = resp.headers.get("x-sitemap-pages", "0")
            return int(total) if str(total).isdigit() else 0
        except Exception:
            return 98

    def discover_all_sitemap_urls(self, progress_callback: ProgressCallback = None) -> list[str]:
        return discover_sitemap_urls(FIZ_SITEMAP_INDEX, session=self.session)

    def discover_all_company_urls(self, progress_callback: ProgressCallback = None) -> list[str]:
        return fetch_all_company_urls(
            FIZ_SITEMAP_INDEX,
            session=self.session,
            progress_callback=progress_callback,
        )

    def _parse_company_page(self, html: str, url: str) -> CompanyEmail | None:
        for match in re.finditer(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
        ):
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

            if data.get("@type") not in {"Corporation", "LocalBusiness", "Organization"}:
                continue
            if data.get("@id", "").endswith("#organization") and "fiz.co/#organization" in data.get(
                "@id", ""
            ):
                continue
            if not data.get("taxID") and not data.get("legalName"):
                continue

            email = normalize_email(data.get("email", ""))
            if not is_valid_email(email):
                continue

            address = data.get("address") or {}
            locality = address.get("addressLocality", "")
            postal = address.get("postalCode", "")

            return CompanyEmail(
                cnpj=str(data.get("taxID", "")),
                email=email,
                razao_social=(data.get("legalName") or data.get("name") or "").strip(),
                nome_fantasia=(data.get("name") or "").strip(),
                telefone=(data.get("telephone") or "").strip(),
                uf=postal[:4] if postal else "",
                municipio=locality,
                cnae=(data.get("isicV4") or "").strip(),
                situacao="Ativa",
                pais="PT",
                fonte=self.name,
                website=(data.get("url") or "").strip(),
            )

        soup = BeautifulSoup(html, "lxml")
        title = soup.find("h1")
        legal_name = title.get_text(strip=True) if title else ""
        emails = re.findall(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html
        )
        for raw_email in emails:
            email = normalize_email(raw_email)
            if is_valid_email(email) and "fiz.co" not in email:
                nipc_match = re.search(r"NIPC\s*(\d{9})", html, re.I)
                return CompanyEmail(
                    cnpj=nipc_match.group(1) if nipc_match else "",
                    email=email,
                    razao_social=legal_name,
                    pais="PT",
                    fonte=self.name,
                )
        return None

    def fetch_company(self, url: str) -> CompanyEmail | None:
        result = self._client.fetch(url)
        if result.blocked or not result.text:
            return None
        time.sleep(self.delay_seconds)
        return self._parse_company_page(result.text, url)

    def _scrape_urls(
        self,
        urls: list[str],
        *,
        max_records: int | None,
        only_with_email: bool,
        progress_callback: ProgressCallback,
    ) -> Iterator[CompanyEmail]:
        seen: set[tuple[str, str]] = set()
        found = 0
        total = len(urls)
        completed = 0

        workers = 2 if self.aggressive_antibot else self.max_workers

        def worker(company_url: str) -> CompanyEmail | None:
            try:
                client = AntibotClient(
                    delay_seconds=self.delay_seconds,
                    aggressive=self.aggressive_antibot,
                    use_playwright_fallback=self.aggressive_antibot,
                )
                result = client.fetch(company_url)
                if result.blocked or not result.text:
                    return None
                return self._parse_company_page(result.text, company_url)
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(worker, url): url for url in urls}
            for future in as_completed(futures):
                completed += 1
                record = future.result()
                if record:
                    key = (record.cnpj, record.email)
                    if key not in seen:
                        seen.add(key)
                        if not only_with_email or is_valid_email(record.email):
                            yield record
                            found += 1
                            if max_records and found >= max_records:
                                executor.shutdown(wait=False, cancel_futures=True)
                                return

                if completed % 50 == 0 or completed == total:
                    self._report(
                        progress_callback,
                        completed / max(total, 1),
                        f"Empresas {completed:,}/{total:,} — {found:,} e-mails",
                    )

    def extract(
        self,
        *,
        auto_discover: bool = True,
        sitemap_index_url: str = FIZ_SITEMAP_INDEX,
        company_urls: list[str] | None = None,
        sitemap_pages: list[int] | None = None,
        max_sitemap_pages: int | None = None,
        aggressive_antibot: bool = True,
        distrito: str | None = None,
        only_with_email: bool = True,
        max_records: int | None = 500,
        progress_callback: ProgressCallback = None,
    ) -> Iterator[CompanyEmail]:
        self.aggressive_antibot = aggressive_antibot
        if aggressive_antibot:
            self._client = AntibotClient(
                delay_seconds=self.delay_seconds,
                aggressive=True,
                use_playwright_fallback=True,
            )
            self.session = self._client

        urls = company_urls or []

        if not urls and auto_discover:
            self._report(progress_callback, 0.0, "A descobrir todos os sitemaps automaticamente...")
            if sitemap_pages:
                template = "https://diretorio.fiz.co/api/sitemap/empresas/{page}"
                sitemap_urls = [template.format(page=page) for page in sitemap_pages]
            else:
                sitemap_urls = [
                    u for u in discover_sitemap_urls(sitemap_index_url, session=self.session)
                    if "/empresas/" in u
                ]
                if max_sitemap_pages:
                    sitemap_urls = sitemap_urls[:max_sitemap_pages]

            urls = []
            for index, sitemap_url in enumerate(sitemap_urls):
                result = self._client.fetch(sitemap_url)
                if result.text:
                    urls.extend(parse_urlset(result.text))
                self._report(
                    progress_callback,
                    (index + 1) / max(len(sitemap_urls), 1) * 0.3,
                    f"Sitemap {index + 1}/{len(sitemap_urls)} — {len(urls):,} URLs",
                )

        if distrito:
            distrito_lower = distrito.lower()
            urls = [url for url in urls if distrito_lower in url.lower()]

        self._report(
            progress_callback,
            0.3,
            f"Total: {len(urls):,} empresas para processar",
        )

        yield from self._scrape_urls(
            urls,
            max_records=max_records,
            only_with_email=only_with_email,
            progress_callback=lambda value, msg: self._report(
                progress_callback, 0.3 + value * 0.7, msg
            ),
        )
