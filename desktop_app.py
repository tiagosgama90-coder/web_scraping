#!/usr/bin/env python3
"""Aplicação desktop nativa Windows — Company Email Extractor."""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from cnpj_extractor.database import export_csv, export_sqlite
from cnpj_extractor.sources import COUNTRIES
from cnpj_extractor.sources.fiz_portugal import FIZ_SITEMAP_INDEX
from cnpj_extractor.utils import dedupe_records, format_cnpj, parse_cnpj_list

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_NAME = "Company Email Extractor"
APP_VERSION = "2.0.0"

BRAZIL_UFS = [
    "Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS",
    "RO", "RR", "SC", "SP", "SE", "TO",
]


class CompanyEmailApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1180x720")
        self.minsize(960, 600)

        self.records: list[dict] = []
        self._extracting = False
        self._stop_requested = False

        self._build_ui()
        self._on_country_change()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(12, weight=1)

        ctk.CTkLabel(
            sidebar, text="📧 Email Extractor", font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")

        ctk.CTkLabel(
            sidebar, text="Brasil + Portugal", font=ctk.CTkFont(size=13), text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        ctk.CTkLabel(sidebar, text="País", anchor="w").grid(row=2, column=0, padx=20, pady=(4, 0), sticky="ew")
        self.country_var = ctk.StringVar(value="PT")
        self.country_menu = ctk.CTkOptionMenu(
            sidebar,
            variable=self.country_var,
            values=list(COUNTRIES.keys()),
            command=self._on_country_change,
            width=260,
        )
        self.country_menu.grid(row=3, column=0, padx=20, pady=(4, 12))

        ctk.CTkLabel(sidebar, text="Fonte de dados", anchor="w").grid(row=4, column=0, padx=20, pady=(4, 0), sticky="ew")
        self.source_var = ctk.StringVar(value="fiz_portugal")
        self.source_menu = ctk.CTkOptionMenu(sidebar, variable=self.source_var, width=260)
        self.source_menu.grid(row=5, column=0, padx=20, pady=(4, 12))

        ctk.CTkLabel(sidebar, text="Modo", anchor="w").grid(row=6, column=0, padx=20, pady=(4, 0), sticky="ew")
        self.mode_var = ctk.StringVar(value="limitado")
        self.mode_menu = ctk.CTkOptionMenu(
            sidebar,
            variable=self.mode_var,
            values=["limitado", "automatico"],
            width=260,
        )
        self.mode_menu.grid(row=7, column=0, padx=20, pady=(4, 12))

        ctk.CTkLabel(sidebar, text="Limite (0 = sem limite)", anchor="w").grid(
            row=8, column=0, padx=20, pady=(4, 0), sticky="ew"
        )
        self.max_var = ctk.StringVar(value="100")
        self.max_entry = ctk.CTkEntry(sidebar, textvariable=self.max_var, width=260)
        self.max_entry.grid(row=9, column=0, padx=20, pady=(4, 12))

        self.filter_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.filter_frame.grid(row=10, column=0, padx=20, pady=4, sticky="ew")

        self.only_email_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            sidebar, text="Apenas com e-mail válido", variable=self.only_email_var
        ).grid(row=11, column=0, padx=20, pady=8, sticky="w")

        self.start_btn = ctk.CTkButton(
            sidebar,
            text="▶  Iniciar Extração",
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_extraction,
        )
        self.start_btn.grid(row=13, column=0, padx=20, pady=(8, 4), sticky="ew")

        self.stop_btn = ctk.CTkButton(
            sidebar,
            text="⏹  Parar",
            height=36,
            fg_color="#c0392b",
            hover_color="#962d22",
            command=self._stop_extraction,
            state="disabled",
        )
        self.stop_btn.grid(row=14, column=0, padx=20, pady=(4, 20), sticky="ew")

        # --- Main area ---
        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # Stats bar
        stats = ctk.CTkFrame(main)
        stats.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)

        self.stat_total = self._stat_card(stats, "Registos", "0", 0)
        self.stat_emails = self._stat_card(stats, "E-mails únicos", "0", 1)
        self.stat_country = self._stat_card(stats, "País", "—", 2)
        self.stat_status = self._stat_card(stats, "Estado", "Pronto", 3)

        # Progress
        prog_frame = ctk.CTkFrame(main, fg_color="transparent")
        prog_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        prog_frame.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(prog_frame, height=14)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            prog_frame, text="Configure os filtros e clique em Iniciar Extração.", anchor="w"
        )
        self.status_label.grid(row=1, column=0, sticky="ew")

        # Results table
        table_frame = ctk.CTkFrame(main)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        columns = ("nipc", "razao_social", "email", "municipio", "pais")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.tree.heading("nipc", text="NIPC/CNPJ")
        self.tree.heading("razao_social", text="Razão Social")
        self.tree.heading("email", text="E-mail")
        self.tree.heading("municipio", text="Município")
        self.tree.heading("pais", text="País")
        self.tree.column("nipc", width=130)
        self.tree.column("razao_social", width=280)
        self.tree.column("email", width=220)
        self.tree.column("municipio", width=140)
        self.tree.column("pais", width=60)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

        # Export bar
        export_frame = ctk.CTkFrame(main, fg_color="transparent")
        export_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 16))

        ctk.CTkButton(
            export_frame, text="💾 Exportar SQLite (.db)", command=self._export_sqlite, width=200
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            export_frame, text="📄 Exportar CSV", command=self._export_csv, width=160
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            export_frame, text="🗑 Limpar resultados", command=self._clear_results, width=140,
            fg_color="gray40", hover_color="gray30",
        ).pack(side="right")

    def _stat_card(self, parent: ctk.CTkFrame, label: str, value: str, col: int) -> ctk.CTkLabel:
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=col, padx=6, pady=8, sticky="ew")
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(8, 0))
        val_label = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=22, weight="bold"))
        val_label.pack(pady=(0, 8))
        return val_label

    def _on_country_change(self, _=None) -> None:
        country_key = self.country_var.get()
        country = COUNTRIES[country_key]
        sources = country["sources"]
        source_keys = list(sources.keys())
        self.source_menu.configure(values=source_keys)
        if source_keys:
            self.source_var.set(source_keys[0])

        for widget in self.filter_frame.winfo_children():
            widget.destroy()

        if country_key == "BR":
            ctk.CTkLabel(self.filter_frame, text="Estado (UF)", anchor="w").pack(fill="x")
            self.uf_var = ctk.StringVar(value="Todos")
            ctk.CTkOptionMenu(self.filter_frame, variable=self.uf_var, values=BRAZIL_UFS, width=260).pack(
                fill="x", pady=(4, 8)
            )
            self.only_active_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(self.filter_frame, text="Apenas ativas", variable=self.only_active_var).pack(
                anchor="w", pady=4
            )
        elif country_key == "PT":
            ctk.CTkLabel(self.filter_frame, text="Distrito/Cidade (opcional)", anchor="w").pack(fill="x")
            self.distrito_var = ctk.StringVar(value="")
            ctk.CTkEntry(self.filter_frame, textvariable=self.distrito_var, placeholder_text="Ex: Lisboa", width=260).pack(
                fill="x", pady=(4, 8)
            )

        self.stat_country.configure(text=f"{country['flag']} {country['name']}")

    def _set_status(self, message: str, progress: float | None = None) -> None:
        self.status_label.configure(text=message)
        if progress is not None:
            self.progress.set(min(max(progress, 0.0), 1.0))

    def _update_stats(self) -> None:
        emails = {r.get("email", "") for r in self.records}
        self.stat_total.configure(text=str(len(self.records)))
        self.stat_emails.configure(text=str(len(emails)))

    def _refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.records[-500:]:
            self.tree.insert("", "end", values=(
                row.get("cnpj", ""),
                row.get("razao_social", "")[:50],
                row.get("email", ""),
                row.get("municipio", ""),
                row.get("pais", ""),
            ))

    def _start_extraction(self) -> None:
        if self._extracting:
            return
        self._extracting = True
        self._stop_requested = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.stat_status.configure(text="A extrair...")
        self.progress.set(0)
        threading.Thread(target=self._run_extraction, daemon=True).start()

    def _stop_extraction(self) -> None:
        self._stop_requested = True
        self._set_status("A parar...")

    def _run_extraction(self) -> None:
        try:
            country_key = self.country_var.get()
            country = COUNTRIES[country_key]
            source_key = self.source_var.get()
            source = country["sources"][source_key]

            max_text = self.max_var.get().strip()
            max_records = None if max_text == "0" else int(max_text or "100")
            auto = self.mode_var.get() == "automatico"
            only_email = self.only_email_var.get()

            kwargs: dict = {
                "max_records": max_records,
                "only_with_email": only_email,
                "progress_callback": lambda v, m: self.after(0, self._set_status, m, v),
            }

            if source_key == "receita_federal":
                uf = getattr(self, "uf_var", None)
                kwargs.update({
                    "partitions": list(range(10)) if auto else [0],
                    "uf_filter": None if not uf or uf.get() == "Todos" else uf.get(),
                    "only_active": getattr(self, "only_active_var", ctk.BooleanVar(value=True)).get(),
                    "load_razao_social": True,
                })
            elif source_key == "dadosbrasil_api":
                uf = getattr(self, "uf_var", None)
                kwargs.update({
                    "uf": None if not uf or uf.get() == "Todos" else uf.get(),
                })
            elif source_key == "fiz_portugal":
                distrito = getattr(self, "distrito_var", None)
                kwargs.update({
                    "auto_discover": True,
                    "max_sitemap_pages": None if auto else 1,
                    "distrito": distrito.get().strip() if distrito and distrito.get().strip() else None,
                })
            elif source_key == "sitemap_generico":
                kwargs.update({
                    "sitemap_url": FIZ_SITEMAP_INDEX,
                    "auto_discover": auto,
                })

            new_records: list[dict] = []
            for record in source.extract(**kwargs):
                if self._stop_requested:
                    break
                row = record.to_dict()
                if country_key == "BR" and row.get("cnpj"):
                    row["cnpj"] = format_cnpj(row["cnpj"])
                new_records.append(row)
                if len(new_records) % 10 == 0:
                    self.after(0, self._set_status, f"{len(new_records):,} registos...", None)

            self.records = dedupe_records(new_records)
            self.after(0, self._on_extraction_done)
        except Exception as exc:
            self.after(0, self._on_extraction_error, str(exc))

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
        messagebox.showerror(APP_NAME, f"Erro na extração:\n{error}")

    def _clear_results(self) -> None:
        self.records = []
        self._refresh_table()
        self._update_stats()
        self.progress.set(0)
        self._set_status("Resultados limpos.")

    def _export_sqlite(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Não há dados para exportar.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("Todos", "*.*")],
            title="Guardar base de dados SQLite",
        )
        if path:
            export_sqlite(self.records, path)
            messagebox.showinfo(APP_NAME, f"Exportado para:\n{path}")

    def _export_csv(self) -> None:
        if not self.records:
            messagebox.showwarning(APP_NAME, "Não há dados para exportar.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            title="Guardar ficheiro CSV",
        )
        if path:
            export_csv(self.records, path)
            messagebox.showinfo(APP_NAME, f"Exportado para:\n{path}")


def main() -> None:
    app = CompanyEmailApp()
    app.mainloop()


if __name__ == "__main__":
    main()
