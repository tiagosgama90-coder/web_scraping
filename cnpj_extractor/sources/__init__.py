from __future__ import annotations

from cnpj_extractor.country_catalogs import (
    CATALOG_COUNTRY_CODES,
    COUNTRY_CATALOG_REGISTRY,
    COUNTRY_MENU_ORDER,
    SPAIN_DIRECTORY_CATALOG,
    build_catalog_country_sources,
    build_spain_sources,
    catalog_source_key_for_country,
    find_catalog_entry,
    get_country_catalog,
)
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

SOURCES_ES: dict[str, BaseSource] = build_spain_sources()

_CATALOG_SOURCES: dict[str, dict[str, BaseSource]] = {
    code: (SOURCES_ES if code == "ES" else build_catalog_country_sources(code))
    for code in COUNTRY_CATALOG_REGISTRY
}

SOURCES_FR = _CATALOG_SOURCES["FR"]
SOURCES_DE = _CATALOG_SOURCES["DE"]
SOURCES_IT = _CATALOG_SOURCES["IT"]
SOURCES_GB = _CATALOG_SOURCES["GB"]
SOURCES_MX = _CATALOG_SOURCES["MX"]
SOURCES_AR = _CATALOG_SOURCES["AR"]
SOURCES_CO = _CATALOG_SOURCES["CO"]
SOURCES_CL = _CATALOG_SOURCES["CL"]
SOURCES_PE = _CATALOG_SOURCES["PE"]
SOURCES_US = _CATALOG_SOURCES["US"]
SOURCES_CA = _CATALOG_SOURCES["CA"]
SOURCES_NL = _CATALOG_SOURCES["NL"]
SOURCES_BE = _CATALOG_SOURCES["BE"]
SOURCES_PL = _CATALOG_SOURCES["PL"]
SOURCES_RO = _CATALOG_SOURCES["RO"]

SOURCES_OUTRO: dict[str, BaseSource] = {
    "sitemap_generico": GenericSitemapSource(),
    "website_scraper": WebScraperSource(),
}

SOURCES: dict[str, BaseSource] = {
    **SOURCES_BR,
    **SOURCES_PT,
    **SOURCES_ES,
    **SOURCES_FR,
    **SOURCES_DE,
    **SOURCES_IT,
    **SOURCES_GB,
    **SOURCES_MX,
    **SOURCES_AR,
    **SOURCES_CO,
    **SOURCES_CL,
    **SOURCES_PE,
    **SOURCES_US,
    **SOURCES_CA,
    **SOURCES_NL,
    **SOURCES_BE,
    **SOURCES_PL,
    **SOURCES_RO,
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

for _code, _meta in COUNTRY_CATALOG_REGISTRY.items():
    COUNTRIES[_code] = {
        "name": _meta["name"],
        "flag": _meta["flag"],
        "sources": _CATALOG_SOURCES[_code],
        "tax_id_label": _meta["tax_id_label"],
        "has_catalog": True,
        "catalog_hint": _meta.get("catalog_hint", ""),
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
