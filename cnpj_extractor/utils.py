from __future__ import annotations

import re
from typing import Iterable

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

SITUACAO_MAP = {
    "01": "Nula",
    "02": "Ativa",
    "03": "Suspensa",
    "04": "Inapta",
    "08": "Baixada",
    "1": "Nula",
    "2": "Ativa",
    "3": "Suspensa",
    "4": "Inapta",
    "8": "Baixada",
    "Ativa": "Ativa",
    "Baixada": "Baixada",
}


def clean_cnpj(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def format_cnpj(value: str) -> str:
    digits = clean_cnpj(value)
    if len(digits) != 14:
        return digits
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def is_valid_email(value: str) -> bool:
    email = (value or "").strip().lower()
    if not email or email in {"n/a", "na", "null", "none", "-", "0"}:
        return False
    return bool(EMAIL_PATTERN.match(email))


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def normalize_situacao(value: str) -> str:
    raw = (value or "").strip()
    return SITUACAO_MAP.get(raw, raw)


def format_phone(ddd: str, phone: str) -> str:
    ddd = (ddd or "").strip()
    phone = (phone or "").strip()
    if not phone:
        return ""
    if ddd:
        return f"({ddd}) {phone}"
    return phone


def parse_cnpj_list(text: str) -> list[str]:
    parts = re.split(r"[\s,;]+", text or "")
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        digits = clean_cnpj(part)
        if len(digits) == 14 and digits not in seen:
            seen.add(digits)
            result.append(digits)
    return result


def dedupe_records(records: Iterable[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for record in records:
        key = (record.get("cnpj", ""), record.get("email", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique
