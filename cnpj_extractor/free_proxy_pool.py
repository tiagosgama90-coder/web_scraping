"""Pool de proxies HTTP gratuitos — modo «Ocultar IP» automático (estilo Hide My IP)."""

from __future__ import annotations

import concurrent.futures
import random
import re
import threading
import time
from collections.abc import Callable

import requests

_lock = threading.Lock()
_candidates: list[str] = []
_index = 0
_last_fetch = 0.0
_active_pool_proxy: str | None = None

CACHE_TTL_SECONDS = 600
_PROXY_LINE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$")

PROXY_SOURCES = (
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
)

TEST_URLS = (
    "http://httpbin.org/ip",
    "http://icanhazip.com",
    "http://api.ipify.org",
)


def _normalize_candidate(host_port: str) -> str | None:
    value = host_port.strip()
    if not value or value.startswith("#"):
        return None
    if "://" in value:
        return value if value.startswith("http://") else None
    if _PROXY_LINE.match(value):
        return f"http://{value}"
    return None


def _parse_proxy_list(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        proxy = _normalize_candidate(line)
        if proxy and proxy not in seen:
            seen.add(proxy)
            found.append(proxy)
    return found


def _fetch_from_source(url: str, timeout: float = 12.0) -> list[str]:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and resp.text.strip():
            return _parse_proxy_list(resp.text)
    except Exception:
        pass
    return []


def _refresh_candidates(*, force: bool = False) -> list[str]:
    global _candidates, _last_fetch, _index
    now = time.time()
    with _lock:
        if not force and _candidates and (now - _last_fetch) < CACHE_TTL_SECONDS:
            return list(_candidates)

    merged: list[str] = []
    seen: set[str] = set()
    for source in PROXY_SOURCES:
        for proxy in _fetch_from_source(source):
            if proxy not in seen:
                seen.add(proxy)
                merged.append(proxy)

    random.shuffle(merged)
    with _lock:
        _candidates = merged
        _index = 0
        _last_fetch = now
    return list(merged)


def test_proxy(proxy_url: str, *, timeout: float = 7.0, proxies: dict[str, str] | None = None) -> bool:
    proxies = proxies or {"http": proxy_url, "https": proxy_url}
    for test_url in TEST_URLS:
        try:
            resp = requests.get(
                test_url,
                proxies=proxies,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200 and len(resp.text.strip()) >= 7:
                return True
        except Exception:
            continue
    return False


def _test_batch(candidates: list[str]) -> str | None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(test_proxy, url): url for url in candidates}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                if future.result():
                    return url
            except Exception:
                continue
    return None


def get_cached_working_proxy(*, quick_check: bool = True) -> str | None:
    """Devolve proxy já preparado em cache, se ainda funcionar."""
    with _lock:
        proxy = _active_pool_proxy
    if not proxy:
        return None
    if quick_check and test_proxy(proxy, timeout=4.0):
        return proxy
    return None


def prewarm_proxy_pool(
    *,
    max_tries: int = 20,
    progress_callback: Callable[[str], None] | None = None,
) -> str | None:
    """Prepara proxies em segundo plano (ao abrir o software)."""
    cached = get_cached_working_proxy()
    if cached:
        if progress_callback:
            progress_callback(f"✅ IP oculto pronto: {cached}")
        return cached
    if progress_callback:
        progress_callback("🌐 A preparar Hide My IP integrado...")
    return acquire_working_proxy(max_tries=max_tries, progress_callback=progress_callback)


def acquire_working_proxy(
    *,
    max_tries: int = 30,
    progress_callback: Callable[[str], None] | None = None,
) -> str | None:
    """Procura e devolve o primeiro proxy gratuito funcional."""
    global _active_pool_proxy, _index

    def report(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    report("🌐 Hide My IP integrado — a procurar servidor anónimo...")
    candidates = _refresh_candidates(force=True)
    if not candidates:
        report("⚠ Não foi possível obter lista de proxies. A tentar de novo...")
        candidates = _refresh_candidates(force=True)

    if not candidates:
        return None

    report(f"🔍 A testar proxies ({len(candidates)} candidatos)...")
    tried = 0
    batch_size = 10

    while tried < max_tries:
        with _lock:
            start = _index
            _index = min(_index + batch_size, len(_candidates))
            batch = _candidates[start:_index]

        if not batch:
            candidates = _refresh_candidates(force=True)
            if not candidates:
                break
            with _lock:
                _index = 0
            continue

        working = _test_batch(batch[: max_tries - tried])
        tried += len(batch)

        if working:
            with _lock:
                _active_pool_proxy = working
            report(f"✅ Proxy ativo: {working}")
            return working

        report(f"🔄 A testar mais proxies ({tried}/{max_tries})...")

    return None


def rotate_working_proxy(
    *,
    max_tries: int = 15,
    progress_callback: Callable[[str], None] | None = None,
) -> str | None:
    """Tenta outro proxy quando o atual falha."""
    global _active_pool_proxy

    with _lock:
        previous = _active_pool_proxy
        if previous and previous in _candidates:
            _candidates.remove(previous)

    if progress_callback:
        progress_callback("🔄 Proxy falhou — a procurar outro...")

    return acquire_working_proxy(max_tries=max_tries, progress_callback=progress_callback)


def get_active_pool_proxy() -> str | None:
    with _lock:
        return _active_pool_proxy


def clear_free_proxy_cache() -> None:
    global _candidates, _index, _last_fetch, _active_pool_proxy
    with _lock:
        _candidates = []
        _index = 0
        _last_fetch = 0.0
        _active_pool_proxy = None
