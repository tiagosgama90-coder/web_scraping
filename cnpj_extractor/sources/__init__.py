from __future__ import annotations

from cnpj_extractor.sources.base import BaseSource
from cnpj_extractor.sources.dadosbrasil_api import DadosBrasilApiSource
from cnpj_extractor.sources.dadosbrasil_scraper import DadosBrasilScraperSource
from cnpj_extractor.sources.fiz_portugal import FizPortugalSource
from cnpj_extractor.sources.receita_federal import ReceitaFederalSource
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.sources.website_scraper import WebScraperSource

SOURCES_BR: dict[str, BaseSource] = {
    "receita_federal": ReceitaFederalSource(),
    "dadosbrasil_api": DadosBrasilApiSource(),
    "dadosbrasil_scraper": DadosBrasilScraperSource(),
}

SOURCES_PT: dict[str, BaseSource] = {
    "fiz_portugal": FizPortugalSource(),
    "sitemap_generico": GenericSitemapSource(),
}

SOURCES_OUTRO: dict[str, BaseSource] = {
    "sitemap_generico": GenericSitemapSource(),
    "website_scraper": WebScraperSource(),
}

COMMERCIAL_SOURCES_INFO = {
    "oportunidados": {
        "name": "Oportunidados",
        "url": "https://oportunidados.com.br/",
        "note": (
            "Plataforma comercial com proteção anti-bot. Os mesmos e-mails estão nos "
            "dados abertos da Receita Federal — use a fonte oficial acima."
        ),
    },
    "econodata": {
        "name": "Econodata",
        "url": "https://www.econodata.com.br/",
        "note": (
            "Serviço pago de prospecção B2B. Recomendamos extrair via Receita Federal "
            "ou DadosBrasil API para uso gratuito e legal."
        ),
    },
    "basecnpj": {
        "name": "BaseCNPJ",
        "url": "https://www.basecnpj.com.br/",
        "note": (
            "Consulta comercial protegida por Cloudflare. Dados equivalentes disponíveis "
            "gratuitamente nos dados abertos oficiais."
        ),
    },
}

# Catálogos — carregados via _init_catalogs() / __getattr__
_catalogs_initialized = False

_LAZY_EXPORTS = frozenset({
    "SOURCES_ES",
    "SOURCES_FR",
    "SOURCES_DE",
    "SOURCES_IT",
    "SOURCES_GB",
    "SOURCES_MX",
    "SOURCES_AR",
    "SOURCES_CO",
    "SOURCES_CL",
    "SOURCES_PE",
    "SOURCES_US",
    "SOURCES_CA",
    "SOURCES_NL",
    "SOURCES_BE",
    "SOURCES_PL",
    "SOURCES_RO",
    "SOURCES",
    "COUNTRIES",
    "COUNTRY_MENU_ORDER",
    "CATALOG_COUNTRY_CODES",
    "COUNTRY_CATALOG_REGISTRY",
    "SPAIN_DIRECTORY_CATALOG",
    "build_catalog_country_sources",
    "build_spain_sources",
    "catalog_source_key_for_country",
    "find_catalog_entry",
    "get_country_catalog",
})


def _init_catalogs() -> None:
    global _catalogs_initialized
    global SOURCES_ES, _CATALOG_SOURCES, SOURCES, COUNTRIES
    global COUNTRY_MENU_ORDER, CATALOG_COUNTRY_CODES, COUNTRY_CATALOG_REGISTRY
    global SPAIN_DIRECTORY_CATALOG

    if _catalogs_initialized:
        return

    from cnpj_extractor.country_catalogs import (
        CATALOG_COUNTRY_CODES as _CODES,
        COUNTRY_CATALOG_REGISTRY as _REGISTRY,
        COUNTRY_MENU_ORDER as _MENU,
        SPAIN_DIRECTORY_CATALOG as _SPAIN_CAT,
        build_catalog_country_sources,
        build_spain_sources,
        catalog_source_key_for_country,
        find_catalog_entry,
        get_country_catalog,
    )

    CATALOG_COUNTRY_CODES = _CODES
    COUNTRY_CATALOG_REGISTRY = _REGISTRY
    COUNTRY_MENU_ORDER = _MENU
    SPAIN_DIRECTORY_CATALOG = _SPAIN_CAT

    SOURCES_ES = build_spain_sources()
    _CATALOG_SOURCES = {
        code: (SOURCES_ES if code == "ES" else build_catalog_country_sources(code))
        for code in COUNTRY_CATALOG_REGISTRY
    }

    SOURCES = {
        **SOURCES_BR,
        **SOURCES_PT,
        **SOURCES_ES,
        **_CATALOG_SOURCES.get("FR", {}),
        **_CATALOG_SOURCES.get("DE", {}),
        **_CATALOG_SOURCES.get("IT", {}),
        **_CATALOG_SOURCES.get("GB", {}),
        **_CATALOG_SOURCES.get("MX", {}),
        **_CATALOG_SOURCES.get("AR", {}),
        **_CATALOG_SOURCES.get("CO", {}),
        **_CATALOG_SOURCES.get("CL", {}),
        **_CATALOG_SOURCES.get("PE", {}),
        **_CATALOG_SOURCES.get("US", {}),
        **_CATALOG_SOURCES.get("CA", {}),
        **_CATALOG_SOURCES.get("NL", {}),
        **_CATALOG_SOURCES.get("BE", {}),
        **_CATALOG_SOURCES.get("PL", {}),
        **_CATALOG_SOURCES.get("RO", {}),
        **SOURCES_OUTRO,
    }

    COUNTRIES = {
        "BR": {
            "name": "Brasil",
            "flag": "🇧🇷",
            "sources": SOURCES_BR,
            "tax_id_label": "CNPJ",
            "has_catalog": False,
        },
        "PT": {
            "name": "Portugal",
            "flag": "🇵🇹",
            "sources": SOURCES_PT,
            "tax_id_label": "NIPC",
            "has_catalog": False,
        },
        "OUTRO": {
            "name": "Outro / Qualquer site",
            "flag": "🌍",
            "sources": SOURCES_OUTRO,
            "tax_id_label": "ID",
            "has_catalog": False,
        },
    }

    for code, meta in COUNTRY_CATALOG_REGISTRY.items():
        COUNTRIES[code] = {
            "name": meta["name"],
            "flag": meta["flag"],
            "sources": _CATALOG_SOURCES[code],
            "tax_id_label": meta["tax_id_label"],
            "has_catalog": True,
            "catalog_hint": meta.get("catalog_hint", ""),
        }

    # Re-export helpers on module for __getattr__
    globals()["build_catalog_country_sources"] = build_catalog_country_sources
    globals()["build_spain_sources"] = build_spain_sources
    globals()["catalog_source_key_for_country"] = catalog_source_key_for_country
    globals()["find_catalog_entry"] = find_catalog_entry
    globals()["get_country_catalog"] = get_country_catalog

    for code in ("FR", "DE", "IT", "GB", "MX", "AR", "CO", "CL", "PE", "US", "CA", "NL", "BE", "PL", "RO"):
        globals()[f"SOURCES_{code}"] = _CATALOG_SOURCES[code]

    _catalogs_initialized = True


def __getattr__(name: str):
    if name in _LAZY_EXPORTS:
        _init_catalogs()
        if name in globals():
            return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "SOURCES",
    "SOURCES_BR",
    "SOURCES_PT",
    "SOURCES_ES",
    "COUNTRIES",
    "COUNTRY_MENU_ORDER",
    "CATALOG_COUNTRY_CODES",
    "COUNTRY_CATALOG_REGISTRY",
    "SPAIN_DIRECTORY_CATALOG",
    "COMMERCIAL_SOURCES_INFO",
    "build_catalog_country_sources",
    "catalog_source_key_for_country",
    "find_catalog_entry",
    "get_country_catalog",
    "ReceitaFederalSource",
    "DadosBrasilApiSource",
    "DadosBrasilScraperSource",
    "FizPortugalSource",
    "GenericSitemapSource",
    "WebScraperSource",
]
