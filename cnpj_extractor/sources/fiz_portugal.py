from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

import requests
from bs4 import BeautifulSoup

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

    def __init__(self, delay_seconds: float = 0.2, max_workers: int = 8):
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; Company-Email-Extractor/1.1; +https://diretorio.fiz.co)"
                ),
                "Accept-Language": "pt-PT,pt;q=0.9",
            }
        )

    def discover_total_pages(self) -> int:
        response = self.session.get(FIZ_SITEMAP_PAGE, timeout=30)
        response.raise_for_status()
        total = response.headers.get("x-sitemap-pages", "0")
        return int(total) if str(total).isdigit() else 0

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
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        time.sleep(self.delay_seconds)
        return self._parse_company_page(response.text, url)

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

        def worker(company_url: str) -> CompanyEmail | None:
            try:
                return self.fetch_company(company_url)
            except requests.RequestException:
                return None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
        distrito: str | None = None,
        only_with_email: bool = True,
        max_records: int | None = 500,
        progress_callback: ProgressCallback = None,
    ) -> Iterator[CompanyEmail]:
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
                response = self.session.get(sitemap_url, timeout=60)
                response.raise_for_status()
                urls.extend(parse_urlset(response.text))
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
