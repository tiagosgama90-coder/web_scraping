#!/usr/bin/env python3
"""Aplicação desktop nativa — Company Email Extractor v2.4."""

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
    export_csv,
    export_emails_for_marketing_csv,
    export_emails_only_csv,
    export_filtered_csv,
    export_sqlite,
)
from cnpj_extractor.email_validator import filter_records_with_mx
from cnpj_extractor.field_filters import (
    AVAILABLE_FIELDS,
    DEFAULT_FIELD_KEYS,
    filter_records_by_requirements,
)
from cnpj_extractor.gui_text import ADD_SOURCE_HELP, GUIDE_TEXT
from cnpj_extractor.sources import COUNTRIES
from cnpj_extractor.sources.custom_adapter import CustomSourceAdapter
from cnpj_extractor.sources.fiz_portugal import FIZ_SITEMAP_INDEX
from cnpj_extractor.sources.receita_federal import ReceitaFederalSource
from cnpj_extractor.sources.sitemap_generic import GenericSitemapSource
from cnpj_extractor.sources.website_scraper import WebScraperSource
from cnpj_extractor.utils import dedupe_by_email, dedupe_records, filter_valid_email_records, format_cnpj

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_NAME = "Company Email Extractor"
APP_VERSION = "2.4.0"
DEFAULT_BASE_DIR = Path.home() / "Documents" / "CompanyEmailExtractor"
DEFAULT_DATA_DIR = DEFAULT_BASE_DIR / "downloads"
DEFAULT_EXPORT_DIR = DEFAULT_BASE_DIR / "export"
BUILTIN_PREFIX = "★ "
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
        ctk.CTkOptionMenu(form, variable=self.country_var, values=["PT", "BR", "OUTRO"]).pack(fill="x", pady=4)

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
        self.minsize(1000, 640)

        self.records: list[dict] = []
        self._extracting = False
        self._stop_requested = False
        self._custom_sources: list[CustomSource] = []
        self._source_map: dict[str, str] = {}
        self._selected_export_fields: list[str] = list(DEFAULT_FIELD_KEYS)

        self._build_ui()
        self._refresh_custom_sources()
        self._on_country_change()
        self._show_welcome_if_first_run()

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
        sidebar.grid_rowconfigure(16, weight=1)

        ctk.CTkLabel(sidebar, text="📧 Email Extractor", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20, 2), sticky="w"
        )
        ctk.CTkLabel(sidebar, text="Qualquer site • BR • PT", font=ctk.CTkFont(size=12), text_color="gray").grid(
            row=1, column=0, padx=20, pady=(0, 12), sticky="w"
        )

        ctk.CTkLabel(sidebar, text="País", anchor="w").grid(row=2, column=0, padx=20, sticky="ew")
        self.country_var = ctk.StringVar(value="PT")
        ctk.CTkOptionMenu(sidebar, variable=self.country_var, values=["PT", "BR", "OUTRO"],
                          command=self._on_country_change, width=260).grid(row=3, column=0, padx=20, pady=(4, 10))

        ctk.CTkLabel(sidebar, text="Fonte de dados", anchor="w").grid(row=4, column=0, padx=20, sticky="ew")
        self.source_var = ctk.StringVar(value="")
        self.source_menu = ctk.CTkOptionMenu(sidebar, variable=self.source_var, width=260,
                                             command=self._on_source_selected)
        self.source_menu.grid(row=5, column=0, padx=20, pady=(4, 10))

        ctk.CTkLabel(sidebar, text="Modo", anchor="w").grid(row=6, column=0, padx=20, sticky="ew")
        self.mode_var = ctk.StringVar(value="limitado")
        ctk.CTkOptionMenu(sidebar, variable=self.mode_var,
                          values=["limitado", "automatico"], width=260).grid(row=7, column=0, padx=20, pady=(4, 10))

        ctk.CTkLabel(sidebar, text="Limite (0 = sem limite)", anchor="w").grid(row=8, column=0, padx=20, sticky="ew")
        self.max_var = ctk.StringVar(value="100")
        ctk.CTkEntry(sidebar, textvariable=self.max_var, width=260).grid(row=9, column=0, padx=20, pady=(4, 10))

        self.filter_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.filter_frame.grid(row=10, column=0, padx=20, sticky="ew")

        self.fields_scroll = ctk.CTkScrollableFrame(sidebar, height=110, label_text="Campos a exportar")
        self.fields_scroll.grid(row=11, column=0, padx=20, pady=(4, 4), sticky="ew")
        self.field_vars: dict[str, ctk.BooleanVar] = {}
        self._build_field_selector()

        self.only_email_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sidebar, text="Obrigatório ter e-mail", variable=self.only_email_var).grid(
            row=12, column=0, padx=20, pady=2, sticky="w"
        )
        self.require_phone_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(sidebar, text="Obrigatório ter telefone", variable=self.require_phone_var).grid(
            row=13, column=0, padx=20, pady=2, sticky="w"
        )
        self.mx_validate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sidebar,
            text="🌐 Validar domínio DNS/MX",
            variable=self.mx_validate_var,
        ).grid(row=14, column=0, padx=20, pady=2, sticky="w")

        self.antibot_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            sidebar,
            text="🛡 Anti-Bot (Playwright + Cloudflare)",
            variable=self.antibot_var,
        ).grid(row=15, column=0, padx=20, pady=6, sticky="w")

        paths = ctk.CTkFrame(sidebar, fg_color="transparent")
        paths.grid(row=16, column=0, padx=20, sticky="ew")
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

        self.start_btn = ctk.CTkButton(sidebar, text="▶  Iniciar Extração", height=44,
                                       font=ctk.CTkFont(size=15, weight="bold"),
                                       command=self._start_extraction)
        self.start_btn.grid(row=17, column=0, padx=20, pady=(10, 4), sticky="ew")

        self.stop_btn = ctk.CTkButton(sidebar, text="⏹  Parar", height=36, fg_color="#c0392b",
                                     hover_color="#962d22", command=self._stop_extraction, state="disabled")
        self.stop_btn.grid(row=18, column=0, padx=20, pady=(4, 12), sticky="ew")

        ctk.CTkButton(sidebar, text="📖 Abrir Guia", height=32, fg_color="gray35",
                      command=lambda: self.tabview.set("📖 Guia")).grid(row=19, column=0, padx=20, pady=(0, 16), sticky="ew")

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
        parent.grid_rowconfigure(2, weight=1)

        stats = ctk.CTkFrame(parent)
        stats.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)
        self.stat_total = self._stat_card(stats, "Registos", "0", 0)
        self.stat_emails = self._stat_card(stats, "E-mails", "0", 1)
        self.stat_country = self._stat_card(stats, "País", "—", 2)
        self.stat_status = self._stat_card(stats, "Estado", "Pronto", 3)

        prog = ctk.CTkFrame(parent, fg_color="transparent")
        prog.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        prog.grid_columnconfigure(0, weight=1)
        self.progress = ctk.CTkProgressBar(prog, height=14)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.progress.set(0)
        self.status_label = ctk.CTkLabel(prog, text="Configure e clique em Iniciar Extração.", anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew")

        table_frame = ctk.CTkFrame(parent)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=6)
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

        exp = ctk.CTkFrame(parent, fg_color="transparent")
        exp.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 12))
        ctk.CTkButton(exp, text="📥 CSV filtrado", command=self._export_filtered, width=120,
                      fg_color="#1a5276", hover_color="#154360").pack(side="left", padx=(0, 6))
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

    def _rebuild_source_menu(self) -> None:
        self._source_map = {}
        labels: list[str] = []

        country = self.country_var.get()
        if country in COUNTRIES:
            for key, src in COUNTRIES[country]["sources"].items():
                label = f"{BUILTIN_PREFIX}{src.name}"
                labels.append(label)
                self._source_map[label] = f"builtin:{key}"

        for cs in self._custom_sources:
            if country != "OUTRO" and cs.country not in (country, "OUTRO"):
                continue
            label = f"{CUSTOM_PREFIX}{cs.name}"
            labels.append(label)
            self._source_map[label] = f"custom:{cs.id}"

        labels.append(SPECIAL_SOURCES["__scraper__"])
        self._source_map[SPECIAL_SOURCES["__scraper__"]] = "special:scraper"
        labels.append(SPECIAL_SOURCES["__add__"])
        self._source_map[SPECIAL_SOURCES["__add__"]] = "special:add"

        self.source_menu.configure(values=labels)
        if labels:
            self.source_var.set(labels[0])

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
        label = f"{CUSTOM_PREFIX}{source.name}"
        if label in self._source_map:
            self.source_var.set(label)
        self.country_var.set(source.country if source.country != "OUTRO" else "OUTRO")
        self.tabview.set("📊 Extrair")
        self._set_status(f"Fonte '{source.name}' selecionada. Clique em Iniciar Extração.")

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
            self._rebuild_source_menu()

    def _on_country_change(self, _=None) -> None:
        country = self.country_var.get()
        for w in self.filter_frame.winfo_children():
            w.destroy()

        if country == "BR":
            ctk.CTkLabel(self.filter_frame, text="UF", anchor="w").pack(fill="x")
            self.uf_var = ctk.StringVar(value="Todos")
            ctk.CTkOptionMenu(self.filter_frame, variable=self.uf_var, values=BRAZIL_UFS, width=260).pack(fill="x", pady=4)
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

        flags = {"PT": "🇵🇹 Portugal", "BR": "🇧🇷 Brasil", "OUTRO": "🌍 Outro"}
        self.stat_country.configure(text=flags.get(country, country))
        self._rebuild_source_menu()

    def _quick_start(self) -> None:
        self.country_var.set("PT")
        self._on_country_change()
        self.max_var.set("50")
        self.mode_var.set("limitado")
        self.tabview.set("📊 Extrair")
        self._set_status("Configurado para teste rápido (50 empresas PT). Clique em Iniciar!")

    def _resolve_source(self):
        label = self.source_var.get()
        key = self._source_map.get(label, "")
        country = self.country_var.get()

        if key.startswith("builtin:"):
            sk = key.split(":", 1)[1]
            src_country = country if country in COUNTRIES else "OUTRO"
            return country, sk, COUNTRIES[src_country]["sources"][sk]
        if key.startswith("custom:"):
            cid = key.split(":", 1)[1]
            for cs in self._custom_sources:
                if cs.id == cid:
                    return cs.country, f"custom:{cid}", CustomSourceAdapter(cs)
        if key == "special:scraper":
            return country, "scraper", WebScraperSource()
        raise ValueError("Selecione uma fonte válida.")

    def _set_status(self, msg: str, progress: float | None = None) -> None:
        self.status_label.configure(text=msg)
        if progress is not None:
            self.progress.set(min(max(progress, 0.0), 1.0))

    def _update_stats(self) -> None:
        self.stat_total.configure(text=str(len(self.records)))
        self.stat_emails.configure(text=str(len({r.get("email") for r in self.records})))

    def _refresh_table(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self.records[-500:]:
            self.tree.insert("", "end", values=(
                row.get("cnpj", "")[:20], row.get("razao_social", "")[:45],
                row.get("email", ""), row.get("municipio", "")[:20], row.get("fonte", "")[:25],
            ))

    def _start_extraction(self) -> None:
        if self._extracting:
            return
        self._extracting = True
        self._stop_requested = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.stat_status.configure(text="A extrair...")
        self.tabview.set("📊 Extrair")
        threading.Thread(target=self._run_extraction, daemon=True).start()

    def _stop_extraction(self) -> None:
        self._stop_requested = True

    def _run_extraction(self) -> None:
        try:
            country_key, source_key, source = self._resolve_source()
            max_text = self.max_var.get().strip()
            max_records = None if max_text == "0" else int(max_text or "100")
            auto = self.mode_var.get() == "automatico"
            only_email = self.only_email_var.get()
            antibot = self.antibot_var.get()
            cb = lambda v, m: self.after(0, self._set_status, m, v)

            kwargs: dict = {
                "max_records": max_records,
                "only_with_email": only_email,
                "progress_callback": cb,
                "aggressive_antibot": antibot,
            }
            new_records: list[dict] = []

            if source_key.startswith("custom:"):
                kwargs["auto_discover"] = auto
                kwargs["max_sitemap_pages"] = None if auto else 1
            elif source_key == "scraper":
                url = self._ask_scraper_url()
                if not url:
                    self.after(0, self._on_extraction_done_empty)
                    return
                kwargs.update({"start_url": url, "crawl_same_site": auto, "max_crawl_pages": 30 if auto else 1})
            elif source_key == "receita_federal":
                uf = getattr(self, "uf_var", None)
                kwargs.update({
                    "partitions": list(range(10)) if auto else [0],
                    "uf_filter": None if not uf or uf.get() == "Todos" else uf.get(),
                    "only_active": getattr(self, "only_active_var", ctk.BooleanVar(value=True)).get(),
                    "load_razao_social": getattr(self, "load_razao_var", ctk.BooleanVar(value=False)).get(),
                    "use_local_zips_only": getattr(self, "use_local_zips_var", ctk.BooleanVar(value=False)).get(),
                    "data_dir": self._get_data_dir(),
                })
            elif source_key == "dadosbrasil_api":
                uf = getattr(self, "uf_var", None)
                kwargs["uf"] = None if not uf or uf.get() == "Todos" else uf.get()
            elif source_key == "fiz_portugal":
                dist = getattr(self, "distrito_var", None)
                kwargs.update({"auto_discover": True, "max_sitemap_pages": None if auto else 1,
                               "distrito": dist.get().strip() if dist and dist.get().strip() else None,
                               "aggressive_antibot": antibot})
            elif source_key == "sitemap_generico":
                url = self._ask_scraper_url() or FIZ_SITEMAP_INDEX
                kwargs.update({
                    "sitemap_url": url,
                    "auto_discover": auto,
                    "include_all_sitemaps": True,
                })
            elif source_key == "website_scraper":
                url = self._ask_scraper_url()
                if not url:
                    self.after(0, self._on_extraction_done_empty)
                    return
                kwargs.update({
                    "start_url": url,
                    "crawl_same_site": auto,
                    "max_crawl_pages": 50 if auto else 1,
                })

            for record in source.extract(**kwargs):
                if self._stop_requested:
                    break
                row = record.to_dict()
                if country_key == "BR" and row.get("cnpj"):
                    row["cnpj"] = format_cnpj(row["cnpj"])
                if not row.get("pais"):
                    row["pais"] = country_key
                new_records.append(row)
                if len(new_records) % 10 == 0:
                    self.after(0, lambda n=len(new_records): self._set_status(f"{n:,} registos..."))

            cleaned = filter_valid_email_records(new_records)
            if self.mx_validate_var.get():
                mx_cb = lambda v, m: self.after(0, self._set_status, m, v)
                cleaned, _ = filter_records_with_mx(cleaned, check_mx=True, progress_callback=mx_cb)
            cleaned = filter_records_by_requirements(
                cleaned,
                require_email=self.only_email_var.get(),
                require_phone=self.require_phone_var.get(),
            )
            self.records = dedupe_by_email(cleaned) if only_email else dedupe_records(cleaned)
            self._selected_export_fields = self._get_selected_fields()
            self.after(0, self._on_extraction_done)
        except Exception as exc:
            self.after(0, self._on_extraction_error, str(exc))

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

    def _on_extraction_done_empty(self) -> None:
        self._extracting = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _on_extraction_done(self) -> None:
        self._extracting = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._update_stats()
        self._refresh_table()
        self.stat_status.configure(text="Concluído")
        self.progress.set(1.0)
        msg = f"Extração concluída: {len(self.records):,} registos"
        self._set_status(msg, 1.0)
        if self.records:
            messagebox.showinfo(APP_NAME, msg)

    def _on_extraction_error(self, error: str) -> None:
        self._extracting = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.stat_status.configure(text="Erro")
        messagebox.showerror(APP_NAME, f"Erro:\n{error}")

    def _clear_results(self) -> None:
        self.records = []
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

    def _export_filtered(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Sem dados para exportar.")
            return
        fields = self._get_selected_fields()
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
