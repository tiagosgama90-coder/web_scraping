#!/usr/bin/env python3
"""Interface web para extração de e-mails de empresas (Brasil e Portugal)."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from cnpj_extractor.database import export_csv, export_sqlite
from cnpj_extractor.sources import COMMERCIAL_SOURCES_INFO, COUNTRIES
from cnpj_extractor.sources.fiz_portugal import FIZ_SITEMAP_INDEX
from cnpj_extractor.utils import dedupe_records, format_cnpj, parse_cnpj_list

st.set_page_config(
    page_title="Company Email Extractor",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0ea5e9 100%);
        padding: 2rem 2.5rem; border-radius: 16px; margin-bottom: 1.5rem; color: white;
        box-shadow: 0 10px 40px rgba(14, 165, 233, 0.2);
    }
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .main-header p { margin: 0.5rem 0 0; opacity: 0.9; font-size: 1.05rem; }
    .metric-card {
        background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 1rem 1.25rem; text-align: center;
    }
    .metric-card .value { font-size: 1.75rem; font-weight: 700; color: #0ea5e9; }
    .metric-card .label {
        font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .source-badge {
        display: inline-block; background: #ecfdf5; color: #047857;
        padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem;
        font-weight: 500; margin-right: 0.5rem; margin-bottom: 0.5rem;
    }
    .warning-box {
        background: #fffbeb; border-left: 4px solid #f59e0b;
        padding: 1rem 1.25rem; border-radius: 0 8px 8px 0; margin: 1rem 0;
    }
    div[data-testid="stSidebar"] { background: #f8fafc; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <div class="main-header">
        <h1>📧 Company Email Extractor</h1>
        <p>Brasil 🇧🇷 e Portugal 🇵🇹 — extração automática via sitemap, API ou dados abertos oficiais</p>
    </div>
    """,
    unsafe_allow_html=True,
)

for key in ("records", "last_export_sqlite", "last_export_csv"):
    if key not in st.session_state:
        st.session_state[key] = [] if key == "records" else None


def update_progress(progress_bar, status_text, value: float, message: str) -> None:
    progress_bar.progress(min(max(value, 0.0), 1.0))
    status_text.markdown(f"**Status:** {message}")


def format_tax_id(value: str, country: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if country == "BR" and len(digits) == 14:
        return format_cnpj(digits)
    return digits or value


with st.sidebar:
    st.markdown("### 🌍 País")
    country_key = st.selectbox(
        "Selecione o país",
        options=list(COUNTRIES.keys()),
        format_func=lambda k: f"{COUNTRIES[k]['flag']} {COUNTRIES[k]['name']}",
    )
    country = COUNTRIES[country_key]
    country_sources = country["sources"]

    st.markdown("### ⚙️ Fonte de dados")
    source_key = st.selectbox(
        "Fonte",
        options=list(country_sources.keys()),
        format_func=lambda key: country_sources[key].name,
    )
    source = country_sources[source_key]
    st.caption(source.description)

    st.markdown("---")
    st.markdown("### 🔍 Filtros")
    only_with_email = st.checkbox("Apenas com e-mail válido", value=True)

    extraction_mode = st.radio(
        "Modo de extração",
        options=["automatico", "limitado"],
        format_func=lambda x: "🔄 Automático (sitemap completo)" if x == "automatico" else "🔢 Limitado (teste rápido)",
        help="Automático descobre todas as páginas do sitemap sozinho",
    )

    if extraction_mode == "limitado":
        max_records = st.number_input("Limite de registros", min_value=10, max_value=1_000_000, value=100, step=50)
    else:
        max_records = st.number_input(
            "Limite de registros (0 = sem limite)",
            min_value=0,
            max_value=10_000_000,
            value=0,
            step=1000,
            help="Use 0 para extrair tudo. Atenção: pode demorar horas.",
        )
        max_records = None if max_records == 0 else int(max_records)

    # Brasil-specific
    uf_value = None
    only_active = True
    cnpj_list: list[str] = []
    release = None
    partitions = None
    load_razao_social = True
    cnae_filter = None

    if country_key == "BR":
        uf_filter = st.selectbox(
            "Estado (UF)",
            options=["Todos"] + [
                "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
                "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
                "RS", "RO", "RR", "SC", "SP", "SE", "TO",
            ],
        )
        uf_value = None if uf_filter == "Todos" else uf_filter
        only_active = st.checkbox("Apenas empresas ativas", value=True)

        st.markdown("### 📋 CNPJs específicos")
        cnpj_text = st.text_area(
            "Lista de CNPJs (opcional)",
            placeholder="Um CNPJ por linha\nEx: 33.000.167/0001-01",
            height=100,
        )
        cnpj_list = parse_cnpj_list(cnpj_text)

        if source_key == "receita_federal":
            st.markdown("### 📦 Receita Federal")
            try:
                releases = source.list_available_releases()
                release = st.selectbox("Versão dos dados", options=releases[::-1], index=0)
            except Exception as exc:
                st.error(f"Erro: {exc}")
                release = None

            if extraction_mode == "automatico":
                partitions = list(range(10))
                st.info("Modo automático: processa as 10 partições nacionais (~67M empresas).")
            else:
                partition_mode = st.radio(
                    "Partições",
                    options=["Amostra (1)", "Parcial (3)", "Completo (10)"],
                    index=0,
                )
                partitions = [0] if partition_mode.startswith("Amostra") else (
                    [0, 1, 2] if partition_mode.startswith("Parcial") else list(range(10))
                )
            load_razao_social = st.checkbox("Carregar razão social", value=True)
        elif source_key == "dadosbrasil_api":
            cnae_filter = st.text_input("CNAE (opcional)", placeholder="Ex: 6202300")

    # Portugal-specific
    sitemap_url = FIZ_SITEMAP_INDEX
    distrito_filter = None
    if country_key == "PT":
        auto_discover = extraction_mode == "automatico"
        if source_key == "fiz_portugal":
            try:
                total_pages = source.discover_total_pages()
                st.info(f"Sitemap automático: **{total_pages} páginas** (~{total_pages * 5000:,} empresas)")
            except Exception:
                st.info("Sitemap automático: descobre todas as páginas sozinho.")
            distrito_filter = st.text_input("Filtrar por distrito/cidade (opcional)", placeholder="Ex: lisboa")
        elif source_key == "sitemap_generico":
            sitemap_url = st.text_input(
                "URL do sitemap",
                value="https://diretorio.fiz.co/sitemap.xml",
                help="Cole o sitemap.xml ou a primeira página (/empresas/1)",
            )

tab_extract, tab_results, tab_export, tab_info = st.tabs(
    ["🚀 Extrair", "📊 Resultados", "💾 Exportar", "ℹ️ Guia"]
)

with tab_extract:
    stats = {
        "BR": ("67M+", "Dados públicos RFB"),
        "PT": ("490K+", "Sitemap automático FIZ"),
    }
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="value">{stats[country_key][0]}</div><div class="label">Empresas</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="value">{country["flag"]}</div><div class="label">{country["name"]}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card"><div class="value">SQLite + CSV</div><div class="label">DB Browser</div></div>', unsafe_allow_html=True)

    if st.button("▶️ Iniciar extração", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        records: list[dict] = []

        def callback(value: float, message: str) -> None:
            update_progress(progress_bar, status_text, value, message)

        try:
            kwargs: dict = {
                "max_records": max_records,
                "only_with_email": only_with_email,
                "progress_callback": callback,
            }

            if source_key == "receita_federal":
                kwargs.update({
                    "release": release, "partitions": partitions,
                    "uf_filter": uf_value, "only_active": only_active,
                    "load_razao_social": load_razao_social,
                })
            elif source_key == "dadosbrasil_api":
                kwargs.update({"cnpj_list": cnpj_list or None, "uf": uf_value, "cnae": cnae_filter or None})
            elif source_key == "dadosbrasil_scraper":
                if not cnpj_list:
                    st.error("O scraper BR requer lista de CNPJs.")
                    st.stop()
                kwargs["cnpj_list"] = cnpj_list
            elif source_key == "fiz_portugal":
                kwargs.update({
                    "auto_discover": True,
                    "distrito": distrito_filter or None,
                    "max_sitemap_pages": None if extraction_mode == "automatico" else 1,
                })
            elif source_key == "sitemap_generico":
                kwargs.update({
                    "sitemap_url": sitemap_url,
                    "auto_discover": extraction_mode == "automatico",
                })

            for record in source.extract(**kwargs):
                row = record.to_dict()
                row["cnpj"] = format_tax_id(row["cnpj"], country_key)
                records.append(row)

            records = dedupe_records(records)
            st.session_state.records = records
            update_progress(progress_bar, status_text, 1.0, f"Concluído — {len(records):,} e-mails")
            st.success(f"✅ **{len(records):,}** registos extraídos ({country['name']})")
        except Exception as exc:
            st.error(f"Erro: {exc}")

with tab_results:
    records = st.session_state.records
    if not records:
        st.info("Nenhum dado extraído. Vá ao separador **Extrair**.")
    else:
        df = pd.DataFrame(records)
        st.markdown(f"**{len(df):,}** registos")
        c1, c2, c3 = st.columns(3)
        c1.metric("E-mails únicos", df["email"].nunique())
        c2.metric("Países", df["pais"].nunique() if "pais" in df else 1)
        c3.metric("Municípios", df["municipio"].nunique() if "municipio" in df else 0)

        search = st.text_input("🔎 Pesquisar")
        display_df = df
        if search:
            mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False, na=False).any(), axis=1)
            display_df = df[mask]

        tax_label = country["tax_id_label"]
        st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={
            "cnpj": st.column_config.TextColumn(tax_label),
            "email": st.column_config.TextColumn("E-mail"),
            "razao_social": st.column_config.TextColumn("Razão Social"),
            "municipio": st.column_config.TextColumn("Município"),
            "pais": st.column_config.TextColumn("País"),
        })

with tab_export:
    records = st.session_state.records
    if not records:
        st.info("Extraia dados primeiro.")
    else:
        st.markdown("### Exportar para DB Browser for SQLite")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = st.text_input("Nome do ficheiro", value=f"empresas_{country_key.lower()}_{ts}")
        c1, c2 = st.columns(2)

        with c1:
            if st.button("💾 Gerar SQLite", use_container_width=True):
                with tempfile.TemporaryDirectory() as tmp:
                    p = Path(tmp) / f"{export_name}.db"
                    export_sqlite(records, p)
                    st.session_state.last_export_sqlite = p.read_bytes()
                st.success("SQLite gerado!")
            if st.session_state.last_export_sqlite:
                st.download_button("⬇️ Descarregar .db", st.session_state.last_export_sqlite,
                                   f"{export_name}.db", "application/x-sqlite3", use_container_width=True)

        with c2:
            if st.button("📄 Gerar CSV", use_container_width=True):
                with tempfile.TemporaryDirectory() as tmp:
                    p = Path(tmp) / f"{export_name}.csv"
                    export_csv(records, p)
                    st.session_state.last_export_csv = p.read_bytes()
                st.success("CSV gerado!")
            if st.session_state.last_export_csv:
                st.download_button("⬇️ Descarregar .csv", st.session_state.last_export_csv,
                                   f"{export_name}.csv", "text/csv", use_container_width=True)

with tab_info:
    st.markdown("## 🇵🇹 Portugal — Diretório FIZ")
    st.markdown("""
    1. Selecione **Portugal** na barra lateral
    2. Fonte: **Diretório FIZ (Portugal)**
    3. Modo: **Automático (sitemap completo)** — descobre as 98 páginas sozinho
    4. Clique **Iniciar extração**
    5. Exporte para SQLite ou CSV

    **URL do sitemap:** `https://diretorio.fiz.co/sitemap.xml` (98 páginas × 5.000 empresas = ~490.000)

    **CLI Portugal (completo):**
    ```bash
    python3 -m cnpj_extractor.cli --pais PT --fonte fiz_portugal --auto -o portugal.db
    ```
    """)

    st.markdown("## 🇧🇷 Brasil — Receita Federal")
    st.markdown("""
    1. Selecione **Brasil**
    2. Fonte: **Receita Federal** (massa) ou **DadosBrasil API** (rápido)
    3. Modo automático: processa as 10 partições nacionais
    4. Exporte para SQLite ou CSV

    **CLI Brasil (completo):**
    ```bash
    python3 -m cnpj_extractor.cli --pais BR --fonte receita_federal --auto -o brasil.db
    ```
    """)

    st.markdown("## 🔗 Outros sites com sitemap")
    st.markdown("""
    Para qualquer site com estrutura semelhante, use **Sitemap Genérico** e cole o URL:
    - `https://site.com/sitemap.xml` (índice com todas as páginas)
    - `https://site.com/api/sitemap/empresas/1` (primeira página)

    O software descobre automaticamente quantas páginas existem.
    """)

    st.markdown("### Fontes disponíveis")
    for ck, cdata in COUNTRIES.items():
        st.markdown(f"**{cdata['flag']} {cdata['name']}**")
        for src in cdata["sources"].values():
            st.markdown(f'<span class="source-badge">✓ {src.name}</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")
