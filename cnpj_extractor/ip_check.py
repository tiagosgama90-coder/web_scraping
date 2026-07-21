"""Verificação de IP público — comparar IP real vs IP através do proxy ativo."""

from __future__ import annotations

import json
from dataclasses import dataclass

import requests

from cnpj_extractor.proxy_config import get_active_proxy, requests_proxies


@dataclass
class IpInfo:
    ip: str
    country: str
    country_code: str
    city: str
    via_proxy: bool

    def summary(self) -> str:
        place = self.country or "desconhecido"
        if self.city:
            place = f"{self.city}, {place}"
        proxy_tag = " (proxy ativo)" if self.via_proxy else " (ligação direta)"
        return f"{self.ip} — {place}{proxy_tag}"


def _fetch_ipify(*, proxies: dict[str, str] | None, timeout: float = 10.0) -> str | None:
    try:
        resp = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            ip = (data.get("ip") or "").strip()
            return ip or None
    except Exception:
        pass
    return None


def _fetch_geo(ip: str, *, timeout: float = 8.0) -> tuple[str, str, str]:
    """Devolve (país, código país, cidade) via ip-api.com (gratuito)."""
    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city",
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return (
                    data.get("country") or "",
                    data.get("countryCode") or "",
                    data.get("city") or "",
                )
    except Exception:
        pass
    return ("", "", "")


def lookup_ip(
    *,
    proxy_url: str | None = None,
    use_active_proxy: bool = False,
    timeout: float = 10.0,
) -> IpInfo | None:
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    elif use_active_proxy and get_active_proxy():
        proxies = requests_proxies()
    else:
        proxies = None
    ip = _fetch_ipify(proxies=proxies, timeout=timeout)
    if not ip:
        return None
    country, code, city = _fetch_geo(ip, timeout=timeout)
    return IpInfo(
        ip=ip,
        country=country,
        country_code=code,
        city=city,
        via_proxy=bool(proxies),
    )


def compare_ips() -> dict[str, IpInfo | None]:
    """IP real (sem proxy) vs IP visto com proxy ativo."""
    real = lookup_ip(use_active_proxy=False)
    proxied = lookup_ip(use_active_proxy=True) if get_active_proxy() else None
    return {"real": real, "proxied": proxied}
