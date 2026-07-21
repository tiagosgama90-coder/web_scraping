from __future__ import annotations

from typing import Any

from cnpj_extractor.catalog_factory import (
    CatalogEntry,
    build_catalog_sources,
    catalog_source_key,
)
from cnpj_extractor.sources.base import BaseSource

# ---------------------------------------------------------------------------
# Espanha
# ---------------------------------------------------------------------------
SPAIN_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "empresite", "name": "Empresite (~4M empresas)", "url": "https://empresite.eleconomista.es/sitemap_EMP_ES_index.xml", "kind": "sitemap", "emails": "15–20%", "description": "Fonte principal — sitemap automático, anti-bot recomendado."},
    {"id": "empresite_provincias", "name": "Empresite — por província", "url": "https://empresite.eleconomista.es/empresas-provincia", "kind": "pagina", "emails": "10–15%", "description": "Lista por província (Madrid, Barcelona, Valencia…)."},
    {"id": "einforma", "name": "eInforma", "url": "https://www.einforma.com/", "kind": "pagina", "emails": "Baixo", "description": "Portal Informa D&B — maioria dos emails atrás de paywall."},
    {"id": "axesor", "name": "Axesor", "url": "https://www.axesor.es/", "kind": "pagina", "emails": "Baixo", "description": "Diretório comercial espanhol."},
    {"id": "iberinform", "name": "Iberinform", "url": "https://www.iberinform.es/", "kind": "pagina", "emails": "Baixo", "description": "Informação comercial e ratings."},
    {"id": "kompass", "name": "Kompass España", "url": "https://es.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "paginas_amarillas", "name": "Páginas Amarillas", "url": "https://www.paginasamarillas.es/", "kind": "pagina", "emails": "Médio", "description": "Guia local com emails nas fichas."},
    {"id": "qdq", "name": "QDQ", "url": "https://www.qdq.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório de negócios locais."},
    {"id": "cylex", "name": "Cylex España", "url": "https://www.cylex.es/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "openmercantil", "name": "OpenMercantil (BORME)", "url": "https://openmercantil.es/", "kind": "pagina", "emails": "Raro", "description": "Dados oficiais BORME — CIF e cargos."},
]

# ---------------------------------------------------------------------------
# França
# ---------------------------------------------------------------------------
FRANCE_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "societe", "name": "Societe.com", "url": "https://www.societe.com/", "kind": "pagina", "emails": "Médio", "description": "Maior diretório francês — SIREN/SIRET, fichas gratuitas."},
    {"id": "pappers", "name": "Pappers", "url": "https://www.pappers.fr/", "kind": "pagina", "emails": "Médio", "description": "Dados de empresas francesas com anti-bot."},
    {"id": "pagesjaunes", "name": "Pages Jaunes", "url": "https://www.pagesjaunes.fr/", "kind": "pagina", "emails": "Médio", "description": "Guia telefónico — emails em negócios locais."},
    {"id": "kompass", "name": "Kompass France", "url": "https://fr.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "verif", "name": "Verif.com", "url": "https://www.verif.com/", "kind": "pagina", "emails": "Baixo", "description": "Informação financeira e contactos."},
    {"id": "infogreffe", "name": "Infogreffe", "url": "https://www.infogreffe.fr/", "kind": "pagina", "emails": "Raro", "description": "Registo comercial oficial — emails raros."},
    {"id": "manageo", "name": "Manageo", "url": "https://www.manageo.fr/", "kind": "pagina", "emails": "Baixo", "description": "Fichas de empresas e indicadores."},
    {"id": "cylex", "name": "Cylex France", "url": "https://www.cylex-locale.fr/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais por cidade."},
]

# ---------------------------------------------------------------------------
# Alemanha
# ---------------------------------------------------------------------------
GERMANY_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "northdata", "name": "North Data", "url": "https://www.northdata.de/", "kind": "pagina", "emails": "Médio", "description": "Base alemã com dados de registo comercial."},
    {"id": "gelbeseiten", "name": "Gelbe Seiten", "url": "https://www.gelbeseiten.de/", "kind": "pagina", "emails": "Médio", "description": "Páginas amarelas alemãs — contactos locais."},
    {"id": "wlw", "name": "WLW (Wer liefert was)", "url": "https://www.wlw.de/", "kind": "pagina", "emails": "Médio", "description": "Diretório industrial B2B."},
    {"id": "kompass", "name": "Kompass Deutschland", "url": "https://de.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "firmenwissen", "name": "Firmenwissen", "url": "https://www.firmenwissen.de/", "kind": "pagina", "emails": "Baixo", "description": "Informação de empresas alemãs."},
    {"id": "handelsregister", "name": "Handelsregister", "url": "https://www.handelsregister.de/", "kind": "pagina", "emails": "Raro", "description": "Registo comercial oficial."},
    {"id": "cylex", "name": "Cylex Deutschland", "url": "https://www.cylex.de/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "unternehmensregister", "name": "Unternehmensregister", "url": "https://www.unternehmensregister.de/", "kind": "pagina", "emails": "Raro", "description": "Portal oficial de publicações societárias."},
]

# ---------------------------------------------------------------------------
# Itália
# ---------------------------------------------------------------------------
ITALY_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "paginegialle", "name": "Pagine Gialle", "url": "https://www.paginegialle.it/", "kind": "pagina", "emails": "Médio", "description": "Guia italiano — emails em fichas de negócio."},
    {"id": "kompass", "name": "Kompass Italia", "url": "https://it.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "registroimprese", "name": "Registro Imprese", "url": "https://www.registroimprese.it/", "kind": "pagina", "emails": "Raro", "description": "Câmara de Comércio — dados oficiais."},
    {"id": "infocamere", "name": "InfoCamere", "url": "https://www.infocamere.it/", "kind": "pagina", "emails": "Raro", "description": "Portal das Câmaras de Comércio."},
    {"id": "cerved", "name": "Cerved", "url": "https://www.cerved.com/", "kind": "pagina", "emails": "Baixo", "description": "Informação comercial italiana."},
    {"id": "cylex", "name": "Cylex Italia", "url": "https://www.cylex.it/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais."},
    {"id": "atoka", "name": "Atoka (Italia)", "url": "https://atoka.io/", "kind": "pagina", "emails": "Baixo", "description": "Inteligência comercial B2B."},
]

# ---------------------------------------------------------------------------
# Reino Unido
# ---------------------------------------------------------------------------
UK_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "yell", "name": "Yell.com", "url": "https://www.yell.com/", "kind": "pagina", "emails": "Médio", "description": "Guia de negócios UK — emails em fichas."},
    {"id": "kompass", "name": "Kompass UK", "url": "https://gb.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "endole", "name": "Endole", "url": "https://open.endole.co.uk/", "kind": "pagina", "emails": "Baixo", "description": "Dados de empresas UK (Companies House)."},
    {"id": "companieshouse", "name": "Companies House", "url": "https://find-and-update.company-information.service.gov.uk/", "kind": "pagina", "emails": "Raro", "description": "Registo oficial — emails raros."},
    {"id": "cylex", "name": "Cylex UK", "url": "https://www.cylex-uk.co.uk/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "checkcompany", "name": "CheckCompany", "url": "https://www.checkcompany.co.uk/", "kind": "pagina", "emails": "Baixo", "description": "Consulta de empresas britânicas."},
    {"id": "192", "name": "192.com", "url": "https://www.192.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório de negócios e pessoas."},
]

# ---------------------------------------------------------------------------
# México
# ---------------------------------------------------------------------------
MEXICO_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "seccionamarilla", "name": "Sección Amarilla", "url": "https://www.seccionamarilla.com.mx/", "kind": "pagina", "emails": "Médio", "description": "Guia de negócios mexicana."},
    {"id": "denue", "name": "DENUE (INEGI)", "url": "https://www.inegi.org.mx/app/mapa/denue/", "kind": "pagina", "emails": "Baixo", "description": "Diretório estatístico oficial de unidades económicas."},
    {"id": "kompass", "name": "Kompass México", "url": "https://mx.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "paginasamarillas", "name": "Páginas Amarillas MX", "url": "https://www.paginasamarillas.com.mx/", "kind": "pagina", "emails": "Médio", "description": "Guia local com contactos."},
    {"id": "cylex", "name": "Cylex México", "url": "https://www.cylex.mx/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "tuugo", "name": "Tuugo México", "url": "https://www.tuugo.mx/", "kind": "pagina", "emails": "Médio", "description": "Diretório de empresas."},
]

# ---------------------------------------------------------------------------
# Argentina
# ---------------------------------------------------------------------------
ARGENTINA_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "guiaempresas", "name": "Guía de Empresas", "url": "https://www.guiaempresas.com.ar/", "kind": "pagina", "emails": "Médio", "description": "Diretório argentino de empresas."},
    {"id": "kompass", "name": "Kompass Argentina", "url": "https://ar.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "paginasamarillas", "name": "Páginas Amarillas AR", "url": "https://www.paginasamarillas.com.ar/", "kind": "pagina", "emails": "Médio", "description": "Guia local argentina."},
    {"id": "cylex", "name": "Cylex Argentina", "url": "https://www.cylex.com.ar/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "argentinaco", "name": "ArgentinaCo", "url": "https://www.argentinaco.com/", "kind": "pagina", "emails": "Baixo", "description": "Portal de empresas argentinas."},
    {"id": "tuugo", "name": "Tuugo Argentina", "url": "https://www.tuugo.com.ar/", "kind": "pagina", "emails": "Médio", "description": "Diretório de negócios."},
]

# ---------------------------------------------------------------------------
# Colômbia
# ---------------------------------------------------------------------------
COLOMBIA_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "paginasamarillas", "name": "Páginas Amarillas CO", "url": "https://www.paginasamarillas.com.co/", "kind": "pagina", "emails": "Médio", "description": "Guia de negócios colombiana."},
    {"id": "kompass", "name": "Kompass Colombia", "url": "https://co.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "cylex", "name": "Cylex Colombia", "url": "https://www.cylex.com.co/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais."},
    {"id": "guiaempresas", "name": "Guía Empresas CO", "url": "https://www.guiaempresas.com.co/", "kind": "pagina", "emails": "Médio", "description": "Diretório de empresas."},
    {"id": "tuugo", "name": "Tuugo Colombia", "url": "https://www.tuugo.com.co/", "kind": "pagina", "emails": "Médio", "description": "Listagens de negócios."},
]

# ---------------------------------------------------------------------------
# Chile
# ---------------------------------------------------------------------------
CHILE_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "amarillas", "name": "Amarillas.cl", "url": "https://www.amarillas.cl/", "kind": "pagina", "emails": "Médio", "description": "Guia de empresas chilena."},
    {"id": "kompass", "name": "Kompass Chile", "url": "https://cl.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "cylex", "name": "Cylex Chile", "url": "https://www.cylex.cl/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "tuugo", "name": "Tuugo Chile", "url": "https://www.tuugo.cl/", "kind": "pagina", "emails": "Médio", "description": "Diretório de negócios."},
    {"id": "emol", "name": "Directorio Emol", "url": "https://www.emol.com/economia/", "kind": "pagina", "emails": "Baixo", "description": "Secção economia — empresas chilenas."},
]

# ---------------------------------------------------------------------------
# Peru
# ---------------------------------------------------------------------------
PERU_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "paginasamarillas", "name": "Páginas Amarillas PE", "url": "https://www.paginasamarillas.com.pe/", "kind": "pagina", "emails": "Médio", "description": "Guia de negócios peruana."},
    {"id": "kompass", "name": "Kompass Perú", "url": "https://pe.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "cylex", "name": "Cylex Perú", "url": "https://www.cylex.com.pe/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais."},
    {"id": "tuugo", "name": "Tuugo Perú", "url": "https://www.tuugo.com.pe/", "kind": "pagina", "emails": "Médio", "description": "Diretório de empresas."},
    {"id": "sunat", "name": "Consulta RUC (SUNAT)", "url": "https://e-consultaruc.sunat.gob.pe/", "kind": "pagina", "emails": "Raro", "description": "Registo fiscal oficial — emails raros."},
]

# ---------------------------------------------------------------------------
# Estados Unidos
# ---------------------------------------------------------------------------
USA_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "yellowpages", "name": "Yellow Pages USA", "url": "https://www.yellowpages.com/", "kind": "pagina", "emails": "Médio", "description": "Guia de negócios americano."},
    {"id": "kompass", "name": "Kompass USA", "url": "https://us.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "manta", "name": "Manta", "url": "https://www.manta.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório de pequenas empresas US."},
    {"id": "bbb", "name": "Better Business Bureau", "url": "https://www.bbb.org/", "kind": "pagina", "emails": "Baixo", "description": "Empresas acreditadas nos EUA."},
    {"id": "cylex", "name": "Cylex USA", "url": "https://www.cylex.us.com/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais."},
    {"id": "dnb", "name": "Dun & Bradstreet", "url": "https://www.dnb.com/business-directory.html", "kind": "pagina", "emails": "Baixo", "description": "Diretório comercial global."},
]

# ---------------------------------------------------------------------------
# Canadá
# ---------------------------------------------------------------------------
CANADA_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "yellowpages", "name": "Yellow Pages Canada", "url": "https://www.yellowpages.ca/", "kind": "pagina", "emails": "Médio", "description": "Guia canadiano de negócios."},
    {"id": "kompass", "name": "Kompass Canada", "url": "https://ca.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "cylex", "name": "Cylex Canada", "url": "https://www.cylex.ca/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "411", "name": "Canada411", "url": "https://www.canada411.ca/", "kind": "pagina", "emails": "Médio", "description": "Listagens telefónicas e negócios."},
    {"id": "corporations", "name": "Corporations Canada", "url": "https://ised-isde.canada.ca/cbr-rec/en/search", "kind": "pagina", "emails": "Raro", "description": "Registo federal de corporações."},
]

# ---------------------------------------------------------------------------
# Países Baixos
# ---------------------------------------------------------------------------
NETHERLANDS_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "kvk", "name": "KVK (Câmara Comércio)", "url": "https://www.kvk.nl/zoeken/", "kind": "pagina", "emails": "Baixo", "description": "Registo oficial holandês — KVK-nummer."},
    {"id": "kompass", "name": "Kompass Nederland", "url": "https://nl.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "detelefoongids", "name": "Detelefoongids", "url": "https://www.detelefoongids.nl/", "kind": "pagina", "emails": "Médio", "description": "Guia telefónico holandês."},
    {"id": "cylex", "name": "Cylex Nederland", "url": "https://www.cylex.nl/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais."},
    {"id": "bedrijvenregister", "name": "Bedrijvenregister", "url": "https://www.bedrijvenregister.nl/", "kind": "pagina", "emails": "Baixo", "description": "Consulta de empresas holandesas."},
]

# ---------------------------------------------------------------------------
# Bélgica
# ---------------------------------------------------------------------------
BELGIUM_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "kompass", "name": "Kompass Belgique", "url": "https://be.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "goldenpages", "name": "Golden Pages", "url": "https://www.goldenpages.be/", "kind": "pagina", "emails": "Médio", "description": "Guia de negócios belga."},
    {"id": "cylex", "name": "Cylex Belgique", "url": "https://www.cylex.be/", "kind": "pagina", "emails": "Médio", "description": "Listagens por cidade."},
    {"id": "kbopub", "name": "Banque-Carrefour (BCE)", "url": "https://kbopub.economie.fgov.be/", "kind": "pagina", "emails": "Raro", "description": "Registo oficial de empresas belgas."},
    {"id": "pagesdor", "name": "Pages d'Or", "url": "https://www.pagesdor.be/", "kind": "pagina", "emails": "Médio", "description": "Guia francófono belga."},
]

# ---------------------------------------------------------------------------
# Polónia
# ---------------------------------------------------------------------------
POLAND_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "panoramafirm", "name": "Panorama Firm", "url": "https://panoramafirm.pl/", "kind": "pagina", "emails": "Médio", "description": "Maior diretório polaco de empresas."},
    {"id": "kompass", "name": "Kompass Polska", "url": "https://pl.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "cylex", "name": "Cylex Polska", "url": "https://www.cylex.pl/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais."},
    {"id": "krs", "name": "KRS (Registo Nacional)", "url": "https://ekrs.ms.gov.pl/", "kind": "pagina", "emails": "Raro", "description": "Registo comercial oficial polaco."},
    {"id": "aleo", "name": "Aleo.com", "url": "https://aleo.com/pl/", "kind": "pagina", "emails": "Baixo", "description": "Opiniões e fichas de empresas."},
]

# ---------------------------------------------------------------------------
# Roménia
# ---------------------------------------------------------------------------
ROMANIA_DIRECTORY_CATALOG: list[CatalogEntry] = [
    {"id": "listafirme", "name": "ListaFirme", "url": "https://www.listafirme.ro/", "kind": "pagina", "emails": "Médio", "description": "Diretório romeno de empresas."},
    {"id": "kompass", "name": "Kompass România", "url": "https://ro.kompass.com/", "kind": "pagina", "emails": "Médio", "description": "Diretório B2B internacional."},
    {"id": "cylex", "name": "Cylex România", "url": "https://www.cylex.ro/", "kind": "pagina", "emails": "Médio", "description": "Listagens locais."},
    {"id": "mfinante", "name": "Registrul Comerțului", "url": "https://www.onrc.ro/", "kind": "pagina", "emails": "Raro", "description": "Registo comercial oficial."},
    {"id": "termene", "name": "Termene.ro", "url": "https://termene.ro/", "kind": "pagina", "emails": "Baixo", "description": "Dados financeiros de empresas romenas."},
]

# ---------------------------------------------------------------------------
# Registo de países com catálogo
# ---------------------------------------------------------------------------
COUNTRY_CATALOG_REGISTRY: dict[str, dict[str, Any]] = {
    "ES": {
        "name": "Espanha",
        "flag": "🇪🇸",
        "tax_id_label": "CIF/NIF",
        "catalog": SPAIN_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Empresite (sitemap, ~4M empresas). Anti-bot ativo.",
        "region_label": "Província",
        "region_placeholder": "Ex: Madrid, Barcelona, Valencia",
        "region_hint": "Filtra URLs Empresite que contenham o nome da província.",
        "skip_ids": {"empresite"},
        "primary_key_map": {"empresite": "empresite_spain"},
    },
    "FR": {
        "name": "França",
        "flag": "🇫🇷",
        "tax_id_label": "SIREN/SIRET",
        "catalog": FRANCE_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Societe.com ou Pages Jaunes. Teste com Pré-visualizar (25).",
        "region_label": "Região",
        "region_placeholder": "Ex: Île-de-France, Paris",
        "region_hint": "Filtro textual opcional nas URLs (quando aplicável).",
    },
    "DE": {
        "name": "Alemanha",
        "flag": "🇩🇪",
        "tax_id_label": "HRB/USt-IdNr",
        "catalog": GERMANY_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Gelbe Seiten ou North Data.",
        "region_label": "Bundesland",
        "region_placeholder": "Ex: Bayern, Berlin, NRW",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "IT": {
        "name": "Itália",
        "flag": "🇮🇹",
        "tax_id_label": "P.IVA / CF",
        "catalog": ITALY_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Pagine Gialle.",
        "region_label": "Região",
        "region_placeholder": "Ex: Lombardia, Lazio, Milano",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "GB": {
        "name": "Reino Unido",
        "flag": "🇬🇧",
        "tax_id_label": "Company No.",
        "catalog": UK_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Yell.com. Companies House raramente tem emails.",
        "region_label": "Condado / Cidade",
        "region_placeholder": "Ex: London, Manchester",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "MX": {
        "name": "México",
        "flag": "🇲🇽",
        "tax_id_label": "RFC",
        "catalog": MEXICO_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Sección Amarilla.",
        "region_label": "Estado",
        "region_placeholder": "Ex: CDMX, Jalisco, Nuevo León",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "AR": {
        "name": "Argentina",
        "flag": "🇦🇷",
        "tax_id_label": "CUIT",
        "catalog": ARGENTINA_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Guía de Empresas ou Páginas Amarillas.",
        "region_label": "Província",
        "region_placeholder": "Ex: Buenos Aires, Córdoba",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "CO": {
        "name": "Colômbia",
        "flag": "🇨🇴",
        "tax_id_label": "NIT",
        "catalog": COLOMBIA_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Páginas Amarillas Colombia.",
        "region_label": "Departamento",
        "region_placeholder": "Ex: Bogotá, Antioquia",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "CL": {
        "name": "Chile",
        "flag": "🇨🇱",
        "tax_id_label": "RUT",
        "catalog": CHILE_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Amarillas.cl.",
        "region_label": "Região",
        "region_placeholder": "Ex: Santiago, Valparaíso",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "PE": {
        "name": "Peru",
        "flag": "🇵🇪",
        "tax_id_label": "RUC",
        "catalog": PERU_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Páginas Amarillas Perú.",
        "region_label": "Departamento",
        "region_placeholder": "Ex: Lima, Arequipa",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "US": {
        "name": "Estados Unidos",
        "flag": "🇺🇸",
        "tax_id_label": "EIN",
        "catalog": USA_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Yellow Pages ou Manta.",
        "region_label": "Estado",
        "region_placeholder": "Ex: California, Texas, NY",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "CA": {
        "name": "Canadá",
        "flag": "🇨🇦",
        "tax_id_label": "BN",
        "catalog": CANADA_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Yellow Pages Canada.",
        "region_label": "Província",
        "region_placeholder": "Ex: Ontario, Quebec, BC",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "NL": {
        "name": "Países Baixos",
        "flag": "🇳🇱",
        "tax_id_label": "KVK",
        "catalog": NETHERLANDS_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Detelefoongids ou Kompass.",
        "region_label": "Província",
        "region_placeholder": "Ex: Noord-Holland, Zuid-Holland",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "BE": {
        "name": "Bélgica",
        "flag": "🇧🇪",
        "tax_id_label": "BCE/KBO",
        "catalog": BELGIUM_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Golden Pages ou Kompass.",
        "region_label": "Região",
        "region_placeholder": "Ex: Bruxelas, Flandres, Valónia",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "PL": {
        "name": "Polónia",
        "flag": "🇵🇱",
        "tax_id_label": "NIP/REGON",
        "catalog": POLAND_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: Panorama Firm.",
        "region_label": "Voivodia",
        "region_placeholder": "Ex: Mazowieckie, Małopolskie",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
    "RO": {
        "name": "Roménia",
        "flag": "🇷🇴",
        "tax_id_label": "CUI",
        "catalog": ROMANIA_DIRECTORY_CATALOG,
        "catalog_hint": "Recomendado: ListaFirme.ro.",
        "region_label": "Județ",
        "region_placeholder": "Ex: București, Cluj",
        "region_hint": "Filtro textual opcional nas URLs.",
    },
}

# Ordem no menu da aplicação
COUNTRY_MENU_ORDER: list[str] = [
    "PT", "BR", "ES", "FR", "DE", "IT", "GB",
    "MX", "AR", "CO", "CL", "PE",
    "US", "CA", "NL", "BE", "PL", "RO",
    "OUTRO",
]

CATALOG_COUNTRY_CODES: list[str] = list(COUNTRY_CATALOG_REGISTRY.keys())


def get_country_catalog(country_code: str) -> list[CatalogEntry]:
    meta = COUNTRY_CATALOG_REGISTRY.get(country_code.upper())
    return list(meta["catalog"]) if meta else []


def find_catalog_entry(country_code: str, source_key: str) -> CatalogEntry | None:
    code = country_code.upper()
    prefix = f"{code.lower()}_"
    catalog = get_country_catalog(code)
    if not catalog:
        return None
    if source_key == "empresite_spain":
        return next((e for e in catalog if e["id"] == "empresite"), None)
    if source_key.startswith(prefix):
        entry_id = source_key[len(prefix):]
        return next((e for e in catalog if e["id"] == entry_id), None)
    return None


def catalog_source_key_for_country(country_code: str, entry_id: str) -> str:
    meta = COUNTRY_CATALOG_REGISTRY.get(country_code.upper(), {})
    return catalog_source_key(
        country_code,
        entry_id,
        primary_key_map=meta.get("primary_key_map"),
    )


def build_spain_sources() -> dict[str, BaseSource]:
    from cnpj_extractor.sources.empresite_spain import EmpresiteSpainSource

    meta = COUNTRY_CATALOG_REGISTRY["ES"]
    return build_catalog_sources(
        "ES",
        meta["catalog"],
        primary_sources={"empresite_spain": EmpresiteSpainSource()},
        skip_ids=meta.get("skip_ids"),
        primary_key_map=meta.get("primary_key_map"),
    )


def build_catalog_country_sources(country_code: str) -> dict[str, BaseSource]:
    code = country_code.upper()
    if code == "ES":
        return build_spain_sources()
    meta = COUNTRY_CATALOG_REGISTRY.get(code)
    if not meta:
        return {}
    return build_catalog_sources(
        code,
        meta["catalog"],
        skip_ids=meta.get("skip_ids"),
        primary_key_map=meta.get("primary_key_map"),
    )


def all_catalog_entries() -> list[tuple[str, CatalogEntry]]:
    rows: list[tuple[str, CatalogEntry]] = []
    for code, meta in COUNTRY_CATALOG_REGISTRY.items():
        for entry in meta["catalog"]:
            rows.append((code, entry))
    return rows
