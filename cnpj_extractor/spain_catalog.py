"""Compatibilidade — use cnpj_extractor.country_catalogs."""

from cnpj_extractor.catalog_factory import ConfiguredPageSource, ConfiguredSitemapSource
from cnpj_extractor.country_catalogs import (
    SPAIN_DIRECTORY_CATALOG,
    build_spain_sources,
    catalog_source_key_for_country as catalog_source_key,
)

__all__ = [
    "SPAIN_DIRECTORY_CATALOG",
    "ConfiguredSitemapSource",
    "ConfiguredPageSource",
    "catalog_source_key",
    "build_spain_sources",
]
