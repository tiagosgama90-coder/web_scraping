from __future__ import annotations

import random
import re
import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from cnpj_extractor.proxy_config import get_active_proxy, playwright_proxy, requests_proxies

# Indicadores de bloqueio anti-bot na resposta HTML
BLOCK_PATTERNS = [
    r"just a moment",
    r"checking your browser",
    r"cf-browser-verification",
    r"challenge-platform",
    r"attention required",
    r"access denied",
    r"please enable cookies",
    r"ddos-guard",
    r"captcha",
    r"bot detection",
    r"unusual traffic",
]

USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
]

BROWSER_IMPERSONATIONS = ["chrome120", "chrome119", "chrome110", "edge101", "safari17_0"]


@dataclass
class FetchResult:
    url: str
    text: str
    status_code: int
    method: str
    blocked: bool = False
    headers: dict | None = None


class AntibotClient:
    """
    Cliente HTTP com várias camadas anti-bot:
    1. curl_cffi (imita TLS fingerprint do Chrome)
    2. cloudscraper (resolve desafios Cloudflare básicos)
    3. Playwright headless (browser real — último recurso)
    4. requests padrão (fallback)
    """

    _playwright_available: bool | None = None

    def __init__(
        self,
        *,
        delay_seconds: float = 0.4,
        max_retries: int = 4,
        use_playwright_fallback: bool = True,
        aggressive: bool = True,
        proxy_url: str | None = None,
    ):
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.use_playwright_fallback = use_playwright_fallback
        self.aggressive = aggressive
        self.proxy_url = proxy_url if proxy_url is not None else get_active_proxy()
        self._local = threading.local()
        self._playwright_lock = threading.Lock()

    def _proxies(self) -> dict[str, str] | None:
        if not self.proxy_url:
            return None
        return {"http": self.proxy_url, "https": self.proxy_url}

    def _random_headers(self, referer: str | None = None) -> dict[str, str]:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none" if not referer else "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        if referer:
            headers["Referer"] = referer
        return headers

    def _is_blocked(self, status_code: int, html: str) -> bool:
        if status_code in {403, 429, 503, 520, 521, 522, 523}:
            return True
        lower = (html or "").lower()[:8000]
        return any(re.search(pat, lower) for pat in BLOCK_PATTERNS)

    def _get_curl_session(self) -> Any | None:
        try:
            from curl_cffi import requests as curl_requests

            if not hasattr(self._local, "curl_session"):
                impersonate = random.choice(BROWSER_IMPERSONATIONS)
                self._local.curl_session = curl_requests.Session(impersonate=impersonate)
            return self._local.curl_session
        except ImportError:
            return None

    def _get_cloudscraper_session(self) -> Any | None:
        try:
            import cloudscraper

            if not hasattr(self._local, "cloud_session"):
                self._local.cloud_session = cloudscraper.create_scraper(
                    browser={"browser": "chrome", "platform": "windows", "mobile": False}
                )
            return self._local.cloud_session
        except ImportError:
            return None

    def _get_requests_session(self) -> requests.Session:
        if not hasattr(self._local, "req_session"):
            session = requests.Session()
            session.headers.update(self._random_headers())
            self._local.req_session = session
        return self._local.req_session

    def _fetch_curl_cffi(self, url: str, referer: str | None) -> FetchResult | None:
        session = self._get_curl_session()
        if not session:
            return None
        try:
            for impersonate in BROWSER_IMPERSONATIONS:
                try:
                    resp = session.get(
                        url,
                        headers=self._random_headers(referer),
                        timeout=45,
                        allow_redirects=True,
                        impersonate=impersonate,
                        proxies=self._proxies(),
                    )
                    text = resp.text
                    blocked = self._is_blocked(resp.status_code, text)
                    hdrs = dict(resp.headers) if hasattr(resp, "headers") else {}
                    if not blocked or resp.status_code == 200:
                        return FetchResult(
                            url, text, resp.status_code, f"curl_cffi/{impersonate}", blocked, hdrs
                        )
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _fetch_cloudscraper(self, url: str, referer: str | None) -> FetchResult | None:
        session = self._get_cloudscraper_session()
        if not session:
            return None
        try:
            resp = session.get(
                url, headers=self._random_headers(referer), timeout=45, proxies=self._proxies()
            )
            text = resp.text
            return FetchResult(
                url, text, resp.status_code, "cloudscraper", self._is_blocked(resp.status_code, text)
            )
        except Exception:
            return None

    def _fetch_requests(self, url: str, referer: str | None) -> FetchResult:
        session = self._get_requests_session()
        session.headers.update(self._random_headers(referer))
        resp = session.get(url, timeout=45, allow_redirects=True, proxies=self._proxies())
        text = resp.text
        return FetchResult(url, text, resp.status_code, "requests", self._is_blocked(resp.status_code, text))

    def _fetch_playwright(self, url: str) -> FetchResult | None:
        if not self.use_playwright_fallback:
            return None
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return None

        pw_proxy = playwright_proxy() if self.proxy_url else None

        with self._playwright_lock:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                        ],
                    )
                    context_kwargs: dict = {
                        "user_agent": random.choice(USER_AGENTS),
                        "locale": "pt-PT",
                        "viewport": {"width": 1366, "height": 768},
                    }
                    if pw_proxy:
                        context_kwargs["proxy"] = pw_proxy
                    context = browser.new_context(**context_kwargs)
                    context.add_init_script(
                        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                    )
                    page = context.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(2500)
                    text = page.content()
                    browser.close()
                    blocked = self._is_blocked(200, text)
                    return FetchResult(url, text, 200, "playwright", blocked)
            except Exception:
                return None

    def fetch(self, url: str, referer: str | None = None) -> FetchResult:
        """Obtém HTML com escalada automática entre métodos anti-bot."""
        parsed = urlparse(url)
        if not referer and parsed.scheme and parsed.netloc:
            referer = f"{parsed.scheme}://{parsed.netloc}/"

        last_result: FetchResult | None = None

        for attempt in range(self.max_retries):
            if attempt > 0:
                wait = self.delay_seconds * (2 ** attempt) + random.uniform(0.5, 2.0)
                time.sleep(wait)

            methods: list = []
            if self.aggressive:
                methods.extend([self._fetch_curl_cffi, self._fetch_cloudscraper])
            methods.append(lambda u, r: self._fetch_requests(u, r))

            if attempt >= 2 and self.use_playwright_fallback:
                methods.append(lambda u, r: self._fetch_playwright(u))

            for method in methods:
                try:
                    if method == self._fetch_playwright:
                        result = method(url)
                    else:
                        result = method(url, referer)

                    if result is None:
                        continue

                    last_result = result
                    if not result.blocked and result.status_code < 400 and len(result.text) > 200:
                        time.sleep(self.delay_seconds + random.uniform(0.1, 0.5))
                        return result
                except Exception:
                    continue

        if last_result:
            return last_result
        return FetchResult(url, "", 0, "failed", blocked=True)

    def get(self, url: str, **kwargs) -> requests.Response:
        """Compatível com interface requests.Session.get()."""
        referer = kwargs.pop("headers", {}).get("Referer")
        result = self.fetch(url, referer=referer)
        response = requests.Response()
        response.status_code = result.status_code or 403
        response._content = result.text.encode("utf-8", errors="replace")
        response.url = url
        if result.blocked:
            response.status_code = 403
        return response

    @classmethod
    def is_playwright_installed(cls) -> bool:
        if cls._playwright_available is not None:
            return cls._playwright_available
        try:
            import playwright  # noqa: F401
            cls._playwright_available = True
        except ImportError:
            cls._playwright_available = False
        return cls._playwright_available


# Cliente global partilhado (thread-safe via thread-local sessions)
_default_client: AntibotClient | None = None
_client_lock = threading.Lock()


def get_antibot_client(aggressive: bool = True) -> AntibotClient:
    global _default_client
    with _client_lock:
        if _default_client is None:
            _default_client = AntibotClient(aggressive=aggressive)
        return _default_client


def fetch_html(url: str, aggressive: bool = True) -> str:
    client = get_antibot_client(aggressive=aggressive)
    result = client.fetch(url)
    if result.blocked:
        raise requests.HTTPError(f"Bloqueado por anti-bot: {url} (método: {result.method})")
    return result.text
