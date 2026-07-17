from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.utils import is_valid_email, normalize_email

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SKIP_EMAIL_DOMAINS = {"example.com", "wixpress.com", "sentry.io", "schema.org"}


class WebScraperSource(BaseSource):
    """Scraper universal para qualquer site, lista de URLs ou página única."""

    name = "Scraper Universal"
    description = "Extrai e-mails de qualquer site, lista de URLs ou ficheiro importado."
    country = "GLOBAL"

    def __init__(self, delay_seconds: float = 0.3, max_workers: int = 6):
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
            }
        )
        self._json_ld_parser = GenericSitemapSource(delay_seconds=delay_seconds)

    def _extract_emails_from_html(self, html: str, page_url: str) -> list[CompanyEmail]:
        records: list[CompanyEmail] = []

        # JSON-LD (schema.org)
        json_ld = self._json_ld_parser._parse_json_ld(html, page_url)
        if json_ld:
            records.append(json_ld)

        # mailto: links
        soup = BeautifulSoup(html, "lxml")
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if href.lower().startswith("mailto:"):
                email = normalize_email(href[7:].split("?")[0])
                if is_valid_email(email):
                    records.append(
                        CompanyEmail(
                            cnpj="",
                            email=email,
                            razao_social=link.get_text(strip=True)[:80],
                            fonte=page_url,
                        )
                    )

        # Regex no HTML
        title = soup.find("title")
        page_title = title.get_text(strip=True) if title else ""
        h1 = soup.find("h1")
        company_name = h1.get_text(strip=True) if h1 else page_title

        found_emails: set[str] = set()
        for match in EMAIL_RE.findall(html):
            email = normalize_email(match)
            domain = email.split("@")[-1] if "@" in email else ""
            if not is_valid_email(email):
                continue
            if domain in SKIP_EMAIL_DOMAINS:
                continue
            if "example@" in email or email.endswith(".png") or email.endswith(".jpg"):
                continue
            if email in found_emails:
                continue
            found_emails.add(email)
            records.append(
                CompanyEmail(
                    cnpj="",
                    email=email,
                    razao_social=company_name[:100],
                    fonte=page_url,
                )
            )

        return records

    def fetch_page(self, url: str) -> list[CompanyEmail]:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        time.sleep(self.delay_seconds)
        return self._extract_emails_from_html(response.text, url)

    def discover_links(self, start_url: str, max_links: int = 50) -> list[str]:
        """Descobre links na mesma página para scraping básico."""
        try:
            response = self.session.get(start_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            return [start_url]

        soup = BeautifulSoup(response.text, "lxml")
        base = urlparse(start_url)
        base_domain = base.netloc
        urls = [start_url]
        seen = {start_url}

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            full = urljoin(start_url, href)
            parsed = urlparse(full)
            if parsed.netloc != base_domain:
                continue
            if full in seen:
                continue
            seen.add(full)
            urls.append(full)
            if len(urls) >= max_links:
                break

        return urls

    def extract(
        self,
        *,
        urls: list[str] | None = None,
        start_url: str | None = None,
        crawl_same_site: bool = False,
        max_crawl_pages: int = 30,
        only_with_email: bool = True,
        max_records: int | None = 500,
        progress_callback: ProgressCallback = None,
        source_name: str = "",
    ) -> Iterator[CompanyEmail]:
        target_urls = list(urls or [])
        if start_url:
            if crawl_same_site:
                self._report(progress_callback, 0.05, "A descobrir links no site...")
                target_urls = self.discover_links(start_url, max_links=max_crawl_pages)
            elif start_url not in target_urls:
                target_urls.insert(0, start_url)

        if not target_urls:
            return

        seen: set[tuple[str, str]] = set()
        found = 0
        total = len(target_urls)
        completed = 0

        def worker(page_url: str) -> list[CompanyEmail]:
            try:
                return self.fetch_page(page_url)
            except requests.RequestException:
                return []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(worker, url): url for url in target_urls}
            for future in as_completed(futures):
                completed += 1
                for record in future.result():
                    if source_name:
                        record.fonte = source_name
                    key = (record.cnpj or record.email, record.email)
                    if key in seen:
                        continue
                    if only_with_email and not is_valid_email(record.email):
                        continue
                    seen.add(key)
                    yield record
                    found += 1
                    if max_records and found >= max_records:
                        executor.shutdown(wait=False, cancel_futures=True)
                        return

                if completed % 5 == 0 or completed == total:
                    self._report(
                        progress_callback,
                        completed / max(total, 1),
                        f"{completed:,}/{total:,} páginas — {found:,} e-mails",
                    )
