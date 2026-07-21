#!/usr/bin/env python3
"""Aplicação desktop nativa — Company Email Extractor v2.16.1."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from cnpj_extractor.custom_sources import (
    SOURCE_TYPES,
    CustomSource,
    add_custom_source,
    delete_custom_source,
    load_custom_sources,
    parse_url_list,
)
from cnpj_extractor.database import (
    CHUNK_SIZE_DEFAULT,
    ChunkExportResult,
    export_csv,
    export_emails_for_marketing_csv,
    export_emails_only_csv,
    export_emails_only_csv_chunked,
    export_emails_txt_chunked,
    export_filtered_csv,
    export_filtered_csv_chunked,
    export_sqlite,
)
from cnpj_extractor.email_validator import filter_records_with_mx
from cnpj_extractor.field_filters import (
    AVAILABLE_FIELDS,
    DEFAULT_FIELD_KEYS,
    filter_records_by_requirements,
)
from cnpj_extractor.gui_text import ADD_SOURCE_HELP, GUIDE_TEXT
from cnpj_extractor.fingerprint_privacy import (
    clear_fingerprint_masking,
    generate_fingerprint_profile,
    get_fingerprint_profile,
    set_fingerprint_masking,
)
from cnpj_extractor.free_proxy_pool import (
    acquire_working_proxy,
    clear_free_proxy_cache,
    get_cached_working_proxy,
    prewarm_proxy_pool,
)
from cnpj_extractor.ip_check import IpInfo, lookup_ip
from cnpj_extractor.privacy_hud import format_privacy_hud
from cnpj_extractor.proxy_config import (
    clear_active_proxy,
    clear_free_proxy_mode,
    get_active_proxy,
    is_valid_proxy_url,
    mask_proxy_for_display,
    normalize_proxy_url,
    set_active_proxy,
    set_free_proxy_mode,
)
from cnpj_extractor.sector_filters import (
    get_sector_hint,
    get_sector_label,
    get_sector_placeholder,
    matches_sector,
    parse_sector_filters,
)
from cnpj_extractor.country_catalogs import (
    CATALOG_COUNTRY_CODES,
    COUNTRY_CATALOG_REGISTRY,
    find_catalog_entry,
)
from cnpj_extractor.sources import COUNTRIES, COUNTRY_MENU_ORDER
from cnpj_extractor.sources.custom_adapter import CustomSourceAdapter
from cnpj_extractor.sources.fiz_portugal import FIZ_SITEMAP_INDEX
from cnpj_extractor.sources.receita_federal import ReceitaFederalSource
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.sources.website_scraper import WebScraperSource
from cnpj_extractor.streaming_export import StreamingExporter
from cnpj_extractor.utils import dedupe_by_email, dedupe_records, filter_valid_email_records, format_cnpj

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_NAME = "Company Email Extractor"
APP_VERSION = "2.16.1"

HUD_BG = "#060b14"
HUD_FG = "#00a8ff"
HUD_BORDER = "#0d47a1"
HUD_FONT = ("Consolas", 12)

ACTIVITY_BG = ("gray94", "gray14")
ACTIVITY_FG = ("gray15", "#9fd4ff")
ACTIVITY_FONT = ("Consolas", 10)
MAX_ACTIVITY_LINES = 500

DEFAULT_BASE_DIR = Path.home() / "Documents" / "CompanyEmailExtractor"
DEFAULT_DATA_DIR = DEFAULT_BASE_DIR / "downloads"
DEFAULT_EXPORT_DIR = DEFAULT_BASE_DIR / "export"
CUSTOM_PREFIX = "✦ "
SPECIAL_SOURCES = {
    "__scraper__": "🌐 Scraper Universal (qualquer URL)",
    "__add__": "➕ Adicionar nova fonte...",
}

BRAZIL_UFS = [
    "Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS",
    "RO", "RR", "SC", "SP", "SE", "TO",
]
BRAZIL_UF_CODES = [uf for uf in BRAZIL_UFS if uf != "Todos"]


class AddSourceDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, on_saved) -> None:
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("Adicionar Nova Fonte")
        self.geometry("520x580")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="➕ Nova Base de Dados / Site", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(16, 8)
        )

        form = ctk.CTkFrame(self)
        form.pack(fill="both", expand=True, padx=20, pady=8)

        ctk.CTkLabel(form, text="Nome da fonte", anchor="w").pack(fill="x", pady=(8, 0))
        self.name_var = ctk.StringVar(value="Minha base de dados")
        ctk.CTkEntry(form, textvariable=self.name_var).pack(fill="x", pady=4)

        ctk.CTkLabel(form, text="Tipo", anchor="w").pack(fill="x", pady=(8, 0))
        self.type_var = ctk.StringVar(value="sitemap")
        ctk.CTkOptionMenu(form, variable=self.type_var, values=list(SOURCE_TYPES.keys()),
                          command=self._on_type_change).pack(fill="x", pady=4)
        self.type_hint = ctk.CTkLabel(form, text=SOURCE_TYPES["sitemap"], text_color="gray", wraplength=440, anchor="w")
        self.type_hint.pack(fill="x", pady=2)

        ctk.CTkLabel(form, text="País", anchor="w").pack(fill="x", pady=(8, 0))
        self.country_var = ctk.StringVar(value="OUTRO")
        ctk.CTkOptionMenu(form, variable=self.country_var, values=COUNTRY_MENU_ORDER).pack(fill="x", pady=4)

        ctk.CTkLabel(form, text="URL principal / Sitemap", anchor="w").pack(fill="x", pady=(8, 0))
        self.url_var = ctk.StringVar(value="https://")
        ctk.CTkEntry(form, textvariable=self.url_var, placeholder_text="https://site.com/sitemap.xml").pack(fill="x", pady=4)

        self.urls_frame = ctk.CTkFrame(form, fg_color="transparent")
        ctk.CTkLabel(self.urls_frame, text="Lista de URLs (uma por linha)", anchor="w").pack(fill="x")
        self.urls_box = ctk.CTkTextbox(self.urls_frame, height=100)
        self.urls_box.pack(fill="x", pady=4)
        ctk.CTkButton(self.urls_frame, text="📂 Importar ficheiro .txt", command=self._import_urls).pack(anchor="w")

        self.auto_var = ctk.BooleanVar(value=True)
        self.auto_check = ctk.CTkCheckBox(form, text="Descoberta automática (sitemap / seguir links)", variable=self.auto_var)
        self.auto_check.pack(anchor="w", pady=8)

        ctk.CTkLabel(form, text="Notas (opcional)", anchor="w").pack(fill="x", pady=(8, 0))
        self.notes_box = ctk.CTkTextbox(form, height=50)
        self.notes_box.pack(fill="x", pady=4)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=16)
        ctk.CTkButton(btns, text="Cancelar", fg_color="gray40", command=self.destroy).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="💾 Guardar Fonte", command=self._save).pack(side="right", padx=4)

        self._on_type_change("sitemap")

    def _on_type_change(self, choice: str) -> None:
        self.type_hint.configure(text=SOURCE_TYPES.get(choice, ""))
        if choice == "urls":
            self.urls_frame.pack(fill="x", pady=4)
        else:
            self.urls_frame.pack_forget()

    def _import_urls(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")])
        if path:
            self.urls_box.delete("1.0", "end")
            self.urls_box.insert("1.0", open(path, encoding="utf-8", errors="ignore").read())

    def _save(self) -> None:
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        stype = self.type_var.get()
        if not name:
            messagebox.showwarning(APP_NAME, "Indique um nome para a fonte.")
            return
        if stype != "urls" and (not url or url == "https://"):
            messagebox.showwarning(APP_NAME, "Indique o URL do sitemap ou página.")
            return
        url_list = self.urls_box.get("1.0", "end").strip() if stype == "urls" else ""
        if stype == "urls" and not url_list and not url:
            messagebox.showwarning(APP_NAME, "Cole pelo menos um URL ou importe um ficheiro.")
            return

        source = CustomSource(
            id="",
            name=name,
            url=url,
            source_type=stype,
            country=self.country_var.get(),
            auto_discover=self.auto_var.get(),
            url_list=url_list,
            notes=self.notes_box.get("1.0", "end").strip(),
        )
        add_custom_source(source)
        self.on_saved()
        messagebox.showinfo(APP_NAME, f"Fonte '{name}' guardada com sucesso!")
        self.destroy()


class CompanyEmailApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1240x760")
        self.minsize(880, 520)
        self.resizable(True, True)

        self.records: list[dict] = []
        self._stream_total = 0
        self._stream_results: list = []
        self._stream_root: Path | None = None
        self._extracting = False
        self._is_preview = False
        self._stop_requested = False
        self._custom_sources: list[CustomSource] = []
        self._source_map: dict[str, str] = {}
        self._selected_export_fields: list[str] = list(DEFAULT_FIELD_KEYS)
        self._hud_ready = False
        self._last_real_ip: IpInfo | None = None
        self._last_hidden_ip: IpInfo | None = None
        self._last_logged_count = 0

        self._build_ui()
        self.start_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")
        self._refresh_custom_sources()
        self._on_country_change()
        self._show_welcome_if_first_run()
        self._start_hide_ip_prewarm()
        if self.fingerprint_mask_var.get():
            self._on_fingerprint_mask_change()
        self._refresh_privacy_status_async()

    def _show_welcome_if_first_run(self) -> None:
        if not load_custom_sources():
            self.tabview.set("📖 Guia")
            self._set_status("Bem-vindo! Leia o Guia e depois comece com um teste rápido (limite 50).")

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(sidebar, text="📧 Email Extractor", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20, 2), sticky="w"
        )
        ctk.CTkLabel(sidebar, text="BR • PT • ES • FR • DE • IT • +12 países", font=ctk.CTkFont(size=11), text_color="gray").grid(
            row=1, column=0, padx=20, pady=(0, 8), sticky="w"
        )

        ctk.CTkLabel(sidebar, text="País (filtros)", anchor="w").grid(row=2, column=0, padx=20, sticky="ew")
        self.country_var = ctk.StringVar(value="PT")
        ctk.CTkOptionMenu(
            sidebar,
            variable=self.country_var,
            values=COUNTRY_MENU_ORDER,
            command=self._on_country_change,
            width=260,
        ).grid(row=3, column=0, padx=20, pady=(4, 6))

        ctk.CTkLabel(sidebar, text="Base de dados / Diretório", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=4, column=0, padx=20, sticky="ew")
        self.source_var = ctk.StringVar(value="")
        self.source_menu = ctk.CTkOptionMenu(
            sidebar,
            variable=self.source_var,
            width=260,
            command=self._on_source_selected,
            dynamic_resizing=False,
        )
        self.source_menu.grid(row=5, column=0, padx=20, pady=(4, 2))
        ctk.CTkLabel(
            sidebar,
            text="Todas as bases por país — escolha aqui (FIZ, Empresite, Receita…)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=260,
            justify="left",
        ).grid(row=6, column=0, padx=20, pady=(0, 6), sticky="w")

        sidebar_scroll = ctk.CTkScrollableFrame(sidebar, label_text="Opções avançadas")
        sidebar_scroll.grid(row=7, column=0, padx=12, pady=(0, 6), sticky="nsew")
        sidebar_scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sidebar_scroll, text="Modo", anchor="w").pack(fill="x", padx=4)
        self.mode_var = ctk.StringVar(value="limitado")
        ctk.CTkOptionMenu(sidebar_scroll, variable=self.mode_var,
                          values=["limitado", "automatico"], width=260).pack(fill="x", padx=4, pady=(4, 10))

        ctk.CTkLabel(sidebar_scroll, text="Limite (0 = sem limite)", anchor="w").pack(fill="x", padx=4)
        self.max_var = ctk.StringVar(value="100")
        ctk.CTkEntry(sidebar_scroll, textvariable=self.max_var, width=260).pack(fill="x", padx=4, pady=(4, 10))

        self.filter_frame = ctk.CTkFrame(sidebar_scroll, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=4)

        self.fields_scroll = ctk.CTkScrollableFrame(sidebar_scroll, height=100, label_text="Campos a exportar")
        self.fields_scroll.pack(fill="x", padx=4, pady=(4, 4))
        self.field_vars: dict[str, ctk.BooleanVar] = {}
        self._build_field_selector()

        self.only_email_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sidebar_scroll, text="Obrigatório ter e-mail", variable=self.only_email_var).pack(
            fill="x", padx=4, pady=2
        )
        self.require_phone_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(sidebar_scroll, text="Obrigatório ter telefone", variable=self.require_phone_var).pack(
            fill="x", padx=4, pady=2
        )
        self.require_cnpj_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(sidebar_scroll, text="Obrigatório ter CNPJ/NIPC", variable=self.require_cnpj_var).pack(
            fill="x", padx=4, pady=2
        )
        self.mx_validate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sidebar_scroll,
            text="🌐 Validar domínio DNS/MX",
            variable=self.mx_validate_var,
        ).pack(fill="x", padx=4, pady=2)

        self.auto_export_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            sidebar_scroll,
            text="📥 Guardar CSV filtrado ao concluir",
            variable=self.auto_export_var,
        ).pack(fill="x", padx=4, pady=2)

        chunk_row = ctk.CTkFrame(sidebar_scroll, fg_color="transparent")
        chunk_row.pack(fill="x", padx=4, pady=(2, 4))
        self.chunk_export_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            chunk_row,
            text="Dividir exportação",
            variable=self.chunk_export_var,
            font=ctk.CTkFont(size=11),
        ).pack(side="left")
        self.chunk_size_var = ctk.StringVar(value=str(CHUNK_SIZE_DEFAULT))
        ctk.CTkEntry(chunk_row, textvariable=self.chunk_size_var, width=56).pack(side="left", padx=(6, 4))
        ctk.CTkLabel(chunk_row, text="linhas/ficheiro", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")

        self.stream_export_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            sidebar_scroll,
            text="💾 Gravar ficheiros enquanto extrai",
            variable=self.stream_export_var,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=4, pady=2)

        self.sqlite_stream_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            sidebar_scroll,
            text="🗄 SQLite em tempo real (volumes grandes)",
            variable=self.sqlite_stream_var,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=4, pady=2)

        self.antibot_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            sidebar_scroll,
            text="🛡 Anti-Bot (Playwright + Cloudflare)",
            variable=self.antibot_var,
        ).pack(fill="x", padx=4, pady=(6, 2))

        privacy = ctk.CTkFrame(sidebar_scroll, fg_color=("gray92", "gray18"), corner_radius=8)
        privacy.pack(fill="x", padx=4, pady=(4, 6))
        ctk.CTkLabel(
            privacy,
            text="🌐 Hide My IP — integrado no software",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(8, 4))
        self.hide_ip_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            privacy,
            text="Ocultar IP (ativado)",
            variable=self.hide_ip_var,
            command=self._on_hide_ip_toggle,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(fill="x", padx=10, pady=(0, 4))
        self.fingerprint_mask_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            privacy,
            text="🎭 Randomizar impressão digital do browser",
            variable=self.fingerprint_mask_var,
            command=self._on_fingerprint_mask_change,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(
            privacy,
            text=(
                "Muda User-Agent, idioma e resolução vistos pelos sites. "
                "Nota: o MAC real da placa NUNCA é enviado à internet."
            ),
            font=ctk.CTkFont(size=9),
            text_color="gray",
            wraplength=250,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(
            privacy,
            text="HUD completo no separador «Extrair».",
            font=ctk.CTkFont(size=9),
            text_color="gray",
            wraplength=250,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkButton(
            privacy,
            text="🔄 Atualizar HUD",
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._refresh_privacy_status_async,
        ).pack(fill="x", padx=10, pady=(0, 6))
        self.advanced_proxy_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            privacy,
            text="Opções avançadas: proxy manual",
            variable=self.advanced_proxy_var,
            command=self._on_advanced_proxy_toggle,
            font=ctk.CTkFont(size=10),
        ).pack(fill="x", padx=10, pady=(0, 2))
        self._advanced_frame = ctk.CTkFrame(privacy, fg_color="transparent")
        self.proxy_url_var = ctk.StringVar(value="")
        self.proxy_entry = ctk.CTkEntry(
            self._advanced_frame,
            textvariable=self.proxy_url_var,
            placeholder_text="socks5://127.0.0.1:1080 (opcional)",
            font=ctk.CTkFont(size=11),
            state="disabled",
        )
        self.proxy_entry.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(
            privacy,
            text="Só use proxy manual se souber o que está a fazer.",
            font=ctk.CTkFont(size=9),
            text_color="gray",
            wraplength=250,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 8))

        paths = ctk.CTkFrame(sidebar_scroll, fg_color="transparent")
        paths.pack(fill="x", padx=4, pady=(4, 8))
        ctk.CTkLabel(paths, text="Pasta de downloads (BR/RFB)", anchor="w").pack(fill="x")
        self.data_dir_var = ctk.StringVar(value=str(DEFAULT_DATA_DIR))
        data_row = ctk.CTkFrame(paths, fg_color="transparent")
        data_row.pack(fill="x", pady=(2, 6))
        ctk.CTkEntry(data_row, textvariable=self.data_dir_var).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(data_row, text="📂", width=36, command=self._browse_data_dir).pack(side="right")

        ctk.CTkLabel(paths, text="Pasta de exportação", anchor="w").pack(fill="x")
        self.export_dir_var = ctk.StringVar(value=str(DEFAULT_EXPORT_DIR))
        export_row = ctk.CTkFrame(paths, fg_color="transparent")
        export_row.pack(fill="x", pady=(2, 0))
        ctk.CTkEntry(export_row, textvariable=self.export_dir_var).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(export_row, text="📂", width=36, command=self._browse_export_dir).pack(side="right")

        ctk.CTkButton(sidebar, text="📖 Abrir Guia", height=32, fg_color="gray35",
                      command=lambda: self.tabview.set("📖 Guia")).grid(row=8, column=0, padx=20, pady=(0, 12), sticky="ew")

        # Main tabs
        self.tabview = ctk.CTkTabview(self, corner_radius=0)
        self.tabview.grid(row=0, column=1, sticky="nsew")
        tab_extract = self.tabview.add("📊 Extrair")
        tab_sources = self.tabview.add("➕ Minhas Fontes")
        tab_guide = self.tabview.add("📖 Guia")

        self._build_extract_tab(tab_extract)
        self._build_sources_tab(tab_sources)
        self._build_guide_tab(tab_guide)

    def _build_extract_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(4, weight=1)

        hud_wrap = ctk.CTkFrame(parent, fg_color=HUD_BG, corner_radius=8, border_width=2, border_color=HUD_BORDER)
        hud_wrap.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        hud_wrap.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hud_wrap,
            text="◉ PRIVACY HUD — RÁDIO DIGITAL",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=HUD_FG,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        self._privacy_hud = ctk.CTkTextbox(
            hud_wrap,
            height=180,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=HUD_BG,
            text_color=HUD_FG,
            border_width=0,
            wrap="none",
            activate_scrollbars=False,
        )
        self._privacy_hud.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 10))
        self._set_hud_display(self._loading_hud_text())

        actions = ctk.CTkFrame(parent, fg_color=("gray92", "gray17"), corner_radius=10)
        actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=2)

        self.start_btn = ctk.CTkButton(
            actions,
            text="▶  INICIAR EXTRAÇÃO",
            height=52,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start_extraction,
        )
        self.start_btn.grid(row=0, column=0, padx=(10, 6), pady=10, sticky="ew")

        self.stop_btn = ctk.CTkButton(
            actions,
            text="⏹  PARAR",
            height=52,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#c0392b",
            hover_color="#962d22",
            command=self._stop_extraction,
            state="disabled",
        )
        self.stop_btn.grid(row=0, column=1, padx=6, pady=10, sticky="ew")

        preview_wrap = ctk.CTkFrame(actions, fg_color="transparent")
        preview_wrap.grid(row=0, column=2, padx=(6, 10), pady=10, sticky="ew")
        preview_wrap.grid_columnconfigure(1, weight=1)
        self.preview_count_var = ctk.StringVar(value="25")
        ctk.CTkEntry(preview_wrap, textvariable=self.preview_count_var, width=48).grid(row=0, column=0, padx=(0, 6))
        self.preview_btn = ctk.CTkButton(
            preview_wrap,
            text="🔍 Pré-visualizar",
            height=52,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1a5276",
            hover_color="#154360",
            command=self._start_preview,
        )
        self.preview_btn.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(
            actions,
            text="Aguarde SYS: READY no HUD acima · Pré-visualizar mostra amostra na tabela sem gravar ficheiros",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
        ).grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))

        stats = ctk.CTkFrame(parent)
        stats.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)
        self.stat_total = self._stat_card(stats, "Registos", "0", 0)
        self.stat_emails = self._stat_card(stats, "E-mails", "0", 1)
        self.stat_country = self._stat_card(stats, "País", "—", 2)
        self.stat_status = self._stat_card(stats, "Estado", "Pronto", 3)

        prog = ctk.CTkFrame(parent, fg_color="transparent")
        prog.grid(row=3, column=0, sticky="ew", padx=12, pady=4)
        prog.grid_columnconfigure(0, weight=1)
        self.progress = ctk.CTkProgressBar(prog, height=14)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.progress.set(0)
        self.status_label = ctk.CTkLabel(prog, text="Configure e clique em Iniciar Extração.", anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew")

        table_frame = ctk.CTkFrame(parent)
        table_frame.grid(row=4, column=0, sticky="nsew", padx=12, pady=6)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        cols = ("id", "empresa", "email", "local", "fonte")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [("id", "NIPC/CNPJ", 120), ("empresa", "Empresa", 240),
                        ("email", "E-mail", 220), ("local", "Local", 120), ("fonte", "Fonte", 140)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w)
        sy = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")

        activity_wrap = ctk.CTkFrame(parent, fg_color=ACTIVITY_BG, corner_radius=8, border_width=1, border_color=HUD_BORDER)
        activity_wrap.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 6))
        activity_wrap.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            activity_wrap,
            text="📋 ATIVIDADE EM TEMPO REAL — o que o software está a fazer agora",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        self._activity_log = ctk.CTkTextbox(
            activity_wrap,
            height=140,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=ACTIVITY_BG,
            text_color=ACTIVITY_FG,
            wrap="word",
            activate_scrollbars=True,
        )
        self._activity_log.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        self._activity_log.insert("1.0", "Pronto. Escolha uma base e clique Pré-visualizar ou INICIAR EXTRAÇÃO.\n")
        self._activity_log.configure(state="disabled")

        exp = ctk.CTkFrame(parent, fg_color="transparent")
        exp.grid(row=6, column=0, sticky="ew", padx=12, pady=(4, 12))
        ctk.CTkButton(exp, text="📥 CSV filtrado", command=self._export_filtered, width=120,
                      fg_color="#1a5276", hover_color="#154360").pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="📂 Guardar na pasta", command=self._export_to_folder, width=130,
                      fg_color="#117a65", hover_color="#0e6251").pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="📝 Emails .txt", command=self._export_emails_txt, width=100,
                      fg_color="#7d6608", hover_color="#5d4c06").pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="💾 SQLite (.db)", command=self._export_sqlite, width=120).pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="📄 CSV completo", command=self._export_csv, width=120).pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="📧 Só emails", command=self._export_emails_only, width=110,
                      fg_color="#1a7a4c", hover_color="#145c38").pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="📨 Marketing", command=self._export_marketing, width=100,
                      fg_color="#6c3483", hover_color="#512664").pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="🗑 Limpar", command=self._clear_results, width=100,
                      fg_color="gray40").pack(side="right")

    def _build_sources_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        ctk.CTkLabel(top, text="As suas bases de dados e sites personalizados",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="➕ Adicionar Fonte", command=self._open_add_source_dialog).pack(side="right")

        quick = ctk.CTkFrame(parent)
        quick.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        ctk.CTkLabel(quick, text="🌐 Novo site — cole o URL e adicione (usa anti-bot automaticamente)",
                     anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x", padx=10, pady=(8, 4))
        qrow = ctk.CTkFrame(quick, fg_color="transparent")
        qrow.pack(fill="x", padx=10, pady=(0, 10))
        self.quick_url_var = ctk.StringVar(value="https://")
        ctk.CTkEntry(qrow, textvariable=self.quick_url_var, placeholder_text="https://site.com/sitemap.xml").pack(
            side="left", fill="x", expand=True, padx=(0, 6)
        )
        ctk.CTkButton(qrow, text="Adicionar e usar", width=120, command=self._quick_add_source).pack(side="right")

        self.sources_list = ctk.CTkScrollableFrame(parent)
        self.sources_list.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        help_frame = ctk.CTkFrame(parent)
        help_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        ctk.CTkLabel(help_frame, text=ADD_SOURCE_HELP, justify="left", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(padx=12, pady=12)

    def _build_guide_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        box = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="Consolas", size=13), wrap="word")
        box.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        box.insert("1.0", GUIDE_TEXT)
        box.configure(state="disabled")

        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        ctk.CTkButton(btns, text="🚀 Iniciar teste rápido (50 empresas)",
                      command=self._quick_start).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="➕ Adicionar fonte personalizada",
                      command=self._open_add_source_dialog).pack(side="left", padx=4)

    def _stat_card(self, parent, label, value, col):
        f = ctk.CTkFrame(parent)
        f.grid(row=0, column=col, padx=4, pady=6, sticky="ew")
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(6, 0))
        lbl = ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=20, weight="bold"))
        lbl.pack(pady=(0, 6))
        return lbl

    def _refresh_custom_sources(self) -> None:
        self._custom_sources = load_custom_sources()
        self._rebuild_source_menu()
        self._rebuild_sources_list()

    def _rebuild_source_menu(self, *, preserve: str | None = None) -> None:
        self._source_map = {}
        labels: list[str] = []

        for country_code in COUNTRY_MENU_ORDER:
            if country_code == "OUTRO":
                continue
            if country_code not in COUNTRIES:
                continue
            flag = COUNTRIES[country_code]["flag"]
            for key, src in COUNTRIES[country_code]["sources"].items():
                label = f"{flag} {src.name}"
                unique = label
                suffix = 2
                while unique in self._source_map:
                    unique = f"{label} ({suffix})"
                    suffix += 1
                labels.append(unique)
                self._source_map[unique] = f"builtin:{country_code}:{key}"

        for cs in self._custom_sources:
            flag = COUNTRIES.get(cs.country, {}).get("flag", "✦")
            label = f"{flag} {CUSTOM_PREFIX}{cs.name}"
            unique = label
            suffix = 2
            while unique in self._source_map:
                unique = f"{label} ({suffix})"
                suffix += 1
            labels.append(unique)
            self._source_map[unique] = f"custom:{cs.id}"

        outro = COUNTRIES.get("OUTRO", {})
        for key, src in outro.get("sources", {}).items():
            label = f"🌍 {src.name}"
            unique = label
            suffix = 2
            while unique in self._source_map:
                unique = f"{label} ({suffix})"
                suffix += 1
            labels.append(unique)
            self._source_map[unique] = f"builtin:OUTRO:{key}"

        labels.append(SPECIAL_SOURCES["__scraper__"])
        self._source_map[SPECIAL_SOURCES["__scraper__"]] = "special:scraper"
        labels.append(SPECIAL_SOURCES["__add__"])
        self._source_map[SPECIAL_SOURCES["__add__"]] = "special:add"

        self.source_menu.configure(values=labels)
        if preserve and preserve in self._source_map:
            self.source_var.set(preserve)
        elif labels:
            preferred = self._default_source_label_for_country(self.country_var.get(), labels)
            self.source_var.set(preferred or labels[0])

    def _default_source_label_for_country(self, country_code: str, labels: list[str]) -> str | None:
        if country_code not in COUNTRIES:
            return None
        for label, mapped in self._source_map.items():
            if mapped.startswith(f"builtin:{country_code}:"):
                return label
        return None

    def _rebuild_sources_list(self) -> None:
        for w in self.sources_list.winfo_children():
            w.destroy()

        if not self._custom_sources:
            ctk.CTkLabel(self.sources_list, text="Nenhuma fonte personalizada.\nClique em '+ Adicionar Fonte' para começar.",
                         text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        for cs in self._custom_sources:
            card = ctk.CTkFrame(self.sources_list)
            card.pack(fill="x", pady=6, padx=4)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=12, pady=10)
            ctk.CTkLabel(info, text=f"✦ {cs.name}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"Tipo: {SOURCE_TYPES.get(cs.source_type, cs.source_type)}", anchor="w", text_color="gray").pack(fill="x")
            ctk.CTkLabel(info, text=f"URL: {cs.url[:70]}{'...' if len(cs.url) > 70 else ''}", anchor="w", text_color="gray").pack(fill="x")

            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.pack(side="right", padx=8, pady=8)
            ctk.CTkButton(btns, text="Usar", width=70, command=lambda s=cs: self._use_custom_source(s)).pack(pady=2)
            ctk.CTkButton(btns, text="🗑", width=40, fg_color="#c0392b",
                          command=lambda sid=cs.id: self._delete_source(sid)).pack(pady=2)

    def _use_custom_source(self, source: CustomSource) -> None:
        flag = COUNTRIES.get(source.country, {}).get("flag", "✦")
        label = f"{flag} {CUSTOM_PREFIX}{source.name}"
        if label not in self._source_map:
            self._rebuild_source_menu()
        if label in self._source_map:
            self.source_var.set(label)
        if source.country and source.country != "OUTRO":
            self.country_var.set(source.country)
            self._on_country_change()
            if label in self._source_map:
                self.source_var.set(label)
        self.tabview.set("📊 Extrair")
        self._set_status(f"Fonte '{source.name}' selecionada. Clique INICIAR EXTRAÇÃO.")

    def _delete_source(self, source_id: str) -> None:
        if messagebox.askyesno(APP_NAME, "Eliminar esta fonte personalizada?"):
            delete_custom_source(source_id)
            self._refresh_custom_sources()

    def _quick_add_source(self) -> None:
        url = self.quick_url_var.get().strip()
        if not url or url == "https://":
            messagebox.showwarning(APP_NAME, "Cole um URL válido (sitemap ou página).")
            return
        stype = "sitemap" if url.endswith(".xml") or "sitemap" in url.lower() else "pagina"
        from urllib.parse import urlparse
        host = urlparse(url).netloc or "site"
        source = CustomSource(
            id="",
            name=f"Site: {host}",
            url=url,
            source_type=stype,
            country="OUTRO",
            auto_discover=True,
            notes="Adicionado via URL rápido — anti-bot ativo",
        )
        add_custom_source(source)
        self._refresh_custom_sources()
        self._use_custom_source(source)
        self.quick_url_var.set("https://")
        messagebox.showinfo(APP_NAME, f"Fonte '{source.name}' adicionada e selecionada.")

    def _open_add_source_dialog(self) -> None:
        AddSourceDialog(self, on_saved=self._refresh_custom_sources)

    def _on_source_selected(self, choice: str) -> None:
        key = self._source_map.get(choice, "")
        if key == "special:add":
            self._open_add_source_dialog()
            self._rebuild_source_menu(preserve=choice if choice != SPECIAL_SOURCES["__add__"] else None)
            return
        if key.startswith("builtin:"):
            parts = key.split(":", 2)
            if len(parts) == 3:
                country_code = parts[1]
                if self.country_var.get() != country_code:
                    self.country_var.set(country_code)
                    self._on_country_change()
                    self.source_var.set(choice)
        country_name = COUNTRIES.get(self.country_var.get(), {}).get("name", self.country_var.get())
        self._set_status(f"Base selecionada ({country_name}). Clique «INICIAR EXTRAÇÃO» ou «Pré-visualizar».")

    def _on_country_change(self, _=None) -> None:
        country = self.country_var.get()
        saved_sector = ""
        if getattr(self, "sector_var", None):
            saved_sector = self.sector_var.get()
        for w in self.filter_frame.winfo_children():
            w.destroy()

        if country == "BR":
            ctk.CTkLabel(self.filter_frame, text="UF", anchor="w").pack(fill="x")
            self.uf_var = ctk.StringVar(value="Todos")
            ctk.CTkOptionMenu(self.filter_frame, variable=self.uf_var, values=BRAZIL_UFS, width=260).pack(fill="x", pady=4)
            self.uf_by_uf_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                self.filter_frame,
                text="Extrair UF por UF (SP, RJ, MG…)",
                variable=self.uf_by_uf_var,
            ).pack(anchor="w")
            self.only_active_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(self.filter_frame, text="Apenas ativas", variable=self.only_active_var).pack(anchor="w")
            self.load_razao_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                self.filter_frame,
                text="Carregar razão social (requer Empresas*.zip)",
                variable=self.load_razao_var,
            ).pack(anchor="w")
            ctk.CTkButton(
                self.filter_frame,
                text="🗑 Limpar ZIPs corrompidos",
                height=28,
                fg_color="gray40",
                command=self._clear_corrupt_rfb_downloads,
            ).pack(anchor="w", pady=(6, 0))
            self.use_local_zips_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                self.filter_frame,
                text="Usar ZIPs já descarregados (pasta acima)",
                variable=self.use_local_zips_var,
            ).pack(anchor="w", pady=(4, 0))
            ctk.CTkLabel(
                self.filter_frame,
                text="Coloque Estabelecimentos0.zip … 9.zip na pasta de downloads",
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                wraplength=250,
            ).pack(fill="x")
        elif country == "PT":
            ctk.CTkLabel(self.filter_frame, text="Distrito (opcional)", anchor="w").pack(fill="x")
            self.distrito_var = ctk.StringVar()
            ctk.CTkEntry(self.filter_frame, textvariable=self.distrito_var, placeholder_text="Ex: Lisboa", width=260).pack(fill="x", pady=4)
        elif country in CATALOG_COUNTRY_CODES:
            meta = COUNTRY_CATALOG_REGISTRY[country]
            ctk.CTkLabel(self.filter_frame, text=f"{meta['region_label']} (opcional)", anchor="w").pack(fill="x")
            self.regiao_var = ctk.StringVar()
            ctk.CTkEntry(
                self.filter_frame,
                textvariable=self.regiao_var,
                placeholder_text=meta.get("region_placeholder", ""),
                width=260,
            ).pack(fill="x", pady=4)
            ctk.CTkLabel(
                self.filter_frame,
                text=meta.get("region_hint", ""),
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                wraplength=250,
            ).pack(fill="x")

        self._build_sector_filter_ui(country, saved_sector)

        if country in COUNTRIES:
            cdata = COUNTRIES[country]
            self.stat_country.configure(text=f"{cdata['flag']} {cdata['name']}")
        else:
            self.stat_country.configure(text=country)

    def _select_source_for_country(self, country_code: str, source_key: str) -> None:
        target = f"builtin:{country_code}:{source_key}"
        label = next((lbl for lbl, key in self._source_map.items() if key == target), None)
        if label:
            self.source_var.set(label)

    def _build_sector_filter_ui(self, country: str, value: str = "") -> None:
        ctk.CTkLabel(
            self.filter_frame,
            text=f"🏭 {get_sector_label(country)}",
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(fill="x", pady=(10, 0))
        self.sector_var = ctk.StringVar(value=value)
        ctk.CTkEntry(
            self.filter_frame,
            textvariable=self.sector_var,
            placeholder_text=get_sector_placeholder(country),
            width=260,
        ).pack(fill="x", pady=4)
        ctk.CTkLabel(
            self.filter_frame,
            text=get_sector_hint(country).split("\n")[0],
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            wraplength=250,
        ).pack(fill="x")
        ctk.CTkLabel(
            self.filter_frame,
            text="Vários códigos: 62, 47, 86 (prefixo ou completo)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
            wraplength=250,
        ).pack(fill="x", pady=(0, 4))

    def _get_sector_filter(self) -> str:
        var = getattr(self, "sector_var", None)
        return var.get().strip() if var else ""

    def _record_passes_sector(self, row: dict) -> bool:
        sector = self._get_sector_filter()
        if not sector:
            return True
        return matches_sector(row.get("cnae", ""), sector)

    def _sector_folder_suffix(self) -> str:
        codes = parse_sector_filters(self._get_sector_filter())
        if not codes:
            return ""
        label = "_".join(codes[:2])
        return f"_setor_{label}"[:32]

    def _quick_start(self) -> None:
        self.country_var.set("PT")
        self._on_country_change()
        self._select_source_for_country("PT", "fiz_portugal")
        self.max_var.set("50")
        self.mode_var.set("limitado")
        self.tabview.set("📊 Extrair")
        self._set_status("Configurado para teste rápido (50 empresas PT). Clique INICIAR EXTRAÇÃO!")

    def _resolve_source(self):
        label = self.source_var.get()
        key = self._source_map.get(label, "")
        country = self.country_var.get()

        if key.startswith("builtin:"):
            parts = key.split(":", 2)
            if len(parts) == 3:
                src_country, sk = parts[1], parts[2]
            else:
                sk = parts[1]
                src_country = country if country in COUNTRIES else "OUTRO"
            if src_country not in COUNTRIES:
                raise ValueError("País da fonte inválido.")
            return src_country, sk, COUNTRIES[src_country]["sources"][sk]
        if key.startswith("custom:"):
            cid = key.split(":", 1)[1]
            for cs in self._custom_sources:
                if cs.id == cid:
                    return cs.country, f"custom:{cid}", CustomSourceAdapter(cs)
        if key == "special:scraper":
            return country, "scraper", WebScraperSource()
        raise ValueError("Selecione uma fonte válida.")

    def _set_status(self, msg: str, progress: float | None = None, *, log: bool | None = None) -> None:
        self.status_label.configure(text=msg)
        should_log = self._extracting if log is None else log
        if msg and should_log:
            self._append_activity(msg, kind="step")
        if progress is not None:
            self.progress.set(min(max(progress, 0.0), 1.0))

    def _on_progress_update(self, value: float, message: str) -> None:
        self.status_label.configure(text=message)
        self._append_activity(message, kind="step")
        self.progress.set(min(max(value, 0.0), 1.0))

    def _append_activity(self, message: str, *, kind: str = "info") -> None:
        if not getattr(self, "_activity_log", None):
            return
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "info": "•",
            "step": "▸",
            "ok": "✓",
            "warn": "!",
            "capture": "→",
            "error": "✗",
        }.get(kind, "•")
        line = f"[{ts}] {prefix} {message}\n"
        self._activity_log.configure(state="normal")
        self._activity_log.insert("end", line)
        line_count = int(self._activity_log.index("end-1c").split(".")[0])
        if line_count > MAX_ACTIVITY_LINES:
            self._activity_log.delete("1.0", f"{line_count - MAX_ACTIVITY_LINES}.0")
        self._activity_log.see("end")
        self._activity_log.configure(state="disabled")

    def _clear_activity_log(self) -> None:
        if not getattr(self, "_activity_log", None):
            return
        self._activity_log.configure(state="normal")
        self._activity_log.delete("1.0", "end")
        self._activity_log.configure(state="disabled")
        self._last_logged_count = 0

    def _log_capture(self, row: dict) -> None:
        empresa = (row.get("razao_social") or row.get("empresa") or "—")[:42]
        email = row.get("email") or "—"
        local = (row.get("municipio") or row.get("uf") or row.get("local") or "")[:24]
        detail = f"{empresa} | {email}"
        if local:
            detail += f" | {local}"
        self._append_activity(detail, kind="capture")

    def _log_extraction_start(self, *, preview: bool) -> None:
        self._clear_activity_log()
        mode = "PRÉ-VISUALIZAÇÃO" if preview else "EXTRAÇÃO COMPLETA"
        self._append_activity(f"Início: {mode}", kind="ok")
        self._append_activity(f"Base: {self.source_var.get()}", kind="info")
        self._append_activity(f"País/filtros: {self.country_var.get()}", kind="info")
        if preview:
            try:
                n = int(self.preview_count_var.get().strip() or "25")
            except ValueError:
                n = 25
            self._append_activity(f"Objetivo: captar até {max(1, min(n, 500))} registos (sem gravar ficheiros)", kind="info")
        else:
            limite = self.max_var.get().strip() or "100"
            modo = self.mode_var.get()
            self._append_activity(f"Modo: {modo} | Limite: {limite}", kind="info")
            if self.stream_export_var.get():
                self._append_activity("Gravação em tempo real: ATIVADA", kind="info")
        if self.antibot_var.get():
            self._append_activity("Anti-Bot: ATIVO", kind="info")
        if self.hide_ip_var.get():
            self._append_activity("Hide My IP: ATIVO", kind="info")
        self._append_activity("A preparar ligação e a começar...", kind="step")

    def _update_stats(self) -> None:
        total = self._stream_total if self._stream_total else len(self.records)
        self.stat_total.configure(text=f"{total:,}")
        emails = self._stream_total if self._stream_total else len({r.get("email") for r in self.records})
        self.stat_emails.configure(text=f"{emails:,}")

    def _refresh_table(self, *, show_all: bool = False) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = self.records if show_all else self.records[-500:]
        for row in rows:
            self.tree.insert("", "end", values=(
                row.get("cnpj", "")[:20], row.get("razao_social", "")[:45],
                row.get("email", ""), row.get("municipio", "")[:20], row.get("fonte", "")[:25],
            ))

    def _loading_hud_text(self) -> str:
        return format_privacy_hud(
            real_ip=None,
            hidden_ip=None,
            hide_ip_enabled=self.hide_ip_var.get(),
            fingerprint_enabled=self.fingerprint_mask_var.get(),
            profile=get_fingerprint_profile() or generate_fingerprint_profile(),
            system_status="CALIBRANDO...",
        )

    def _set_hud_display(self, text: str) -> None:
        self._privacy_hud.configure(state="normal")
        self._privacy_hud.delete("1.0", "end")
        self._privacy_hud.insert("1.0", text)
        self._privacy_hud.configure(state="disabled")

    def _build_hud_text(
        self,
        *,
        real_ip: IpInfo | None = None,
        hidden_ip: IpInfo | None = None,
        system_status: str = "READY",
    ) -> str:
        profile = None
        if self.fingerprint_mask_var.get():
            profile = get_fingerprint_profile() or generate_fingerprint_profile()
        return format_privacy_hud(
            real_ip=real_ip,
            hidden_ip=hidden_ip,
            hide_ip_enabled=self.hide_ip_var.get(),
            fingerprint_enabled=self.fingerprint_mask_var.get(),
            profile=profile,
            system_status=system_status,
        )

    def _apply_privacy_displays(
        self,
        *,
        real_ip: IpInfo | None,
        hidden_ip: IpInfo | None,
        system_status: str = "READY",
    ) -> None:
        self._last_real_ip = real_ip
        self._last_hidden_ip = hidden_ip
        self._hud_ready = real_ip is not None
        text = self._build_hud_text(real_ip=real_ip, hidden_ip=hidden_ip, system_status=system_status)
        self._set_hud_display(text)
        if self._hud_ready:
            self.start_btn.configure(state="normal")
            self.preview_btn.configure(state="normal")

    def _refresh_privacy_status_worker(self) -> None:
        try:
            self.after(0, self._set_hud_display, self._build_hud_text(system_status="SCANNING..."))
            real = lookup_ip(use_active_proxy=False)
            hidden = None
            if self.hide_ip_var.get():
                proxy_url = get_active_proxy()
                if not proxy_url and not self._uses_manual_proxy():
                    proxy_url = get_cached_working_proxy()
                if proxy_url:
                    hidden = lookup_ip(proxy_url=proxy_url)
            self.after(
                0,
                lambda r=real, h=hidden: self._apply_privacy_displays(
                    real_ip=r, hidden_ip=h, system_status="READY"
                ),
            )
        except Exception:
            self.after(0, self._set_hud_display, self._build_hud_text(system_status="ERRO SCAN"))

    def _ensure_hud_before_action(self) -> bool:
        if not self.hide_ip_var.get():
            return True
        if get_active_proxy() or get_cached_working_proxy():
            self._refresh_privacy_status_async()
            return True
        self._set_hud_display(self._build_hud_text(system_status="WARMUP..."))
        url = prewarm_proxy_pool(max_tries=20)
        if url:
            set_active_proxy(url)
        self._refresh_privacy_status_worker()
        return bool(get_active_proxy() or get_cached_working_proxy() or not self.hide_ip_var.get())

    def _refresh_privacy_status_async(self) -> None:
        threading.Thread(target=self._refresh_privacy_status_worker, daemon=True).start()

    def _start_hide_ip_prewarm(self) -> None:
        if self.hide_ip_var.get() and not self._uses_manual_proxy():
            threading.Thread(target=self._prewarm_hide_ip_worker, daemon=True).start()

    def _prewarm_hide_ip_worker(self) -> None:
        self.after(0, self._set_hud_display, self._build_hud_text(system_status="WARMUP..."))
        url = prewarm_proxy_pool(max_tries=18)
        if url:
            set_active_proxy(url)
        self._refresh_privacy_status_worker()

    def _uses_manual_proxy(self) -> bool:
        return self.advanced_proxy_var.get() and bool(self.proxy_url_var.get().strip())

    def _on_hide_ip_toggle(self) -> None:
        if self.hide_ip_var.get():
            self._start_hide_ip_prewarm()
        self._refresh_privacy_status_async()

    def _on_advanced_proxy_toggle(self) -> None:
        if self.advanced_proxy_var.get():
            self._advanced_frame.pack(fill="x", pady=(0, 2))
            self.proxy_entry.configure(state="normal")
            self.hide_ip_var.set(False)
        else:
            self._advanced_frame.pack_forget()
            self.proxy_entry.configure(state="disabled")
            self.hide_ip_var.set(True)
            self._on_hide_ip_toggle()
        self._refresh_privacy_status_async()

    def _on_fingerprint_mask_change(self) -> None:
        if self.fingerprint_mask_var.get():
            set_fingerprint_masking(True, rotate_each_request=True)
        else:
            clear_fingerprint_masking()
        self._refresh_privacy_status_async()

    def _activate_fingerprint_for_extraction(self) -> None:
        if self.fingerprint_mask_var.get():
            set_fingerprint_masking(True, rotate_each_request=True)
        else:
            clear_fingerprint_masking()
        self._refresh_privacy_status_async()

    def _validate_proxy_settings(self) -> bool:
        if not self._uses_manual_proxy():
            return True
        raw = self.proxy_url_var.get().strip()
        if not raw:
            messagebox.showwarning(
                APP_NAME,
                "Ativou proxy manual mas não indicou o endereço.\n\n"
                "Ou desative «Opções avançadas» e use Hide My IP integrado.",
            )
            return False
        if not is_valid_proxy_url(raw):
            messagebox.showwarning(
                APP_NAME,
                "Endereço de proxy inválido.\n\n"
                "Formatos aceites:\n"
                "  http://host:port\n"
                "  socks5://user:pass@host:port",
            )
            return False
        return True

    def _activate_proxy_for_extraction(self) -> bool:
        if self._uses_manual_proxy():
            set_free_proxy_mode(False)
            url = normalize_proxy_url(self.proxy_url_var.get())
            set_active_proxy(url)
            self.after(0, self._set_status, f"🔒 Proxy manual: {mask_proxy_for_display(url)}")
            self.after(0, self._refresh_privacy_status_async)
            return True

        if self.hide_ip_var.get():
            set_free_proxy_mode(True)

            def report(msg: str) -> None:
                self.after(0, self._set_hud_display, self._build_hud_text(system_status=msg[:28]))
                self.after(0, self._set_status, msg)

            url = get_cached_working_proxy()
            if not url:
                url = acquire_working_proxy(max_tries=35, progress_callback=report)
            if not url:
                self.after(
                    0,
                    messagebox.showwarning,
                    APP_NAME,
                    "Hide My IP: não encontrou servidor anónimo agora.\n\n"
                    "Tente novamente em 1 minuto ou desative temporariamente.",
                )
                return False
            set_active_proxy(url)
            self.after(0, self._refresh_privacy_status_async)
            return True

        set_free_proxy_mode(False)
        clear_active_proxy()
        return True

    def _start_preview(self) -> None:
        if self._extracting:
            return
        if not self._validate_proxy_settings():
            return
        try:
            preview_n = int(self.preview_count_var.get().strip() or "25")
        except ValueError:
            preview_n = 25
        preview_n = max(1, min(preview_n, 500))

        self._extracting = True
        self._is_preview = True
        self._stop_requested = False
        self._stream_results = []
        self._stream_total = 0
        self._stream_root = None
        self.records = []
        self._log_extraction_start(preview=True)
        self.start_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.stat_status.configure(text="Pré-visualização...")
        self.tabview.set("📊 Extrair")
        self._refresh_table()
        self._set_status(f"🔍 A captar até {preview_n} registos (sem gravar ficheiros)...", 0.0)
        threading.Thread(target=self._run_extraction, daemon=True).start()

    def _start_extraction(self) -> None:
        if self._extracting:
            return
        if not self._validate_proxy_settings():
            return
        self._extracting = True
        self._is_preview = False
        self._stop_requested = False
        self._log_extraction_start(preview=False)
        self.start_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.stat_status.configure(text="A extrair...")
        self.tabview.set("📊 Extrair")
        threading.Thread(target=self._run_extraction, daemon=True).start()

    def _stop_extraction(self) -> None:
        self._stop_requested = True
        self._append_activity("Pedido de paragem enviado...", kind="warn")

    def _get_uf_targets(self, country_key: str, source_key: str) -> list[str | None]:
        if country_key != "BR" or source_key not in ("receita_federal", "dadosbrasil_api"):
            return [None]
        uf = getattr(self, "uf_var", None)
        current = uf.get() if uf else "Todos"
        if current != "Todos":
            return [current]
        if getattr(self, "uf_by_uf_var", None) and self.uf_by_uf_var.get():
            return list(BRAZIL_UF_CODES)
        return [None]

    def _normalize_record(self, record, country_key: str) -> dict:
        row = record.to_dict() if hasattr(record, "to_dict") else dict(record)
        if country_key == "BR" and row.get("cnpj"):
            row["cnpj"] = format_cnpj(row["cnpj"])
        if not row.get("pais"):
            row["pais"] = country_key
        return row

    def _build_extract_kwargs(
        self,
        source_key: str,
        country_key: str,
        *,
        uf_code: str | None,
        max_records,
        only_email: bool,
        antibot: bool,
        auto: bool,
        progress_callback,
        ) -> dict:
        kwargs: dict = {
            "max_records": max_records,
            "only_with_email": only_email,
            "progress_callback": progress_callback,
            "aggressive_antibot": antibot,
        }
        sector = self._get_sector_filter() or None
        if source_key.startswith("custom:"):
            kwargs["auto_discover"] = auto
            kwargs["max_sitemap_pages"] = None if auto else 1
            kwargs["sector_filter"] = sector
        elif source_key == "scraper":
            url = self._ask_scraper_url()
            if not url:
                raise ValueError("URL não indicado.")
            kwargs.update({"start_url": url, "crawl_same_site": auto, "max_crawl_pages": 30 if auto else 1})
        elif source_key == "receita_federal":
            kwargs.update({
                "partitions": list(range(10)) if auto else [0],
                "uf_filter": uf_code,
                "only_active": getattr(self, "only_active_var", ctk.BooleanVar(value=True)).get(),
                "load_razao_social": getattr(self, "load_razao_var", ctk.BooleanVar(value=False)).get(),
                "use_local_zips_only": getattr(self, "use_local_zips_var", ctk.BooleanVar(value=False)).get(),
                "data_dir": self._get_data_dir(),
                "cnae_filter": sector,
            })
        elif source_key == "dadosbrasil_api":
            kwargs["uf"] = uf_code
            kwargs["cnae"] = sector
        elif source_key == "fiz_portugal":
            dist = getattr(self, "distrito_var", None)
            kwargs.update({
                "auto_discover": True,
                "max_sitemap_pages": None if auto else 1,
                "distrito": dist.get().strip() if dist and dist.get().strip() else None,
                "aggressive_antibot": antibot,
                "sector_filter": sector,
            })
        elif source_key == "sitemap_generico":
            url = self._ask_scraper_url() or FIZ_SITEMAP_INDEX
            kwargs.update({
                "sitemap_url": url,
                "auto_discover": auto,
                "include_all_sitemaps": True,
                "sector_filter": sector,
            })
        elif source_key == "website_scraper":
            url = self._ask_scraper_url()
            if not url:
                raise ValueError("URL não indicado.")
            kwargs.update({
                "start_url": url,
                "crawl_same_site": auto,
                "max_crawl_pages": 50 if auto else 1,
            })
        elif source_key == "empresite_spain":
            regiao = getattr(self, "regiao_var", None)
            kwargs.update({
                "auto_discover": auto,
                "max_sitemap_pages": None if auto else 1,
                "provincia": regiao.get().strip() if regiao and regiao.get().strip() else None,
                "aggressive_antibot": antibot,
            })
        elif self._apply_catalog_kwargs(kwargs, source_key, country_key, auto=auto, sector=sector, antibot=antibot):
            pass
        return kwargs

    def _apply_catalog_kwargs(
        self,
        kwargs: dict,
        source_key: str,
        country_key: str,
        *,
        auto: bool,
        sector: str | None,
        antibot: bool,
    ) -> bool:
        prefix = f"{country_key.lower()}_"
        if not source_key.startswith(prefix):
            return False
        entry = find_catalog_entry(country_key, source_key)
        if not entry:
            return False
        if entry["kind"] == "sitemap":
            kwargs.update({
                "sitemap_url": entry["url"],
                "auto_discover": auto,
                "include_all_sitemaps": True,
                "sector_filter": sector,
                "aggressive_antibot": antibot,
            })
        else:
            kwargs.update({
                "start_url": entry["url"],
                "crawl_same_site": auto,
                "max_crawl_pages": 50 if auto else 1,
                "aggressive_antibot": antibot,
            })
        return True

    def _run_extraction(self) -> None:
        try:
            if not self._activate_proxy_for_extraction():
                self.after(0, self._on_extraction_done_empty)
                return
            self._activate_fingerprint_for_extraction()
            country_key, source_key, source = self._resolve_source()
            preview = self._is_preview
            max_text = self.max_var.get().strip()
            if preview:
                try:
                    max_records = int(self.preview_count_var.get().strip() or "25")
                except ValueError:
                    max_records = 25
                max_records = max(1, min(max_records, 500))
            else:
                max_records = None if max_text == "0" else int(max_text or "100")
            auto = self.mode_var.get() == "automatico"
            only_email = self.only_email_var.get()
            antibot = self.antibot_var.get()
            streaming = self.stream_export_var.get() and not preview
            cb = lambda v, m: self.after(0, self._on_progress_update, v, m)

            uf_targets = self._get_uf_targets(country_key, source_key)
            self._stream_total = 0
            self._stream_results = []
            ui_records: list[dict] = []
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._stream_root = self._get_export_dir() / f"empresas_{country_key.lower()}_{stamp}"

            if streaming:
                for uf_code in uf_targets:
                    if self._stop_requested:
                        break
                    uf_label = f"UF {uf_code}" if uf_code else "todos"
                    if self._get_sector_filter():
                        uf_label += f" | setor {self._get_sector_filter()}"
                    self.after(0, self._set_status, f"A extrair {uf_label}...")
                    suffix = self._sector_folder_suffix()
                    base_name = (f"UF_{uf_code}{suffix}" if uf_code else f"dados{suffix}")
                    try:
                        kwargs = self._build_extract_kwargs(
                            source_key, country_key,
                            uf_code=uf_code,
                            max_records=max_records,
                            only_email=only_email,
                            antibot=antibot,
                            auto=auto,
                            progress_callback=cb,
                        )
                    except ValueError:
                        self.after(0, self._on_extraction_done_empty)
                        return

                    exporter = StreamingExporter(
                        self._stream_root,
                        base_name,
                        selected_fields=self._get_selected_fields(),
                        chunk_size=self._get_chunk_size(),
                        write_csv=True,
                        write_txt=True,
                        use_sqlite=self.sqlite_stream_var.get(),
                        unique_emails=only_email,
                        check_mx=self.mx_validate_var.get(),
                        require_email=self.only_email_var.get(),
                        require_phone=self.require_phone_var.get(),
                        require_cnpj=self.require_cnpj_var.get(),
                        label=uf_label,
                    )

                    for record in source.extract(**kwargs):
                        if self._stop_requested:
                            break
                        row = self._normalize_record(record, country_key)
                        if not self._record_passes_sector(row):
                            continue
                        if exporter.add(row):
                            self._stream_total += 1
                            ui_records.append(row)
                            if len(ui_records) > 500:
                                ui_records.pop(0)
                            n = self._stream_total
                            batch = list(ui_records)
                            refresh = preview or n % 25 == 0 or n <= 5
                            self.after(0, lambda r=row, c=n, b=batch, rt=refresh: self._register_capture(r, c, b, refresh_table=rt))
                            if not preview and self._stream_total % 500 == 0:
                                n = self._stream_total
                                self.after(0, lambda n=n: self._set_status(
                                    f"{n:,} guardados em disco ({uf_label})..."
                                ))

                    self._stream_results.append(exporter.close())

                self.records = ui_records
                self._selected_export_fields = self._get_selected_fields()
                self.after(0, self._on_extraction_done)
                return

            new_records: list[dict] = []
            for uf_code in uf_targets:
                if self._stop_requested:
                    break
                try:
                    kwargs = self._build_extract_kwargs(
                        source_key, country_key,
                        uf_code=uf_code,
                        max_records=max_records,
                        only_email=only_email,
                        antibot=antibot,
                        auto=auto,
                        progress_callback=cb,
                    )
                except ValueError:
                    self.after(0, self._on_extraction_done_empty)
                    return
                for record in source.extract(**kwargs):
                    if self._stop_requested:
                        break
                    row = self._normalize_record(record, country_key)
                    if not self._record_passes_sector(row):
                        continue
                    new_records.append(row)
                    n = len(new_records)
                    batch = list(new_records)
                    refresh = preview or n % 5 == 0 or n <= 3
                    self.after(0, lambda r=row, c=n, b=batch, rt=refresh: self._register_capture(r, c, b, refresh_table=rt))
                    if not preview and len(new_records) % 10 == 0:
                        self.after(0, lambda n=len(new_records): self._set_status(f"{n:,} registos capturados..."))

            cleaned = filter_valid_email_records(new_records)
            if self.mx_validate_var.get():
                mx_cb = lambda v, m: self.after(0, self._on_progress_update, v, m)
                cleaned, _ = filter_records_with_mx(cleaned, check_mx=True, progress_callback=mx_cb)
            cleaned = filter_records_by_requirements(
                cleaned,
                require_email=self.only_email_var.get(),
                require_phone=self.require_phone_var.get(),
                require_cnpj=self.require_cnpj_var.get(),
            )
            self.records = dedupe_by_email(cleaned) if only_email else dedupe_records(cleaned)
            self._selected_export_fields = self._get_selected_fields()
            self.after(0, self._on_extraction_done)
        except Exception as exc:
            self.after(0, self._on_extraction_error, str(exc))
        finally:
            clear_active_proxy()
            clear_free_proxy_mode()
            clear_free_proxy_cache()
            clear_fingerprint_masking()

    def _ask_scraper_url(self) -> str | None:
        result: list[str | None] = [None]
        evt = threading.Event()

        def ask():
            from tkinter import simpledialog
            result[0] = simpledialog.askstring(
                APP_NAME,
                "Cole o URL do site ou página a extrair:\n\n"
                "Exemplos:\n"
                "  https://site.com/sitemap.xml\n"
                "  https://site.com/empresa/123\n"
                "  https://site.com/contactos",
                parent=self,
            )
            evt.set()

        self.after(0, ask)
        evt.wait(timeout=120)
        return result[0]

    def _register_capture(self, row: dict, count: int, batch: list[dict], *, refresh_table: bool) -> None:
        self._log_capture(row)
        self.stat_total.configure(text=f"{count:,}")
        emails = len({r.get("email") for r in batch if r.get("email")})
        self.stat_emails.configure(text=f"{emails:,}")
        self.stat_status.configure(text=f"A captar… ({count:,})")
        if refresh_table:
            self.records = batch
            self._refresh_table(show_all=self._is_preview)

    def _update_live_table(self, rows: list[dict], count: int) -> None:
        self.records = rows
        self._refresh_table(show_all=self._is_preview)
        self.stat_total.configure(text=f"{count:,}")
        emails = len({r.get("email") for r in rows if r.get("email")})
        self.stat_emails.configure(text=f"{emails:,}")
        if rows:
            self.stat_status.configure(text=f"A captar… ({count:,})")

    def _on_extraction_done_empty(self) -> None:
        self._extracting = False
        self._is_preview = False
        self.start_btn.configure(state="normal")
        self.preview_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _on_extraction_done(self) -> None:
        was_preview = self._is_preview
        self._extracting = False
        self._is_preview = False
        self.start_btn.configure(state="normal")
        self.preview_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._update_stats()
        self._refresh_table(show_all=was_preview)
        if was_preview:
            self.stat_status.configure(text="Pré-visualização")
            self.progress.set(1.0)
            msg = f"Pré-visualização: {len(self.records):,} registos na tabela"
            self._append_activity(msg, kind="ok")
            self._set_status(msg, 1.0)
            if self.records:
                messagebox.showinfo(
                    APP_NAME,
                    f"{msg}\n\nRevise os emails no ecrã (separador «Extrair»).\n"
                    "Se estiver OK, clique «▶ Iniciar Extração» para gravar ficheiros.",
                )
            else:
                messagebox.showwarning(
                    APP_NAME,
                    "Pré-visualização concluída sem resultados.\n\n"
                    "Tente outra fonte, active Anti-Bot, ou aumente o limite da amostra.",
                )
            return

        self.stat_status.configure(text="Concluído")
        self.progress.set(1.0)
        msg = f"Extração concluída: {self._stream_total or len(self.records):,} registos"
        self._append_activity(msg, kind="ok")
        if self._stream_root:
            self._append_activity(f"Ficheiros em: {self._stream_root}", kind="info")
        self._set_status(msg, 1.0)

        if self._stream_results:
            summaries = [result.summary for result in self._stream_results]
            root = self._stream_root or self._get_export_dir()
            messagebox.showinfo(
                APP_NAME,
                f"{msg}\n\nGuardado em tempo real em:\n{root}\n\n" + "\n---\n".join(summaries[:3])
                + (f"\n\n... e mais {len(summaries) - 3} UF(s)" if len(summaries) > 3 else ""),
            )
            return

        saved_path = None
        saved_summary = None
        if self.records and self.auto_export_var.get():
            saved_path, saved_summary = self._export_to_folder(silent=True)
        if self.records:
            if saved_path:
                messagebox.showinfo(APP_NAME, f"{msg}\n\n{saved_summary or saved_path}")
            else:
                messagebox.showinfo(APP_NAME, msg)

    def _on_extraction_error(self, error: str) -> None:
        self._extracting = False
        self._is_preview = False
        self.start_btn.configure(state="normal")
        self.preview_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.stat_status.configure(text="Erro")
        self._append_activity(f"ERRO: {error}", kind="error")
        messagebox.showerror(APP_NAME, f"Erro:\n{error}")

    def _clear_results(self) -> None:
        self.records = []
        self._stream_total = 0
        self._stream_results = []
        self._stream_root = None
        self._refresh_table()
        self._update_stats()
        self.progress.set(0)

    def _build_field_selector(self) -> None:
        for widget in self.fields_scroll.winfo_children():
            widget.destroy()
        self.field_vars.clear()
        for key, label, default_on in AVAILABLE_FIELDS:
            var = ctk.BooleanVar(value=default_on)
            self.field_vars[key] = var
            ctk.CTkCheckBox(
                self.fields_scroll,
                text=label,
                variable=var,
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", pady=1)

    def _get_selected_fields(self) -> list[str]:
        selected = [key for key, var in self.field_vars.items() if var.get()]
        return selected or list(DEFAULT_FIELD_KEYS)

    def _get_data_dir(self) -> str:
        path = Path(self.data_dir_var.get().strip() or DEFAULT_DATA_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def _get_export_dir(self) -> Path:
        path = Path(self.export_dir_var.get().strip() or DEFAULT_EXPORT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _browse_data_dir(self) -> None:
        folder = filedialog.askdirectory(
            title="Escolher pasta para downloads (ZIPs Receita Federal)",
            initialdir=self._get_data_dir(),
        )
        if folder:
            self.data_dir_var.set(folder)

    def _browse_export_dir(self) -> None:
        folder = filedialog.askdirectory(
            title="Escolher pasta de exportação",
            initialdir=str(self._get_export_dir()),
        )
        if folder:
            self.export_dir_var.set(folder)

    def _clear_corrupt_rfb_downloads(self) -> None:
        data_dir = Path(self._get_data_dir())
        removed = 0
        for pattern in ("Empresas*.zip", "Estabelecimentos*.zip", "*.zip.part"):
            for path in data_dir.glob(pattern):
                if path.suffix == ".part" or not ReceitaFederalSource.is_valid_zip_file(path):
                    try:
                        path.unlink()
                        removed += 1
                    except OSError:
                        pass
        messagebox.showinfo(
            APP_NAME,
            f"Removidos {removed} ficheiro(s) corrompido(s) ou incompleto(s).\n\nPasta: {data_dir}",
        )

    def _default_export_path(self, extension: str) -> str:
        export_dir = self._get_export_dir()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        country = self.country_var.get().lower()
        return str(export_dir / f"empresas_{country}_{stamp}.{extension}")

    def _export_base_name(self, suffix: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        country = self.country_var.get().lower()
        return f"empresas_{country}_{stamp}_{suffix}"

    def _get_chunk_size(self) -> int:
        try:
            size = int(self.chunk_size_var.get().strip() or str(CHUNK_SIZE_DEFAULT))
        except ValueError:
            size = CHUNK_SIZE_DEFAULT
        return max(100, min(size, 1_000_000))

    def _use_chunk_export(self) -> bool:
        return self.chunk_export_var.get()

    def _format_chunk_summary(self, result: ChunkExportResult) -> str:
        return (
            f"{result.total_rows:,} linhas em {len(result.files)} ficheiro(s)\n"
            f"({result.chunk_size:,} linhas por ficheiro)\n\n"
            f"Pasta:\n{result.folder}"
        )

    def _export_to_folder(self, *, silent: bool = False) -> tuple[str | None, str | None]:
        if not self.records:
            if not silent:
                messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return None, None

        fields = self._get_selected_fields()
        export_dir = self._get_export_dir()

        if self._use_chunk_export():
            result = export_filtered_csv_chunked(
                self.records,
                export_dir,
                base_name=self._export_base_name("filtrado"),
                selected_fields=fields,
                unique_emails=True,
                chunk_size=self._get_chunk_size(),
            )
            summary = self._format_chunk_summary(result)
            if not silent:
                messagebox.showinfo(APP_NAME, f"Exportação dividida concluída!\n\n{summary}")
            return str(result.folder), summary

        path = export_dir / (Path(self._default_export_path("csv")).stem + "_filtrado.csv")
        export_filtered_csv(self.records, path, selected_fields=fields, unique_emails=True)
        summary = f"CSV filtrado guardado:\n{path}\n\nColunas: {', '.join(fields)}"
        if not silent:
            messagebox.showinfo(APP_NAME, summary)
        return str(path), summary

    def _export_filtered(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return
        fields = self._get_selected_fields()

        if self._use_chunk_export():
            result = export_filtered_csv_chunked(
                self.records,
                self._get_export_dir(),
                base_name=self._export_base_name("filtrado"),
                selected_fields=fields,
                unique_emails=True,
                chunk_size=self._get_chunk_size(),
            )
            messagebox.showinfo(APP_NAME, f"Exportação dividida concluída!\n\n{self._format_chunk_summary(result)}")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(self._get_export_dir()),
            initialfile=Path(self._default_export_path("csv")).with_suffix("").name + "_filtrado.csv",
        )
        if path:
            export_filtered_csv(self.records, path, selected_fields=fields, unique_emails=True)
            messagebox.showinfo(
                APP_NAME,
                f"CSV exportado com {len(fields)} colunas:\n"
                f"{', '.join(fields)}\n\n{path}",
            )

    def _export_emails_only(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return

        if self._use_chunk_export():
            result = export_emails_only_csv_chunked(
                self.records,
                self._get_export_dir(),
                base_name=self._export_base_name("emails"),
                unique_emails=True,
                chunk_size=self._get_chunk_size(),
            )
            messagebox.showinfo(
                APP_NAME,
                f"Lista de emails exportada em partes!\n\n{self._format_chunk_summary(result)}\n\n"
                "Colunas: email, empresa, cnpj, uf, municipio",
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV emails", "*.csv")],
            initialdir=str(self._get_export_dir()),
            initialfile=Path(self._default_export_path("csv")).with_suffix("").name + "_emails.csv",
        )
        if path:
            export_emails_only_csv(self.records, path, unique_emails=True)
            count = len({r.get("email") for r in self.records if r.get("email")})
            messagebox.showinfo(
                APP_NAME,
                f"Lista limpa exportada!\n\n{count:,} e-mails únicos validados\n\n{path}\n\n"
                "Abra no Excel — colunas: email, empresa, cnpj, uf, municipio",
            )

    def _export_emails_txt(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return

        result = export_emails_txt_chunked(
            self.records,
            self._get_export_dir(),
            base_name=self._export_base_name("emails_txt"),
            unique_emails=True,
            chunk_size=self._get_chunk_size(),
        )
        messagebox.showinfo(
            APP_NAME,
            f"Emails exportados em ficheiros .txt (1 email por linha)!\n\n"
            f"{self._format_chunk_summary(result)}",
        )

    def _export_marketing(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return
        messagebox.showinfo(
            APP_NAME,
            "Formato para Mailchimp, Brevo, Sendinblue, etc.\n\n"
            "IMPORTANTE (Lei brasileira LGPD / Marco Civil):\n"
            "• Envio em massa sem consentimento pode ser ilegal\n"
            "• Use apenas contactos que autorizaram receber e-mails\n"
            "• Inclua sempre link de cancelar subscrição (opt-out)",
        )
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV marketing", "*.csv")],
            initialdir=str(self._get_export_dir()),
            initialfile=Path(self._default_export_path("csv")).with_suffix("").name + "_marketing.csv",
        )
        if path:
            export_emails_for_marketing_csv(self.records, path)
            messagebox.showinfo(APP_NAME, f"Ficheiro para campanhas guardado:\n{path}")

    def _export_sqlite(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite", "*.db")],
            initialdir=str(self._get_export_dir()),
            initialfile=Path(self._default_export_path("db")).name,
        )
        if path:
            export_sqlite(self.records, path)
            messagebox.showinfo(APP_NAME, f"Guardado:\n{path}")

    def _export_csv(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(self._get_export_dir()),
            initialfile=Path(self._default_export_path("csv")).name,
        )
        if path:
            export_csv(self.records, path, selected_fields=self._get_selected_fields())
            messagebox.showinfo(APP_NAME, f"Guardado:\n{path}")


def main() -> None:
    CompanyEmailApp().mainloop()


if __name__ == "__main__":
    main()
