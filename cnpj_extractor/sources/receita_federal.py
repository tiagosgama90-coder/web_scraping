from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Iterator
from urllib.parse import urljoin

import requests

from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.utils import (
    format_phone,
    is_valid_email,
    normalize_email,
    normalize_situacao,
)
from cnpj_extractor.sector_filters import matches_sector

CASADOS_DADOS_BASE = "https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/"
MIN_ZIP_BYTES = 100
ESTABELECIMENTOS_COLUMNS = [
    "cnpj_basico",
    "cnpj_ordem",
    "cnpj_dv",
    "identificador_matriz_filial",
    "nome_fantasia",
    "situacao_cadastral",
    "data_situacao_cadastral",
    "motivo_situacao_cadastral",
    "nome_cidade_exterior",
    "pais",
    "data_inicio_atividade",
    "cnae_fiscal_principal",
    "cnae_fiscal_secundaria",
    "tipo_logradouro",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cep",
    "uf",
    "municipio",
    "ddd_1",
    "telefone_1",
    "ddd_2",
    "telefone_2",
    "ddd_fax",
    "fax",
    "correio_eletronico",
    "situacao_especial",
    "data_situacao_especial",
]
EMPRESAS_COLUMNS = [
    "cnpj_basico",
    "razao_social",
    "natureza_juridica",
    "qualificacao_responsavel",
    "capital_social",
    "porte_empresa",
    "ente_federativo_responsavel",
]


class ReceitaFederalSource(BaseSource):
    name = "Receita Federal (Dados Abertos)"
    description = (
        "Base oficial com ~67 milhões de empresas. Processa arquivos Estabelecimentos "
        "da Receita Federal (via mirror Casa dos Dados)."
    )

    def list_available_releases(self) -> list[str]:
        response = requests.get(CASADOS_DADOS_BASE, timeout=30)
        response.raise_for_status()
        folders = re.findall(r'href="(\d{4}-\d{2}-\d{2})/"', response.text)
        return sorted(set(folders))

    def get_latest_release(self) -> str:
        releases = self.list_available_releases()
        if not releases:
            raise RuntimeError("Não foi possível listar versões dos dados abertos.")
        return releases[-1]

    @staticmethod
    def is_valid_zip_file(path: Path) -> bool:
        """Verifica se o ficheiro ZIP existe e contém CSV válido."""
        if not path.exists() or path.stat().st_size < MIN_ZIP_BYTES:
            return False
        try:
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    return False
                return any(name.lower().endswith(".csv") for name in archive.namelist())
        except (zipfile.BadZipFile, OSError):
            return False

    def download_file(
        self,
        release: str,
        filename: str,
        dest_dir: Path,
        progress_callback: ProgressCallback = None,
        *,
        force_redownload: bool = False,
    ) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        output = dest_dir / filename
        if output.exists() and not force_redownload:
            if self.is_valid_zip_file(output):
                self._report(progress_callback, 1.0, f"{filename} já existe localmente.")
                return output
            self._report(
                progress_callback,
                0.0,
                f"{filename} corrompido ou incompleto — a transferir de novo...",
            )
            output.unlink(missing_ok=True)

        url = urljoin(CASADOS_DADOS_BASE, f"{release}/{filename}")
        self._report(progress_callback, 0.0, f"A transferir {filename}...")
        temp_output = output.with_suffix(output.suffix + ".part")
        if temp_output.exists():
            temp_output.unlink(missing_ok=True)

        with requests.get(url, stream=True, timeout=300) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            with open(temp_output, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        self._report(
                            progress_callback,
                            downloaded / total,
                            f"A transferir {filename} ({downloaded // (1024 * 1024)} MB)",
                        )

        if not self.is_valid_zip_file(temp_output):
            temp_output.unlink(missing_ok=True)
            raise RuntimeError(
                f"O ficheiro transferido '{filename}' não é um ZIP válido. "
                "Verifique a ligação à internet e tente novamente."
            )

        temp_output.replace(output)
        return output

    def load_empresas_lookup(
        self,
        release: str,
        data_dir: Path,
        partitions: list[int] | None = None,
        progress_callback: ProgressCallback = None,
    ) -> dict[str, str]:
        lookup: dict[str, str] = {}
        parts = partitions if partitions is not None else list(range(10))
        total = len(parts)
        for index, part in enumerate(parts):
            filename = f"Empresas{part}.zip"
            zip_path = self.download_file(release, filename, data_dir, progress_callback)
            if not self.is_valid_zip_file(zip_path):
                raise RuntimeError(f"ZIP inválido após transferência: {filename}")
            with zipfile.ZipFile(zip_path) as archive:
                csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
                with archive.open(csv_name) as raw:
                    text = io.TextIOWrapper(raw, encoding="latin-1", newline="")
                    reader = csv.reader(text, delimiter=";")
                    for row in reader:
                        if len(row) < 2:
                            continue
                        lookup[row[0]] = row[1]
            self._report(
                progress_callback,
                (index + 1) / total,
                f"Índice de empresas carregado ({index + 1}/{total})",
            )
        return lookup

    def _iter_estabelecimentos_rows(
        self, zip_path: Path
    ) -> Iterator[list[str]]:
        if not self.is_valid_zip_file(zip_path):
            raise zipfile.BadZipFile(f"Ficheiro ZIP inválido: {zip_path.name}")
        with zipfile.ZipFile(zip_path) as archive:
            csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
            with archive.open(csv_name) as raw:
                text = io.TextIOWrapper(raw, encoding="latin-1", newline="")
                reader = csv.reader(text, delimiter=";")
                for row in reader:
                    yield row

    def find_local_partitions(self, data_dir: str | Path) -> list[int]:
        """Deteta ZIPs Estabelecimentos já descarregados na pasta."""
        data_path = Path(data_dir)
        parts: list[int] = []
        for part in range(10):
            zip_path = data_path / f"Estabelecimentos{part}.zip"
            if self.is_valid_zip_file(zip_path):
                parts.append(part)
        return parts

    def extract(
        self,
        *,
        release: str | None = None,
        data_dir: str | Path = "data/rfb",
        partitions: list[int] | None = None,
        uf_filter: str | None = None,
        cnae_filter: str | None = None,
        only_active: bool = True,
        only_with_email: bool = True,
        max_records: int | None = None,
        load_razao_social: bool = True,
        use_local_zips_only: bool = False,
        progress_callback: ProgressCallback = None,
    ) -> Iterator[CompanyEmail]:
        data_path = Path(data_dir)
        release = release or self.get_latest_release()

        if use_local_zips_only:
            parts = self.find_local_partitions(data_path)
            if not parts:
                raise RuntimeError(
                    f"Nenhum ZIP válido encontrado em {data_path}. "
                    "Coloque ficheiros Estabelecimentos0.zip … Estabelecimentos9.zip na pasta."
                )
            self._report(
                progress_callback,
                0.0,
                f"A usar {len(parts)} ZIP(s) locais: {parts}",
            )
        else:
            parts = partitions if partitions is not None else list(range(10))

        empresas_lookup: dict[str, str] = {}
        if load_razao_social:
            empresas_lookup = self.load_empresas_lookup(
                release, data_path, partitions=parts, progress_callback=progress_callback
            )

        found = 0
        total_parts = len(parts)
        for part_index, part in enumerate(parts):
            filename = f"Estabelecimentos{part}.zip"
            if use_local_zips_only:
                zip_path = data_path / filename
                if not self.is_valid_zip_file(zip_path):
                    continue
                self._report(progress_callback, part_index / total_parts, f"A processar {filename} (local)...")
            else:
                zip_path = self.download_file(release, filename, data_path, progress_callback)
            processed = 0
            for row in self._iter_estabelecimentos_rows(zip_path):
                processed += 1
                if len(row) < 28:
                    continue

                email = normalize_email(row[27])
                if only_with_email and not is_valid_email(email):
                    continue

                uf = (row[19] or "").strip().upper()
                if uf_filter and uf != uf_filter.upper():
                    continue

                cnae_value = (row[11] or "").strip()
                if cnae_filter and not matches_sector(cnae_value, cnae_filter):
                    continue

                situacao = normalize_situacao(row[5])
                if only_active and situacao not in {"Ativa", "02", "2"}:
                    continue

                cnpj = f"{row[0]}{row[1]}{row[2]}"
                telefone = format_phone(row[21], row[22])
                record = CompanyEmail(
                    cnpj=cnpj,
                    email=email,
                    razao_social=empresas_lookup.get(row[0], ""),
                    nome_fantasia=(row[4] or "").strip(),
                    telefone=telefone,
                    uf=uf,
                    municipio=(row[20] or "").strip(),
                    cnae=cnae_value,
                    situacao=situacao,
                    pais="BR",
                    fonte=self.name,
                )
                yield record
                found += 1
                if max_records and found >= max_records:
                    return

                if processed % 100_000 == 0:
                    self._report(
                        progress_callback,
                        (part_index + processed / 1_000_000) / total_parts,
                        f"Partição {part}: {processed:,} linhas, {found:,} e-mails",
                    )

            self._report(
                progress_callback,
                (part_index + 1) / total_parts,
                f"Partição {part} concluída ({found:,} e-mails)",
            )
