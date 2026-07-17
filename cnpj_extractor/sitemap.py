from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def discover_sitemap_urls(
    sitemap_index_url: str,
    session: requests.Session | None = None,
    timeout: int = 30,
) -> list[str]:
    """Descobre automaticamente todos os URLs de sitemap a partir de um índice."""
    http = session or requests
    response = http.get(sitemap_index_url, timeout=timeout)
    response.raise_for_status()

    # Tenta obter total de páginas do header (ex: x-sitemap-pages: 98)
    total_pages = response.headers.get("x-sitemap-pages")
    if total_pages and total_pages.isdigit():
        base = _sitemap_template_from_url(sitemap_index_url)
        if base:
            return [base.format(page=page) for page in range(1, int(total_pages) + 1)]

    return _parse_sitemap_document(response.text, sitemap_index_url, http, timeout)


def _sitemap_template_from_url(url: str) -> str | None:
    match = re.search(r"(.*/)(\d+)(/?)$", url)
    if not match:
        return None
    return f"{match.group(1)}{{page}}{match.group(3) or ''}"


def _parse_sitemap_document(
    content: str,
    source_url: str,
    http: requests.Session | type[requests],
    timeout: int,
) -> list[str]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return _filter_sitemap_locs(re.findall(r"<loc>(.*?)</loc>", content))

    tag = _strip_ns(root.tag)
    if tag == "sitemapindex":
        urls: list[str] = []
        for loc in root.iter():
            if _strip_ns(loc.tag) == "loc" and loc.text:
                loc_text = loc.text.strip()
                if _is_company_sitemap(loc_text):
                    urls.append(loc_text)
        if not urls:
            urls = _filter_sitemap_locs(re.findall(r"<loc>(.*?)</loc>", content))
        return urls

    if tag == "urlset":
        return [source_url]

    return []


def _filter_sitemap_locs(locs: list[str]) -> list[str]:
    return [loc.strip() for loc in locs if _is_company_sitemap(loc.strip())]


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_urlset(content: str) -> list[str]:
    """Extrai URLs de empresas de um ficheiro urlset XML."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return re.findall(r"<loc>(.*?)</loc>", content)

    urls: list[str] = []
    for loc in root.iter():
        if _strip_ns(loc.tag) == "loc" and loc.text:
            urls.append(loc.text.strip())
    if urls:
        return urls

    for url_node in root.findall("sm:url", SITEMAP_NS):
        loc = url_node.find("sm:loc", SITEMAP_NS)
        if loc is not None and loc.text:
            urls.append(loc.text.strip())
    if urls:
        return urls

    return re.findall(r"<loc>(.*?)</loc>", content)


def fetch_all_company_urls(
    sitemap_index_url: str,
    session: requests.Session | None = None,
    progress_callback=None,
) -> list[str]:
    """Descobre sitemaps e recolhe todos os URLs de empresas automaticamente."""
    http = session or requests
    sitemap_urls = discover_sitemap_urls(sitemap_index_url, session=http)
    if not sitemap_urls:
        sitemap_urls = [sitemap_index_url]

    company_urls: list[str] = []
    total = len(sitemap_urls)
    for index, sitemap_url in enumerate(sitemap_urls):
        response = http.get(sitemap_url, timeout=60)
        response.raise_for_status()
        batch = parse_urlset(response.text)
        company_urls.extend(batch)
        if progress_callback:
            progress_callback(
                (index + 1) / total,
                f"Sitemap {index + 1}/{total} — {len(company_urls):,} URLs encontrados",
            )

    return _dedupe_preserve_order(company_urls)


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def is_sitemap_index_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.path.endswith(".xml") or "/api/sitemap/" in parsed.path


def _is_company_sitemap(url: str) -> bool:
    """Filtra sitemaps de empresas (ignora cidades, setores, etc.)."""
    lower = url.lower()
    if "/empresas" in lower or "/empresa" in lower:
        return True
    if re.search(r"/sitemap/empresas/\d+", lower):
        return True
    if re.search(r"sitemap_emp_es_\d+\.xml", lower):
        return True
    if re.search(r"sitemap_sucur_es_\d+\.xml", lower):
        return True
    if lower.endswith("sitemap.xml") and "empresa" in lower:
        return True
    # Páginas numeradas diretas: /api/sitemap/empresas/1
    if re.search(r"/api/sitemap/[^/]+/\d+", lower) and "cidade" not in lower:
        return "empresa" in lower
    return False
