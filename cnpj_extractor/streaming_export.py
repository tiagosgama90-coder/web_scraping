from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from cnpj_extractor.database import CHUNK_SIZE_DEFAULT, ensure_schema
from cnpj_extractor.email_validator import validate_email_full
from cnpj_extractor.field_filters import DEFAULT_FIELD_KEYS, get_field_labels, project_record_fields
from cnpj_extractor.utils import clean_and_validate_email


@dataclass
class StreamingExportResult:
    folder: Path
    total_rows: int
    chunk_size: int
    csv_files: list[Path] = field(default_factory=list)
    txt_files: list[Path] = field(default_factory=list)
    sqlite_path: Path | None = None
    label: str = ""

    @property
    def summary(self) -> str:
        parts = [f"{self.total_rows:,} registos guardados"]
        if self.csv_files:
            parts.append(f"{len(self.csv_files)} ficheiro(s) CSV")
        if self.txt_files:
            parts.append(f"{len(self.txt_files)} ficheiro(s) .txt")
        if self.sqlite_path:
            parts.append(f"SQLite: {self.sqlite_path.name}")
        header = f"{self.label}\n" if self.label else ""
        return (
            f"{header}"
            + "\n".join(parts)
            + f"\n({self.chunk_size:,} linhas por ficheiro)\n\nPasta:\n{self.folder}"
        )


class StreamingExporter:
    """Grava registos em CSV/TXT/SQLite à medida que chegam — sem carregar tudo na RAM."""

    def __init__(
        self,
        export_dir: str | Path,
        base_name: str,
        *,
        selected_fields: list[str] | None = None,
        chunk_size: int = CHUNK_SIZE_DEFAULT,
        write_csv: bool = True,
        write_txt: bool = True,
        use_sqlite: bool = True,
        unique_emails: bool = True,
        check_mx: bool = False,
        require_email: bool = True,
        require_phone: bool = False,
        require_cnpj: bool = False,
        label: str = "",
    ) -> None:
        self.fields = selected_fields or list(DEFAULT_FIELD_KEYS)
        self.labels = [get_field_labels().get(key, key) for key in self.fields]
        self.chunk_size = max(100, chunk_size)
        self.write_csv = write_csv
        self.write_txt = write_txt
        self.use_sqlite = use_sqlite
        self.unique_emails = unique_emails
        self.check_mx = check_mx
        self.require_email = require_email
        self.require_phone = require_phone
        self.require_cnpj = require_cnpj
        self.label = label

        self.folder = Path(export_dir) / base_name
        self.folder.mkdir(parents=True, exist_ok=True)

        self.total_rows = 0
        self._seen_emails: set[str] = set()
        self._csv_buffer: list[dict] = []
        self._txt_buffer: list[str] = []
        self._csv_part = 0
        self._txt_part = 0
        self.csv_files: list[Path] = []
        self.txt_files: list[Path] = []

        self.sqlite_path: Path | None = None
        self._sqlite_conn: sqlite3.Connection | None = None
        self._sqlite_batch: list[tuple] = []
        if self.use_sqlite:
            self.sqlite_path = self.folder / "empresas.db"
            if self.sqlite_path.exists():
                self.sqlite_path.unlink()
            self._sqlite_conn = sqlite3.connect(self.sqlite_path)
            ensure_schema(self._sqlite_conn)

    def _passes_filters(self, record: dict) -> dict | None:
        row = dict(record)
        email = row.get("email", "")
        if self.require_email or email:
            cleaned, status = validate_email_full(email, check_mx=self.check_mx)
            if self.require_email and not cleaned:
                return None
            if cleaned:
                row["email"] = cleaned
            elif self.require_email:
                return None

        if self.require_phone and not str(row.get("telefone", "")).strip():
            return None
        if self.require_cnpj and not str(row.get("cnpj", "")).strip():
            return None

        if self.unique_emails and row.get("email"):
            key = row["email"].strip().lower()
            if key in self._seen_emails:
                return None
            self._seen_emails.add(key)

        return row

    def add(self, record: dict) -> bool:
        row = self._passes_filters(record)
        if not row:
            return False

        self.total_rows += 1
        if not row.get("data_extracao"):
            row["data_extracao"] = datetime.now(timezone.utc).isoformat()

        if self.write_csv:
            self._csv_buffer.append(project_record_fields(row, self.fields))
            if len(self._csv_buffer) >= self.chunk_size:
                self._flush_csv()

        if self.write_txt and row.get("email"):
            self._txt_buffer.append(row["email"].strip())
            if len(self._txt_buffer) >= self.chunk_size:
                self._flush_txt()

        if self._sqlite_conn is not None:
            self._sqlite_batch.append(self._row_to_sql_tuple(row))
            if len(self._sqlite_batch) >= self.chunk_size:
                self._flush_sqlite()

        return True

    def _row_to_sql_tuple(self, row: dict) -> tuple:
        return (
            row.get("cnpj", "") or "",
            row.get("razao_social", "") or "",
            row.get("nome_fantasia", "") or "",
            row.get("email", "") or "",
            row.get("telefone", "") or "",
            row.get("uf", "") or "",
            row.get("municipio", "") or "",
            row.get("cnae", "") or "",
            row.get("situacao", "") or "",
            row.get("pais", "") or "",
            row.get("website", "") or "",
            row.get("fonte", "") or "",
            row.get("data_extracao", "") or "",
        )

    def _flush_csv(self) -> None:
        if not self._csv_buffer:
            return
        self._csv_part += 1
        path = self.folder / f"parte_{self._csv_part:04d}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.labels)
            writer.writeheader()
            writer.writerows(self._csv_buffer)
        self.csv_files.append(path)
        self._csv_buffer.clear()

    def _flush_txt(self) -> None:
        if not self._txt_buffer:
            return
        self._txt_part += 1
        path = self.folder / f"emails_{self._txt_part:04d}.txt"
        path.write_text("\n".join(self._txt_buffer) + "\n", encoding="utf-8")
        self.txt_files.append(path)
        self._txt_buffer.clear()

    def _flush_sqlite(self) -> None:
        if not self._sqlite_conn or not self._sqlite_batch:
            return
        self._sqlite_conn.executemany(
            """
            INSERT INTO empresas (
                cnpj, razao_social, nome_fantasia, email, telefone, uf, municipio,
                cnae, situacao, pais, website, fonte, data_extracao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            self._sqlite_batch,
        )
        self._sqlite_conn.commit()
        self._sqlite_batch.clear()

    def close(self) -> StreamingExportResult:
        self._flush_csv()
        self._flush_txt()
        self._flush_sqlite()
        if self._sqlite_conn is not None:
            self._sqlite_conn.close()
            self._sqlite_conn = None
        return StreamingExportResult(
            folder=self.folder,
            total_rows=self.total_rows,
            chunk_size=self.chunk_size,
            csv_files=list(self.csv_files),
            txt_files=list(self.txt_files),
            sqlite_path=self.sqlite_path,
            label=self.label,
        )
