from __future__ import annotations

import asyncio
import random
import re
import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from cnpj_extractor.browser_stealth import CHROME_LAUNCH_ARGS, STEALTH_INIT_SCRIPT

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
    r"verify you are human",
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

CLOUDFLARE_WAIT_SECONDS = 20
BROWSER_POLL_INTERVAL = 1.5


@dataclass
class FetchResult:
    url: str
    text: str
    status_code: int
    method: str
    blocked: bool = False
    headers: dict | None = None


def _run_async(coro):
    """Executa corrotina async a partir de código sync (thread-safe)."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.run_until_complete(asyncio.sleep(0.25))
        return result
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()
        asyncio.set_event_loop(None)


class AntibotClient:
    """
    Cliente HTTP com várias camadas anti-bot:
    1. curl_cffi (imita TLS fingerprint do Chrome)
    2. cloudscraper (resolve desafios Cloudflare básicos)
    3. requests padrão (fallback)
    4. Playwright (browser real com stealth)
    5. nodriver (estilo Puppeteer — Chrome indetectável)
    """

    _playwright_available: bool | None = None
    _nodriver_available: bool | None = None

    def __init__(
        self,
        *,
        delay_seconds: float = 0.4,
        max_retries: int = 4,
        use_playwright_fallback: bool = True,
        aggressive: bool = True,
    ):
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.use_playwright_fallback = use_playwright_fallback
        self.aggressive = aggressive
        self._local = threading.local()
        self._browser_lock = threading.Lock()

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
        lower = (html or "").lower()[:12000]
        return any(re.search(pat, lower) for pat in BLOCK_PATTERNS)

    def _wait_for_real_content(self, get_html: Any, max_wait: float = CLOUDFLARE_WAIT_SECONDS) -> str:
        """Espera até o desafio Cloudflare desaparecer ou timeout."""
        deadline = time.time() + max_wait
        last_html = ""
        while time.time() < deadline:
            last_html = get_html() or ""
            if last_html and not self._is_blocked(200, last_html) and len(last_html) > 300:
                return last_html
            time.sleep(BROWSER_POLL_INTERVAL)
        return last_html

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
        last_result: FetchResult | None = None
        try:
            for impersonate in BROWSER_IMPERSONATIONS:
                try:
                    resp = session.get(
                        url,
                        headers=self._random_headers(referer),
                        timeout=45,
                        allow_redirects=True,
                        impersonate=impersonate,
                    )
                    text = resp.text
                    blocked = self._is_blocked(resp.status_code, text)
                    hdrs = dict(resp.headers) if hasattr(resp, "headers") else {}
                    last_result = FetchResult(
                        url, text, resp.status_code, f"curl_cffi/{impersonate}", blocked, hdrs
                    )
                    if not blocked and resp.status_code < 400 and len(text) > 200:
                        return last_result
                except Exception:
                    continue
            return last_result
        except Exception:
            return last_result

    def _fetch_cloudscraper(self, url: str, referer: str | None) -> FetchResult | None:
        session = self._get_cloudscraper_session()
        if not session:
            return None
        try:
            resp = session.get(url, headers=self._random_headers(referer), timeout=45)
            text = resp.text
            return FetchResult(
                url, text, resp.status_code, "cloudscraper", self._is_blocked(resp.status_code, text)
            )
        except Exception:
            return None

    def _fetch_requests(self, url: str, referer: str | None) -> FetchResult:
        session = self._get_requests_session()
        session.headers.update(self._random_headers(referer))
        resp = session.get(url, timeout=45, allow_redirects=True)
        text = resp.text
        return FetchResult(url, text, resp.status_code, "requests", self._is_blocked(resp.status_code, text))

    def _fetch_playwright(self, url: str) -> FetchResult | None:
        if not self.use_playwright_fallback:
            return None
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return None

        with self._browser_lock:
            try:
                with sync_playwright() as p:
                    launch_kwargs: dict[str, Any] = {
                        "headless": True,
                        "args": CHROME_LAUNCH_ARGS,
                    }
                    browser = None
                    for channel in ("chrome", None):
                        try:
                            if channel:
                                browser = p.chromium.launch(channel=channel, **launch_kwargs)
                            else:
                                browser = p.chromium.launch(**launch_kwargs)
                            break
                        except Exception:
                            continue
                    if not browser:
                        return None

                    user_agent = random.choice(USER_AGENTS)
                    context = browser.new_context(
                        user_agent=user_agent,
                        locale="pt-PT",
                        viewport={"width": 1366, "height": 768},
                        java_script_enabled=True,
                        bypass_csp=True,
                    )
                    context.add_init_script(STEALTH_INIT_SCRIPT)
                    page = context.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except Exception:
                        pass

                    text = self._wait_for_real_content(page.content)
                    browser.close()
                    blocked = self._is_blocked(200, text)
                    return FetchResult(url, text, 200, "playwright", blocked)
            except Exception:
                return None

    def _fetch_puppeteer(self, url: str) -> FetchResult | None:
        """nodriver — automação estilo Puppeteer com Chrome indetectável."""
        if not self.use_playwright_fallback:
            return None
        try:
            import nodriver as uc
        except ImportError:
            return None

        async def _run() -> str:
            browser = await uc.start(headless=True)
            try:
                page = await browser.get(url)
                deadline = time.time() + CLOUDFLARE_WAIT_SECONDS
                last_html = ""
                while time.time() < deadline:
                    await asyncio.sleep(BROWSER_POLL_INTERVAL)
                    last_html = await page.get_content()
                    if last_html and not self._is_blocked(200, last_html) and len(last_html) > 300:
                        return last_html
                return last_html or await page.get_content()
            finally:
                try:
                    stop = browser.stop()
                    if asyncio.iscoroutine(stop):
                        await stop
                except Exception:
                    pass

        with self._browser_lock:
            try:
                text = _run_async(_run())
                if not text:
                    return None
                blocked = self._is_blocked(200, text)
                return FetchResult(url, text, 200, "puppeteer/nodriver", blocked)
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

            http_methods: list = []
            if self.aggressive:
                http_methods.extend([self._fetch_curl_cffi, self._fetch_cloudscraper])
            http_methods.append(self._fetch_requests)

            all_http_blocked = True
            for method in http_methods:
                try:
                    result = method(url, referer)
                    if result is None:
                        continue

                    last_result = result
                    if not result.blocked and result.status_code < 400 and len(result.text) > 200:
                        time.sleep(self.delay_seconds + random.uniform(0.1, 0.5))
                        return result
                    if result and not result.blocked:
                        all_http_blocked = False
                except Exception:
                    continue

            if self.use_playwright_fallback and (all_http_blocked or attempt >= 1):
                for browser_method in (self._fetch_playwright, self._fetch_puppeteer):
                    try:
                        br_result = browser_method(url)
                        if br_result:
                            last_result = br_result
                            if not br_result.blocked and len(br_result.text) > 200:
                                time.sleep(self.delay_seconds + random.uniform(0.1, 0.5))
                                return br_result
                    except Exception:
                        continue

        if last_result:
            return last_result
        return FetchResult(url, "", 0, "failed", blocked=True)

    def get(self, url: str, **kwargs) -> requests.Response:
        """Compatível com interface requests.Session.get()."""
        headers = kwargs.pop("headers", {}) or {}
        referer = headers.get("Referer")
        result = self.fetch(url, referer=referer)
        response = requests.Response()
        response.status_code = result.status_code or (403 if result.blocked else 0)
        response._content = result.text.encode("utf-8", errors="replace")
        response.url = url
        if result.headers:
            response.headers.update(result.headers)
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

    @classmethod
    def is_puppeteer_installed(cls) -> bool:
        if cls._nodriver_available is not None:
            return cls._nodriver_available
        try:
            import nodriver  # noqa: F401

            cls._nodriver_available = True
        except ImportError:
            cls._nodriver_available = False
        return cls._nodriver_available


# Cliente global partilhado (thread-safe via thread-local sessions)
_default_client: AntibotClient | None = None
_client_lock = threading.Lock()


def get_antibot_client(aggressive: bool = True) -> AntibotClient:
    global _default_client
    with _client_lock:
        if _default_client is None:
            _default_client = AntibotClient(
                aggressive=aggressive,
                use_playwright_fallback=aggressive,
            )
        else:
            _default_client.aggressive = aggressive
            _default_client.use_playwright_fallback = aggressive
        return _default_client


def fetch_html(url: str, aggressive: bool = True) -> str:
    client = get_antibot_client(aggressive=aggressive)
    result = client.fetch(url)
    if result.blocked:
        raise requests.HTTPError(f"Bloqueado por anti-bot: {url} (método: {result.method})")
    return result.text
