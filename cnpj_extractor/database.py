from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from cnpj_extractor.field_filters import DEFAULT_FIELD_KEYS, get_field_labels, project_records
from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.utils import clean_and_validate_email, dedupe_by_email, filter_valid_email_records

CHUNK_SIZE_DEFAULT = 1000


@dataclass
class ChunkExportResult:
    folder: Path
    files: list[Path]
    total_rows: int
    chunk_size: int

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS empresas (
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
    pais TEXT,
    website TEXT,
    fonte TEXT,
    data_extracao TEXT
);

CREATE INDEX IF NOT EXISTS idx_empresas_email ON empresas(email);
CREATE INDEX IF NOT EXISTS idx_empresas_cnpj ON empresas(cnpj);
CREATE INDEX IF NOT EXISTS idx_empresas_uf ON empresas(uf);
CREATE INDEX IF NOT EXISTS idx_empresas_fonte ON empresas(fonte);
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def records_to_dataframe(records: Iterable[CompanyEmail | dict]) -> pd.DataFrame:
    rows = [
        record.to_dict() if isinstance(record, CompanyEmail) else record
        for record in records
    ]
    if not rows:
        return pd.DataFrame(
            columns=[
                "cnpj",
                "razao_social",
                "nome_fantasia",
                "email",
                "telefone",
                "uf",
                "municipio",
                "cnae",
                "situacao",
                "pais",
                "website",
                "fonte",
                "data_extracao",
            ]
        )
    return pd.DataFrame(rows)


def export_filtered_csv(
    records: Iterable[CompanyEmail | dict],
    path: str | Path,
    *,
    selected_fields: list[str] | None = None,
    unique_emails: bool = True,
) -> Path:
    """Exporta CSV com colunas escolhidas pelo utilizador."""
    rows = [
        record.to_dict() if isinstance(record, CompanyEmail) else dict(record)
        for record in records
    ]
    cleaned = filter_valid_email_records(rows)
    if unique_emails and "email" in (selected_fields or DEFAULT_FIELD_KEYS):
        cleaned = dedupe_by_email(cleaned)

    fields = selected_fields or DEFAULT_FIELD_KEYS
    projected = project_records(cleaned, fields)

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    labels = [get_field_labels().get(f, f) for f in fields]
    df = pd.DataFrame(projected, columns=labels) if projected else pd.DataFrame(columns=labels)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return output


def export_csv(
    records: Iterable[CompanyEmail | dict],
    path: str | Path,
    *,
    selected_fields: list[str] | None = None,
) -> Path:
    if selected_fields:
        return export_filtered_csv(records, path, selected_fields=selected_fields, unique_emails=False)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df = records_to_dataframe(records)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return output


def export_emails_only_csv(
    records: Iterable[CompanyEmail | dict],
    path: str | Path,
    *,
    unique_emails: bool = True,
) -> Path:
    """
    Exporta lista limpa para Excel — apenas e-mails validados.
    Colunas: email, empresa, cnpj, uf, municipio
    """
    rows = [
        record.to_dict() if isinstance(record, CompanyEmail) else dict(record)
        for record in records
    ]
    cleaned = filter_valid_email_records(rows)
    if unique_emails:
        cleaned = dedupe_by_email(cleaned)

    export_rows = []
    for row in cleaned:
        export_rows.append(
            {
                "email": row.get("email", ""),
                "empresa": (row.get("razao_social") or row.get("nome_fantasia") or "").strip(),
                "cnpj": row.get("cnpj", ""),
                "uf": row.get("uf", ""),
                "municipio": row.get("municipio", ""),
            }
        )

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(export_rows, columns=["email", "empresa", "cnpj", "uf", "municipio"])
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return output


def export_emails_for_marketing_csv(
    records: Iterable[CompanyEmail | dict],
    path: str | Path,
) -> Path:
    """Formato compatível com Mailchimp, Brevo, etc.: email + nome."""
    rows = [
        record.to_dict() if isinstance(record, CompanyEmail) else dict(record)
        for record in records
    ]
    cleaned = dedupe_by_email(filter_valid_email_records(rows))

    export_rows = [
        {
            "email": row.get("email", ""),
            "nome": (row.get("razao_social") or row.get("nome_fantasia") or "Empresa").strip(),
        }
        for row in cleaned
    ]

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(export_rows, columns=["email", "nome"])
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return output


def _records_to_dicts(records: Iterable[CompanyEmail | dict]) -> list[dict]:
    return [
        record.to_dict() if isinstance(record, CompanyEmail) else dict(record)
        for record in records
    ]


def _write_csv_chunks(
    rows: list[dict],
    *,
    folder: Path,
    labels: list[str],
    chunk_size: int,
    file_prefix: str = "parte",
) -> list[Path]:
    """Escreve CSV em partes sem carregar tudo no pandas."""
    folder.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    if not rows:
        path = folder / f"{file_prefix}_0001.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            csv.DictWriter(handle, fieldnames=labels).writeheader()
        files.append(path)
        return files

    part = 1
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start : start + chunk_size]
        path = folder / f"{file_prefix}_{part:04d}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=labels)
            writer.writeheader()
            writer.writerows(chunk)
        files.append(path)
        part += 1
    return files


def export_filtered_csv_chunked(
    records: Iterable[CompanyEmail | dict],
    output_dir: str | Path,
    *,
    base_name: str,
    selected_fields: list[str] | None = None,
    unique_emails: bool = True,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
) -> ChunkExportResult:
    """Exporta CSV filtrado em ficheiros de N linhas (ideal para Excel e volumes grandes)."""
    rows = _records_to_dicts(records)
    cleaned = filter_valid_email_records(rows)
    fields = selected_fields or DEFAULT_FIELD_KEYS
    if unique_emails and "email" in fields:
        cleaned = dedupe_by_email(cleaned)

    projected = project_records(cleaned, fields)
    labels = [get_field_labels().get(field, field) for field in fields]
    folder = Path(output_dir) / base_name
    files = _write_csv_chunks(projected, folder=folder, labels=labels, chunk_size=chunk_size)
    return ChunkExportResult(folder=folder, files=files, total_rows=len(projected), chunk_size=chunk_size)


def export_emails_only_csv_chunked(
    records: Iterable[CompanyEmail | dict],
    output_dir: str | Path,
    *,
    base_name: str,
    unique_emails: bool = True,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
) -> ChunkExportResult:
    """Lista limpa em vários CSV — colunas: email, empresa, cnpj, uf, municipio."""
    rows = _records_to_dicts(records)
    cleaned = filter_valid_email_records(rows)
    if unique_emails:
        cleaned = dedupe_by_email(cleaned)

    export_rows = [
        {
            "email": row.get("email", ""),
            "empresa": (row.get("razao_social") or row.get("nome_fantasia") or "").strip(),
            "cnpj": row.get("cnpj", ""),
            "uf": row.get("uf", ""),
            "municipio": row.get("municipio", ""),
        }
        for row in cleaned
    ]
    labels = ["email", "empresa", "cnpj", "uf", "municipio"]
    folder = Path(output_dir) / base_name
    files = _write_csv_chunks(export_rows, folder=folder, labels=labels, chunk_size=chunk_size)
    return ChunkExportResult(folder=folder, files=files, total_rows=len(export_rows), chunk_size=chunk_size)


def export_emails_txt_chunked(
    records: Iterable[CompanyEmail | dict],
    output_dir: str | Path,
    *,
    base_name: str,
    unique_emails: bool = True,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
) -> ChunkExportResult:
    """Exporta só emails (1 por linha) em ficheiros .txt leves."""
    rows = _records_to_dicts(records)
    cleaned = filter_valid_email_records(rows)
    if unique_emails:
        cleaned = dedupe_by_email(cleaned)

    emails = [row.get("email", "").strip() for row in cleaned if row.get("email")]
    folder = Path(output_dir) / base_name
    folder.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    if not emails:
        path = folder / "emails_0001.txt"
        path.write_text("", encoding="utf-8")
        files.append(path)
        return ChunkExportResult(folder=folder, files=files, total_rows=0, chunk_size=chunk_size)

    part = 1
    for start in range(0, len(emails), chunk_size):
        chunk = emails[start : start + chunk_size]
        path = folder / f"emails_{part:04d}.txt"
        path.write_text("\n".join(chunk) + "\n", encoding="utf-8")
        files.append(path)
        part += 1

    return ChunkExportResult(folder=folder, files=files, total_rows=len(emails), chunk_size=chunk_size)


def export_sqlite(
    records: Iterable[CompanyEmail | dict],
    path: str | Path,
    *,
    replace: bool = True,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if replace and output.exists():
        output.unlink()

    df = records_to_dataframe(records)
    conn = sqlite3.connect(output)
    try:
        ensure_schema(conn)
        if not df.empty:
            df.to_sql("empresas", conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()
    return output


def load_sqlite(path: str | Path) -> pd.DataFrame:
    conn = sqlite3.connect(path)
    try:
        return pd.read_sql_query("SELECT * FROM empresas", conn)
    finally:
        conn.close()
