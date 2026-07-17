from __future__ import annotations

from cnpj_extractor.sources.base import BaseSource
from cnpj_extractor.sources.dadosbrasil_api import DadosBrasilApiSource
from cnpj_extractor.sources.dadosbrasil_scraper import DadosBrasilScraperSource
from cnpj_extractor.sources.receita_federal import ReceitaFederalSource

SOURCES: dict[str, BaseSource] = {
    "receita_federal": ReceitaFederalSource(),
    "dadosbrasil_api": DadosBrasilApiSource(),
    "dadosbrasil_scraper": DadosBrasilScraperSource(),
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
    "COMMERCIAL_SOURCES_INFO",
    "ReceitaFederalSource",
    "DadosBrasilApiSource",
    "DadosBrasilScraperSource",
]
