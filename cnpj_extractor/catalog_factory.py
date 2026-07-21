from __future__ import annotations

from typing import Iterator

from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.sources.website_scraper import WebScraperSource

CatalogEntry = dict[str, str]


class ConfiguredSitemapSource(GenericSitemapSource):
    """Sitemap genérico com URL pré-configurada."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        sitemap_url: str,
        country: str,
    ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.country = country
        self._default_sitemap_url = sitemap_url

    def extract(
        self,
        *,
        sitemap_url: str | None = None,
        auto_discover: bool = True,
        include_all_sitemaps: bool = True,
        aggressive_antibot: bool = True,
        only_with_email: bool = True,
        max_records: int | None = 500,
        sector_filter: str | None = None,
        progress_callback: ProgressCallback = None,
    ) -> Iterator:
        yield from super().extract(
            sitemap_url=sitemap_url or self._default_sitemap_url,
            auto_discover=auto_discover,
            include_all_sitemaps=include_all_sitemaps,
            aggressive_antibot=aggressive_antibot,
            only_with_email=only_with_email,
            max_records=max_records,
            sector_filter=sector_filter,
            progress_callback=progress_callback,
        )


class ConfiguredPageSource(WebScraperSource):
    """Scraper de página com URL inicial pré-configurada."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        start_url: str,
        country: str,
    ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.country = country
        self._start_url = start_url

    def extract(
        self,
        *,
        start_url: str | None = None,
        crawl_same_site: bool = True,
        max_crawl_pages: int = 50,
        only_with_email: bool = True,
        max_records: int | None = 500,
        progress_callback: ProgressCallback = None,
        **_,
    ) -> Iterator:
        yield from super().extract(
            start_url=start_url or self._start_url,
            crawl_same_site=crawl_same_site,
            max_crawl_pages=max_crawl_pages,
            only_with_email=only_with_email,
            max_records=max_records,
            progress_callback=progress_callback,
            source_name=self.name,
        )


def catalog_source_key(
    country_code: str,
    entry_id: str,
    *,
    primary_key_map: dict[str, str] | None = None,
) -> str:
    if primary_key_map and entry_id in primary_key_map:
        return primary_key_map[entry_id]
    return f"{country_code.lower()}_{entry_id}"


def build_catalog_sources(
    country_code: str,
    catalog: list[CatalogEntry],
    *,
    primary_sources: dict[str, BaseSource] | None = None,
    skip_ids: set[str] | None = None,
    primary_key_map: dict[str, str] | None = None,
    include_generics: bool = True,
) -> dict[str, BaseSource]:
    sources: dict[str, BaseSource] = dict(primary_sources or {})
    skipped = skip_ids or set()
    prefix = country_code.upper()

    for entry in catalog:
        entry_id = entry["id"]
        if entry_id in skipped:
            continue
        key = catalog_source_key(country_code, entry_id, primary_key_map=primary_key_map)
        label = f"{prefix} — {entry['name']}"
        if entry["kind"] == "sitemap":
            sources[key] = ConfiguredSitemapSource(
                name=label,
                description=entry["description"],
                sitemap_url=entry["url"],
                country=country_code,
            )
        else:
            sources[key] = ConfiguredPageSource(
                name=label,
                description=entry["description"],
                start_url=entry["url"],
                country=country_code,
            )

    if include_generics:
        sources["sitemap_generico"] = GenericSitemapSource()
        sources["website_scraper"] = WebScraperSource()
    return sources
