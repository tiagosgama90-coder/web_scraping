from __future__ import annotations

from cnpj_extractor.sources.base import BaseSource
from cnpj_extractor.sources.dadosbrasil_api import DadosBrasilApiSource
from cnpj_extractor.sources.dadosbrasil_scraper import DadosBrasilScraperSource
from cnpj_extractor.sources.fiz_portugal import FizPortugalSource
from cnpj_extractor.sources.receita_federal import ReceitaFederalSource
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource

SOURCES_BR: dict[str, BaseSource] = {
    "receita_federal": ReceitaFederalSource(),
    "dadosbrasil_api": DadosBrasilApiSource(),
    "dadosbrasil_scraper": DadosBrasilScraperSource(),
}

SOURCES_PT: dict[str, BaseSource] = {
    "fiz_portugal": FizPortugalSource(),
    "sitemap_generico": GenericSitemapSource(),
}

SOURCES: dict[str, BaseSource] = {**SOURCES_BR, **SOURCES_PT}

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
    "COUNTRIES",
    "COMMERCIAL_SOURCES_INFO",
    "ReceitaFederalSource",
    "DadosBrasilApiSource",
    "DadosBrasilScraperSource",
    "FizPortugalSource",
    "GenericSitemapSource",
]
