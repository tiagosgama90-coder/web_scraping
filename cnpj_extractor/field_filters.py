from __future__ import annotations

from typing import Iterable

# Campos disponíveis: (chave_interna, rótulo_exportação, ligado_por_defeito)
AVAILABLE_FIELDS: list[tuple[str, str, bool]] = [
    ("email", "email", True),
    ("razao_social", "empresa", True),
    ("nome_fantasia", "nome_fantasia", False),
    ("cnpj", "cnpj", True),
    ("telefone", "telefone", False),
    ("uf", "uf", True),
    ("municipio", "municipio", True),
    ("cnae", "cnae", False),
    ("situacao", "situacao", False),
    ("pais", "pais", False),
    ("website", "website", False),
    ("fonte", "fonte", False),
]

DEFAULT_FIELD_KEYS = [key for key, _, default in AVAILABLE_FIELDS if default]


def get_field_labels() -> dict[str, str]:
    return {key: label for key, label, _ in AVAILABLE_FIELDS}


def filter_records_by_requirements(
    records: Iterable[dict],
    *,
    require_email: bool = True,
    require_phone: bool = False,
    require_cnpj: bool = False,
) -> list[dict]:
    result: list[dict] = []
    for record in records:
        row = dict(record)
        if require_email and not (row.get("email") or "").strip():
            continue
        if require_phone and not (row.get("telefone") or "").strip():
            continue
        if require_cnpj and not (row.get("cnpj") or "").strip():
            continue
        result.append(row)
    return result


def project_record_fields(record: dict, selected_fields: list[str]) -> dict:
    """Projeta registo apenas com campos selecionados (nomes amigáveis para Excel)."""
    labels = get_field_labels()
    projected: dict = {}
    for key in selected_fields:
        value = record.get(key, "")
        if value is None:
            value = ""
        label = labels.get(key, key)
        projected[label] = str(value).strip() if value else ""
    return projected


def project_records(records: Iterable[dict], selected_fields: list[str]) -> list[dict]:
    if not selected_fields:
        selected_fields = list(DEFAULT_FIELD_KEYS)
    return [project_record_fields(r, selected_fields) for r in records]
