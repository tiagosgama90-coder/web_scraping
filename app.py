#!/usr/bin/env python3
"""Interface web para extração de e-mails de empresas brasileiras."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from cnpj_extractor.database import export_csv, export_sqlite
from cnpj_extractor.sources import COMMERCIAL_SOURCES_INFO, SOURCES
from cnpj_extractor.utils import dedupe_records, format_cnpj, parse_cnpj_list

st.set_page_config(
    page_title="CNPJ Email Extractor",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0ea5e9 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 10px 40px rgba(14, 165, 233, 0.2);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }

    .main-header p {
        margin: 0.5rem 0 0;
        opacity: 0.9;
        font-size: 1.05rem;
    }

    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        text-align: center;
    }

    .metric-card .value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0ea5e9;
    }

    .metric-card .label {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .source-badge {
        display: inline-block;
        background: #ecfdf5;
        color: #047857;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .warning-box {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 1rem 1.25rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }

    .stDownloadButton button {
        background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    div[data-testid="stSidebar"] {
        background: #f8fafc;
    }

    code {
        font-family: 'JetBrains Mono', monospace !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="main-header">
        <h1>📧 CNPJ Email Extractor</h1>
        <p>Extraia e-mails de empresas brasileiras a partir de dados públicos oficiais — exporte para SQLite ou CSV</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "records" not in st.session_state:
    st.session_state.records = []
if "last_export_sqlite" not in st.session_state:
    st.session_state.last_export_sqlite = None
if "last_export_csv" not in st.session_state:
    st.session_state.last_export_csv = None


def update_progress(progress_bar, status_text, value: float, message: str) -> None:
    progress_bar.progress(min(max(value, 0.0), 1.0))
    status_text.markdown(f"**Status:** {message}")


with st.sidebar:
    st.markdown("### ⚙️ Configuração")
    source_key = st.selectbox(
        "Fonte de dados",
        options=list(SOURCES.keys()),
        format_func=lambda key: SOURCES[key].name,
        help="Escolha a origem dos dados",
    )
    source = SOURCES[source_key]
    st.caption(source.description)

    st.markdown("---")
    st.markdown("### 🔍 Filtros")

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
    only_with_email = st.checkbox("Apenas com e-mail válido", value=True)

    max_records = st.number_input(
        "Limite de registros",
        min_value=10,
        max_value=1_000_000,
        value=500,
        step=50,
        help="Limite para evitar extrações muito longas",
    )

    st.markdown("---")
    st.markdown("### 📋 CNPJs específicos")
    cnpj_text = st.text_area(
        "Lista de CNPJs (opcional)",
        placeholder="Um CNPJ por linha ou separados por vírgula\nEx: 33.000.167/0001-01",
        height=120,
    )
    cnpj_list = parse_cnpj_list(cnpj_text)

    if source_key == "receita_federal":
        st.markdown("---")
        st.markdown("### 📦 Receita Federal")
        try:
            releases = source.list_available_releases()
            release = st.selectbox("Versão dos dados", options=releases[::-1], index=0)
        except Exception as exc:
            st.error(f"Erro ao listar versões: {exc}")
            release = None

        partition_mode = st.radio(
            "Partições",
            options=["Amostra (1 ficheiro)", "UF filtrado (3 ficheiros)", "Completo (10 ficheiros)"],
            index=0,
        )
        if partition_mode.startswith("Amostra"):
            partitions = [0]
        elif partition_mode.startswith("UF"):
            partitions = [0, 1, 2]
        else:
            partitions = list(range(10))

        load_razao_social = st.checkbox("Carregar razão social (mais lento)", value=True)
        cnae_filter = None
    else:
        release = None
        partitions = None
        load_razao_social = True
        cnae_filter = st.text_input("CNAE (opcional)", placeholder="Ex: 6202300")

tab_extract, tab_results, tab_export, tab_info = st.tabs(
    ["🚀 Extrair", "📊 Resultados", "💾 Exportar", "ℹ️ Sobre"]
)

with tab_extract:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="metric-card"><div class="value">67M+</div><div class="label">Empresas na base</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="metric-card"><div class="value">Grátis</div><div class="label">Dados públicos oficiais</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="metric-card"><div class="value">SQLite + CSV</div><div class="label">Compatível DB Browser</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    if st.button("▶️ Iniciar extração", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def callback(value: float, message: str) -> None:
            update_progress(progress_bar, status_text, value, message)

        records: list[dict] = []
        try:
            kwargs: dict = {
                "max_records": int(max_records),
                "progress_callback": callback,
            }

            if source_key == "receita_federal":
                kwargs.update(
                    {
                        "release": release,
                        "partitions": partitions,
                        "uf_filter": uf_value,
                        "only_active": only_active,
                        "only_with_email": only_with_email,
                        "load_razao_social": load_razao_social,
                    }
                )
            elif source_key == "dadosbrasil_api":
                kwargs.update(
                    {
                        "cnpj_list": cnpj_list or None,
                        "uf": uf_value,
                        "cnae": cnae_filter or None,
                    }
                )
            elif source_key == "dadosbrasil_scraper":
                if not cnpj_list:
                    st.error("O web scraper requer uma lista de CNPJs.")
                    st.stop()
                kwargs["cnpj_list"] = cnpj_list

            for record in source.extract(**kwargs):
                row = record.to_dict()
                row["cnpj"] = format_cnpj(row["cnpj"])
                records.append(row)

            records = dedupe_records(records)
            st.session_state.records = records
            update_progress(progress_bar, status_text, 1.0, f"Concluído — {len(records)} e-mails encontrados")
            st.success(f"✅ Extração concluída: **{len(records)}** registos com e-mail")
        except Exception as exc:
            st.error(f"Erro na extração: {exc}")

with tab_results:
    records = st.session_state.records
    if not records:
        st.info("Nenhum dado extraído ainda. Vá ao separador **Extrair** para começar.")
    else:
        df = pd.DataFrame(records)
        st.markdown(f"**{len(df)}** registos encontrados")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("E-mails únicos", df["email"].nunique())
        with col_b:
            st.metric("UFs", df["uf"].nunique() if "uf" in df else 0)
        with col_c:
            st.metric("Fontes", df["fonte"].nunique() if "fonte" in df else 1)

        search = st.text_input("🔎 Pesquisar", placeholder="Filtrar por CNPJ, e-mail ou razão social...")
        display_df = df
        if search:
            mask = df.apply(
                lambda row: row.astype(str).str.contains(search, case=False, na=False).any(),
                axis=1,
            )
            display_df = df[mask]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "email": st.column_config.TextColumn("E-mail"),
                "cnpj": st.column_config.TextColumn("CNPJ"),
                "razao_social": st.column_config.TextColumn("Razão Social"),
                "uf": st.column_config.TextColumn("UF"),
            },
        )

with tab_export:
    records = st.session_state.records
    if not records:
        st.info("Extraia dados primeiro para poder exportar.")
    else:
        st.markdown("### Exportar para DB Browser for SQLite")
        st.markdown(
            "A base de dados SQLite criada é compatível com [DB Browser for SQLite](https://sqlitebrowser.org/). "
            "A tabela principal chama-se `empresas`."
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"empresas_emails_{timestamp}"

        export_name = st.text_input("Nome do ficheiro", value=default_name)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Gerar SQLite (.db)", use_container_width=True):
                with tempfile.TemporaryDirectory() as tmp:
                    db_path = Path(tmp) / f"{export_name}.db"
                    export_sqlite(records, db_path)
                    st.session_state.last_export_sqlite = db_path.read_bytes()
                st.success("Base de dados SQLite gerada!")

            if st.session_state.last_export_sqlite:
                st.download_button(
                    label="⬇️ Descarregar SQLite",
                    data=st.session_state.last_export_sqlite,
                    file_name=f"{export_name}.db",
                    mime="application/x-sqlite3",
                    use_container_width=True,
                )

        with col2:
            if st.button("📄 Gerar CSV", use_container_width=True):
                with tempfile.TemporaryDirectory() as tmp:
                    csv_path = Path(tmp) / f"{export_name}.csv"
                    export_csv(records, csv_path)
                    st.session_state.last_export_csv = csv_path.read_bytes()
                st.success("Ficheiro CSV gerado!")

            if st.session_state.last_export_csv:
                st.download_button(
                    label="⬇️ Descarregar CSV",
                    data=st.session_state.last_export_csv,
                    file_name=f"{export_name}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        st.markdown("---")
        st.markdown("#### Esquema da tabela `empresas`")
        st.code(
            """CREATE TABLE empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT NOT NULL,
    razao_social TEXT,
    nome_fantasia TEXT,
    email TEXT NOT NULL,
    telefone TEXT,
    uf TEXT,
    municipio TEXT,
    cnae TEXT,
    situacao TEXT,
    fonte TEXT,
    data_extracao TEXT
);""",
            language="sql",
        )

with tab_info:
    st.markdown("### Fontes de dados suportadas")
    for key, src in SOURCES.items():
        st.markdown(f'<span class="source-badge">✓ {src.name}</span>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown(
        """
        Este software extrai e-mails de **dados públicos oficiais** da Receita Federal do Brasil,
        organizados e disponibilizados gratuitamente.
        """
    )

    st.markdown("### Plataformas comerciais referenciadas")
    for info in COMMERCIAL_SOURCES_INFO.values():
        with st.expander(f"🔗 {info['name']}"):
            st.markdown(f"**URL:** [{info['url']}]({info['url']})")
            st.markdown(f'<div class="warning-box">{info["note"]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Como usar")
    st.markdown(
        """
        1. **Escolha a fonte** na barra lateral (recomendado: DadosBrasil API para testes rápidos)
        2. **Configure filtros** — UF, limite de registros, apenas ativas
        3. **Clique em Iniciar extração**
        4. **Veja os resultados** no separador Resultados
        5. **Exporte** para SQLite ou CSV e abra no DB Browser for SQLite

        **Dica:** Para extrações em massa de todo o Brasil, use a fonte **Receita Federal** com partições completas.
        O processo pode demorar várias horas e requer ~15 GB de espaço em disco.
        """
    )

    st.markdown("---")
    st.markdown("### Executar localmente")
    st.code(
        """pip install -r requirements.txt
streamlit run app.py""",
        language="bash",
    )
