from __future__ import annotations

from typing import Iterator

from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.sources.website_scraper import WebScraperSource

# Catálogo de diretórios e portais empresariais em Espanha.
# Empresite é a fonte principal (sitemap público, ~4M empresas).
SPAIN_DIRECTORY_CATALOG: list[dict[str, str]] = [
    {
        "id": "empresite",
        "name": "Empresite (~4M empresas)",
        "url": "https://empresite.eleconomista.es/sitemap_EMP_ES_index.xml",
        "kind": "sitemap",
        "emails": "15–20%",
        "description": "Fonte principal — sitemap automático, anti-bot recomendado.",
    },
    {
        "id": "empresite_provincias",
        "name": "Empresite — por província",
        "url": "https://empresite.eleconomista.es/empresas-provincia",
        "kind": "pagina",
        "emails": "10–15%",
        "description": "Lista por província (Madrid, Barcelona, Valencia…).",
    },
    {
        "id": "empresite_informes",
        "name": "Empresite — informes",
        "url": "https://empresite.eleconomista.es/informes-empresas",
        "kind": "pagina",
        "emails": "5–10%",
        "description": "Secção de informes; emails limitados nas fichas gratuitas.",
    },
    {
        "id": "empresite_actividades",
        "name": "Empresite — por actividade",
        "url": "https://empresite.eleconomista.es/actividad",
        "kind": "pagina",
        "emails": "10–15%",
        "description": "Navegação por sector CNAE/CAE.",
    },
    {
        "id": "einforma",
        "name": "eInforma",
        "url": "https://www.einforma.com/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Portal Informa D&B — maioria dos emails atrás de paywall.",
    },
    {
        "id": "axesor",
        "name": "Axesor",
        "url": "https://www.axesor.es/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Diretório comercial espanhol; dados financeiros públicos.",
    },
    {
        "id": "iberinform",
        "name": "Iberinform",
        "url": "https://www.iberinform.es/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Informação comercial e ratings de empresas.",
    },
    {
        "id": "infocif",
        "name": "Infocif",
        "url": "https://www.infocif.es/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Consulta CIF/NIF e dados mercantis.",
    },
    {
        "id": "infonif",
        "name": "Infonif",
        "url": "https://www.infonif.economia3.com/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Base de NIFs e empresas espanholas.",
    },
    {
        "id": "kompass",
        "name": "Kompass España",
        "url": "https://es.kompass.com/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Diretório internacional B2B.",
    },
    {
        "id": "paginas_amarillas",
        "name": "Páginas Amarillas",
        "url": "https://www.paginasamarillas.es/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Guia local — emails nas fichas de negócio.",
    },
    {
        "id": "qdq",
        "name": "QDQ (guia local)",
        "url": "https://www.qdq.com/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Diretório de negócios locais em Espanha.",
    },
    {
        "id": "cylex",
        "name": "Cylex España",
        "url": "https://www.cylex.es/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Listagens de empresas por cidade.",
    },
    {
        "id": "tuugo",
        "name": "Tuugo España",
        "url": "https://www.tuugo.es/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Diretório de empresas e serviços.",
    },
    {
        "id": "hotfrog",
        "name": "Hotfrog España",
        "url": "https://www.hotfrog.es/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Listagens gratuitas de negócios.",
    },
    {
        "id": "infoempresa",
        "name": "Infoempresa.com",
        "url": "https://www.infoempresa.com/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Consulta de empresas por nome ou CIF.",
    },
    {
        "id": "guias_empresas",
        "name": "Guías de Empresas",
        "url": "https://www.guiasdeempresas.com/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Diretório sectorial de empresas.",
    },
    {
        "id": "directorio_empresas",
        "name": "Directorio-Empresas.es",
        "url": "https://www.directorio-empresas.es/",
        "kind": "pagina",
        "emails": "Médio",
        "description": "Listagem por sector e região.",
    },
    {
        "id": "expansion",
        "name": "Expansión — directorio",
        "url": "https://www.expansion.com/empresas/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Ranking e perfis de grandes empresas.",
    },
    {
        "id": "openmercantil",
        "name": "OpenMercantil (BORME)",
        "url": "https://openmercantil.es/",
        "kind": "pagina",
        "emails": "Raro",
        "description": "Dados oficiais BORME — CIF e cargos; emails raros.",
    },
    {
        "id": "borme_boe",
        "name": "BOE — BORME",
        "url": "https://www.boe.es/diario_borme/",
        "kind": "pagina",
        "emails": "Raro",
        "description": "Boletim Oficial — actos mercantis (sem emails).",
    },
    {
        "id": "registro_mercantil",
        "name": "Registro Mercantil Central",
        "url": "https://www.rmc.es/",
        "kind": "pagina",
        "emails": "Raro",
        "description": "Consulta de sociedades mercantis oficiais.",
    },
    {
        "id": "cif_es",
        "name": "CIF.es",
        "url": "https://www.cif.es/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Validação e consulta de CIF/NIF.",
    },
    {
        "id": "datoscif",
        "name": "DatosCIF",
        "url": "https://www.datoscif.es/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Base de dados de CIFs espanhóis.",
    },
    {
        "id": "ranking_empresas",
        "name": "Ranking-Empresas.com",
        "url": "https://www.ranking-empresas.com/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Rankings por facturación e sector.",
    },
    {
        "id": "yelp_es",
        "name": "Yelp España",
        "url": "https://www.yelp.es/",
        "kind": "pagina",
        "emails": "Baixo",
        "description": "Avaliações e contactos de negócios locais.",
    },
    {
        "id": "empresite_madrid",
        "name": "Empresite — Madrid",
        "url": "https://empresite.eleconomista.es/empresas/Madrid.html",
        "kind": "pagina",
        "emails": "10–15%",
        "description": "Empresas na Comunidade de Madrid.",
    },
    {
        "id": "empresite_barcelona",
        "name": "Empresite — Barcelona",
        "url": "https://empresite.eleconomista.es/empresas/Barcelona.html",
        "kind": "pagina",
        "emails": "10–15%",
        "description": "Empresas na província de Barcelona.",
    },
    {
        "id": "empresite_valencia",
        "name": "Empresite — Valencia",
        "url": "https://empresite.eleconomista.es/empresas/Valencia.html",
        "kind": "pagina",
        "emails": "10–15%",
        "description": "Empresas na Comunidade Valenciana.",
    },
    {
        "id": "empresite_sevilla",
        "name": "Empresite — Sevilla",
        "url": "https://empresite.eleconomista.es/empresas/Sevilla.html",
        "kind": "pagina",
        "emails": "10–15%",
        "description": "Empresas em Andaluzia (Sevilla).",
    },
]


def catalog_source_key(entry_id: str) -> str:
    """Mapeia ID do catálogo para a chave em SOURCES_ES."""
    if entry_id == "empresite":
        return "empresite_spain"
    return f"es_{entry_id}"


class ConfiguredSitemapSource(GenericSitemapSource):
    """Sitemap genérico com URL pré-configurada para Espanha."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        sitemap_url: str,
        country: str = "ES",
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
        country: str = "ES",
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


def build_spain_sources() -> dict[str, BaseSource]:
    from cnpj_extractor.sources.empresite_spain import EmpresiteSpainSource

    sources: dict[str, BaseSource] = {
        "empresite_spain": EmpresiteSpainSource(),
    }
    for entry in SPAIN_DIRECTORY_CATALOG:
        if entry["id"] == "empresite":
            continue
        key = catalog_source_key(entry["id"])
        if entry["kind"] == "sitemap":
            sources[key] = ConfiguredSitemapSource(
                name=f"ES — {entry['name']}",
                description=entry["description"],
                sitemap_url=entry["url"],
            )
        else:
            sources[key] = ConfiguredPageSource(
                name=f"ES — {entry['name']}",
                description=entry["description"],
                start_url=entry["url"],
            )
    sources["sitemap_generico"] = GenericSitemapSource()
    sources["website_scraper"] = WebScraperSource()
    return sources
