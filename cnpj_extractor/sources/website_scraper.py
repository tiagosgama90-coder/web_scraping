from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from cnpj_extractor.antibot import AntibotClient, get_antibot_client
from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.utils import is_valid_email, normalize_email

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SKIP_EMAIL_DOMAINS = {"example.com", "wixpress.com", "sentry.io", "schema.org", "cloudflare.com"}


class WebScraperSource(BaseSource):
    """Scraper universal com bypass anti-bot para qualquer site."""

    name = "Scraper Universal (Anti-Bot)"
    description = "Extrai e-mails de qualquer site — contorna Cloudflare e proteções anti-bot."
    country = "GLOBAL"

    def __init__(
        self,
        delay_seconds: float = 0.4,
        max_workers: int = 4,
        aggressive_antibot: bool = True,
    ):
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.aggressive_antibot = aggressive_antibot
        self._client = AntibotClient(
            delay_seconds=delay_seconds,
            use_playwright_fallback=aggressive_antibot,
            aggressive=aggressive_antibot,
        )
        self._json_ld_parser = GenericSitemapSource(
            delay_seconds=delay_seconds, aggressive_antibot=aggressive_antibot
        )

    def _extract_emails_from_html(self, html: str, page_url: str) -> list[CompanyEmail]:
        records: list[CompanyEmail] = []

        json_ld = self._json_ld_parser._parse_json_ld(html, page_url)
        if json_ld:
            records.append(json_ld)

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
            if "example@" in email or email.endswith((".png", ".jpg", ".gif")):
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
        result = self._client.fetch(url)
        if result.blocked or not result.text:
            return []
        return self._extract_emails_from_html(result.text, url)

    def discover_links(self, start_url: str, max_links: int = 50) -> list[str]:
        result = self._client.fetch(start_url)
        if result.blocked or not result.text:
            return [start_url]

        soup = BeautifulSoup(result.text, "lxml")
        base_domain = urlparse(start_url).netloc
        urls = [start_url]
        seen = {start_url}

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            full = urljoin(start_url, href)
            if urlparse(full).netloc != base_domain or full in seen:
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
        aggressive_antibot: bool | None = None,
    ) -> Iterator[CompanyEmail]:
        if aggressive_antibot is not None:
            self.aggressive_antibot = aggressive_antibot
            self._client.aggressive = aggressive_antibot

        target_urls = list(urls or [])
        if start_url:
            if crawl_same_site:
                self._report(progress_callback, 0.05, "A descobrir links (modo anti-bot)...")
                target_urls = self.discover_links(start_url, max_links=max_crawl_pages)
            elif start_url not in target_urls:
                target_urls.insert(0, start_url)

        if not target_urls:
            return

        # Uma instância de cliente por thread para evitar conflitos
        seen: set[tuple[str, str]] = set()
        found = 0
        total = len(target_urls)
        completed = 0
        blocked_count = 0

        def worker(page_url: str) -> tuple[list[CompanyEmail], bool]:
            client = AntibotClient(
                delay_seconds=self.delay_seconds,
                aggressive=self.aggressive_antibot,
                use_playwright_fallback=self.aggressive_antibot,
            )
            try:
                result = client.fetch(page_url)
                if result.blocked:
                    return [], True
                scraper = WebScraperSource(
                    delay_seconds=self.delay_seconds,
                    max_workers=1,
                    aggressive_antibot=self.aggressive_antibot,
                )
                scraper._client = client
                return scraper._extract_emails_from_html(result.text, page_url), False
            except Exception:
                return [], True

        workers = 2 if self.aggressive_antibot else self.max_workers
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(worker, url): url for url in target_urls}
            for future in as_completed(futures):
                completed += 1
                page_records, was_blocked = future.result()
                if was_blocked:
                    blocked_count += 1

                for record in page_records:
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

                status = f"{completed:,}/{total:,} — {found:,} e-mails"
                if blocked_count:
                    status += f" ({blocked_count} bloqueados)"
                if completed % 3 == 0 or completed == total:
                    self._report(progress_callback, completed / max(total, 1), status)
