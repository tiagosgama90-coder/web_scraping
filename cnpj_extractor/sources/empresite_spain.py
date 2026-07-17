from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from cnpj_extractor.antibot import AntibotClient
from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sitemap import discover_sitemap_urls, parse_urlset
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.utils import is_valid_email, normalize_email

EMPRESITE_SITEMAP_INDEX = "https://empresite.eleconomista.es/sitemap_EMP_ES_index.xml"
EMPRESITE_BASE = "https://empresite.eleconomista.es"
SKIP_EMAIL_DOMAINS = {"eleconomista.es", "empresite.es", "informa.es", "informadb.es"}
SPANISH_CIF_RE = re.compile(r"\b[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]\b")
MAILTO_RE = re.compile(r"mailto:([^\"'>\s?]+)", re.I)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


class EmpresiteSpainSource(BaseSource):
    name = "Empresite (Espanha)"
    description = (
        "Diretório espanhol com ~4 milhões de empresas (eleconomista.es/empresite). "
        "Extrai e-mails publicados nas fichas gratuitas via sitemap automático."
    )
    country = "ES"

    def __init__(self, delay_seconds: float = 0.4, max_workers: int = 4, aggressive_antibot: bool = True):
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.aggressive_antibot = aggressive_antibot
        self._client = AntibotClient(
            delay_seconds=delay_seconds,
            aggressive=aggressive_antibot,
            use_playwright_fallback=aggressive_antibot,
        )
        self.session = self._client

    def _extract_emails(self, html: str) -> list[str]:
        candidates: list[str] = []
        for raw in MAILTO_RE.findall(html):
            candidates.append(normalize_email(raw.split("?")[0]))
        candidates.extend(normalize_email(e) for e in EMAIL_RE.findall(html))

        seen: set[str] = set()
        result: list[str] = []
        for email in candidates:
            if not email or email in seen:
                continue
            domain = email.split("@")[-1].lower()
            if any(skip in domain for skip in SKIP_EMAIL_DOMAINS):
                continue
            if is_valid_email(email):
                seen.add(email)
                result.append(email)
        return result

    def _extract_cif(self, html: str) -> str:
        match = SPANISH_CIF_RE.search(html)
        return match.group(0) if match else ""

    def _parse_company_page(self, html: str, url: str) -> CompanyEmail | None:
        emails = self._extract_emails(html)
        if not emails:
            return None

        soup = BeautifulSoup(html, "lxml")
        title = soup.find("h1")
        legal_name = title.get_text(strip=True) if title else ""

        cif = self._extract_cif(html)
        telefone = ""
        phone_match = re.search(r"tel:(\+?[\d\s\-]+)", html, re.I)
        if phone_match:
            telefone = phone_match.group(1).strip()

        municipio = ""
        province = ""
        for meta in soup.find_all("meta"):
            name = (meta.get("name") or meta.get("property") or "").lower()
            content = (meta.get("content") or "").strip()
            if "locality" in name or "municipio" in name:
                municipio = content
            if "region" in name or "provincia" in name:
                province = content

        return CompanyEmail(
            cnpj=cif,
            email=emails[0],
            razao_social=legal_name,
            telefone=telefone,
            uf=province,
            municipio=municipio,
            pais="ES",
            fonte=self.name,
            website=url,
        )

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
                    key = (record.cnpj or record.email, record.email)
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
        sitemap_index_url: str = EMPRESITE_SITEMAP_INDEX,
        max_sitemap_pages: int | None = None,
        provincia: str | None = None,
        aggressive_antibot: bool = True,
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

        self._report(progress_callback, 0.0, "A descobrir sitemaps Empresite (Espanha)...")
        sitemap_urls = discover_sitemap_urls(sitemap_index_url, session=self.session)
        if not sitemap_urls:
            sitemap_urls = [sitemap_index_url]
        if max_sitemap_pages:
            sitemap_urls = sitemap_urls[:max_sitemap_pages]

        urls: list[str] = []
        for index, sitemap_url in enumerate(sitemap_urls):
            result = self._client.fetch(sitemap_url)
            if result.text:
                urls.extend(parse_urlset(result.text))
            self._report(
                progress_callback,
                (index + 1) / max(len(sitemap_urls), 1) * 0.25,
                f"Sitemap {index + 1}/{len(sitemap_urls)} — {len(urls):,} URLs",
            )

        if provincia:
            provincia_lower = provincia.lower()
            urls = [url for url in urls if provincia_lower in url.lower()]

        # Em modo limitado, não enfileirar milhões de URLs de uma vez
        if max_records:
            url_scan_cap = max(max_records * 50, 500)
            urls = urls[:url_scan_cap]
        elif max_sitemap_pages:
            urls = urls[:25000 * max_sitemap_pages]

        self._report(
            progress_callback,
            0.25,
            f"Total: {len(urls):,} empresas para processar",
        )

        yield from self._scrape_urls(
            urls,
            max_records=max_records,
            only_with_email=only_with_email,
            progress_callback=lambda value, msg: self._report(
                progress_callback, 0.25 + value * 0.75, msg
            ),
        )
