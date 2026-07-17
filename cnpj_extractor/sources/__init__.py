from __future__ import annotations

from cnpj_extractor.sources.base import BaseSource
from cnpj_extractor.sources.dadosbrasil_api import DadosBrasilApiSource
from cnpj_extractor.sources.dadosbrasil_scraper import DadosBrasilScraperSource
from cnpj_extractor.sources.empresite_spain import EmpresiteSpainSource
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

SOURCES_ES: dict[str, BaseSource] = {
    "empresite_spain": EmpresiteSpainSource(),
    "sitemap_generico": GenericSitemapSource(),
}

SOURCES_OUTRO: dict[str, BaseSource] = {
    "sitemap_generico": GenericSitemapSource(),
    "website_scraper": WebScraperSource(),
}

SOURCES: dict[str, BaseSource] = {**SOURCES_BR, **SOURCES_PT, **SOURCES_ES, **SOURCES_OUTRO}

COUNTRIES = {
    "BR": {
        "name": "Brasil",
        "flag": "🇧🇷",
        "sources": SOURCES_BR,
        "tax_id_label": "CNPJ",
    },
    "PT": {
        "name": "Portugal",
        "flag": "🇵🇹",
        "sources": SOURCES_PT,
        "tax_id_label": "NIPC",
    },
    "ES": {
        "name": "Espanha",
        "flag": "🇪🇸",
        "sources": SOURCES_ES,
        "tax_id_label": "CIF/NIF",
    },
    "OUTRO": {
        "name": "Outro / Qualquer site",
        "flag": "🌍",
        "sources": SOURCES_OUTRO,
        "tax_id_label": "ID",
    },
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
    "COMMERCIAL_SOURCES_INFO",
    "ReceitaFederalSource",
    "DadosBrasilApiSource",
    "DadosBrasilScraperSource",
    "FizPortugalSource",
    "EmpresiteSpainSource",
    "GenericSitemapSource",
    "WebScraperSource",
]
