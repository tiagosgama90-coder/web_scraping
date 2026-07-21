from __future__ import annotations

import re
import threading
from urllib.parse import urlparse

_lock = threading.Lock()
_active_proxy: str | None = None

_SUPPORTED_SCHEMES = ("http://", "https://", "socks4://", "socks5://")


def normalize_proxy_url(text: str) -> str | None:
    """Normaliza URL de proxy HTTP/HTTPS/SOCKS."""
    value = (text or "").strip()
    if not value:
        return None
    if not value.lower().startswith(_SUPPORTED_SCHEMES):
        value = f"http://{value}"
    parsed = urlparse(value)
    if not parsed.hostname:
        return None
    return value


def is_valid_proxy_url(text: str) -> bool:
    url = normalize_proxy_url(text)
    if not url:
        return False
    parsed = urlparse(url)
    return bool(parsed.hostname and parsed.scheme)


def set_active_proxy(url: str | None) -> None:
    """Define o proxy usado por todas as extrações na thread atual."""
    global _active_proxy
    with _lock:
        _active_proxy = normalize_proxy_url(url or "")


def get_active_proxy() -> str | None:
    with _lock:
        return _active_proxy


def clear_active_proxy() -> None:
    set_active_proxy(None)


def requests_proxies() -> dict[str, str] | None:
    url = get_active_proxy()
    if not url:
        return None
    return {"http": url, "https": url}


def playwright_proxy() -> dict[str, str] | None:
    url = get_active_proxy()
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    port = parsed.port
    if port is None:
        port = 1080 if parsed.scheme.startswith("socks") else 8080
    server = f"{parsed.scheme}://{parsed.hostname}:{port}"
    cfg: dict[str, str] = {"server": server}
    if parsed.username:
        cfg["username"] = parsed.username
    if parsed.password:
        cfg["password"] = parsed.password
    return cfg


def mask_proxy_for_display(url: str | None) -> str:
    """Oculta password no ecrã/log."""
    if not url:
        return ""
    return re.sub(r":([^:@/]+)@", ":***@", url)
