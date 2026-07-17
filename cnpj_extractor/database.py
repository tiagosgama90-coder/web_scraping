from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

from cnpj_extractor.models import CompanyEmail

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


def export_csv(records: Iterable[CompanyEmail | dict], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df = records_to_dataframe(records)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return output


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
