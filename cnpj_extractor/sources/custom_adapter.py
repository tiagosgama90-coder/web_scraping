from __future__ import annotations

from typing import Iterator

from cnpj_extractor.custom_sources import CustomSource, parse_url_list
from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.sources.website_scraper import WebScraperSource


class CustomSourceAdapter(BaseSource):
    """Adapta uma fonte personalizada guardada pelo utilizador."""

    def __init__(self, config: CustomSource):
        self.config = config
        self.name = config.name
        self.description = config.notes or f"Fonte personalizada: {config.url}"
        self.country = config.country

    def extract(
        self,
        *,
        max_records: int | None = 500,
        only_with_email: bool = True,
        auto_discover: bool | None = None,
        max_sitemap_pages: int | None = None,
        aggressive_antibot: bool = True,
        progress_callback: ProgressCallback = None,
    ) -> Iterator[CompanyEmail]:
        auto = auto_discover if auto_discover is not None else self.config.auto_discover
        source_type = self.config.source_type

        if source_type == "sitemap":
            scraper = GenericSitemapSource(aggressive_antibot=aggressive_antibot)
            kwargs: dict = {
                "sitemap_url": self.config.url,
                "auto_discover": auto,
                "include_all_sitemaps": True,
                "only_with_email": only_with_email,
                "max_records": max_records,
                "progress_callback": progress_callback,
            }
            if max_sitemap_pages is not None and not auto:
                # Processar só N páginas do sitemap
                from cnpj_extractor.sitemap import discover_sitemap_urls, parse_urlset

                sitemaps = discover_sitemap_urls(self.config.url, session=scraper.session)
                if not sitemaps:
                    sitemaps = [self.config.url]
                sitemaps = sitemaps[:max_sitemap_pages]
                urls: list[str] = []
                for sm in sitemaps:
                    result = scraper._client.fetch(sm)
                    if result.text:
                        urls.extend(parse_urlset(result.text))
                web = WebScraperSource(aggressive_antibot=aggressive_antibot)
                yield from web.extract(
                    urls=urls,
                    only_with_email=only_with_email,
                    max_records=max_records,
                    progress_callback=progress_callback,
                    source_name=self.config.name,
                )
                return

            for record in scraper.extract(**kwargs):
                record.fonte = self.config.name
                record.pais = self.config.country if self.config.country != "OUTRO" else record.pais
                yield record

        elif source_type == "urls":
            urls = parse_url_list(self.config.url_list or self.config.url)
            web = WebScraperSource(aggressive_antibot=aggressive_antibot)
            yield from web.extract(
                urls=urls,
                only_with_email=only_with_email,
                max_records=max_records,
                progress_callback=progress_callback,
                source_name=self.config.name,
            )

        elif source_type == "pagina":
            web = WebScraperSource(aggressive_antibot=aggressive_antibot)
            yield from web.extract(
                start_url=self.config.url,
                crawl_same_site=auto,
                max_crawl_pages=50 if auto else 1,
                only_with_email=only_with_email,
                max_records=max_records,
                progress_callback=progress_callback,
                source_name=self.config.name,
            )

        else:
            raise ValueError(f"Tipo de fonte desconhecido: {source_type}")
