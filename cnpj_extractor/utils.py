from __future__ import annotations

import re
from typing import Iterable

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

JUNK_EMAIL_PREFIXES = (
    "noreply",
    "no-reply",
    "nao-responda",
    "donotreply",
    "mailer-daemon",
    "postmaster",
    "abuse",
    "bounce",
    "spam",
    "root",
    "admin@",
)

JUNK_EMAIL_DOMAINS = (
    "example.com",
    "example.org",
    "test.com",
    "teste.com",
    "email.com",
    "naoinformado",
    "sememail",
    "naotem",
    "invalid",
    "localhost",
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
    return clean_and_validate_email(value) is not None


def clean_and_validate_email(value: str) -> str | None:
    """Normaliza e valida e-mail — rejeita lixo comum em bases públicas."""
    email = normalize_email(value)
    if not email or email in {"n/a", "na", "null", "none", "-", "0", "nao@nao.com"}:
        return None
    if not EMAIL_PATTERN.match(email):
        return None

    local, _, domain = email.partition("@")
    if not local or not domain or "." not in domain:
        return None

    if any(email.startswith(prefix) or local == prefix.rstrip("@") for prefix in JUNK_EMAIL_PREFIXES):
        return None
    if any(junk in domain for junk in JUNK_EMAIL_DOMAINS):
        return None
    if len(local) < 2 or len(domain) < 4:
        return None

    return email


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


def dedupe_by_email(records: Iterable[dict]) -> list[dict]:
    """Remove e-mails duplicados — mantém o primeiro registo de cada e-mail."""
    seen: set[str] = set()
    unique: list[dict] = []
    for record in records:
        email = clean_and_validate_email(record.get("email", ""))
        if not email or email in seen:
            continue
        seen.add(email)
        row = dict(record)
        row["email"] = email
        unique.append(row)
    return unique


def filter_valid_email_records(records: Iterable[dict]) -> list[dict]:
    """Mantém apenas registos com e-mail válido e limpo."""
    result: list[dict] = []
    for record in records:
        email = clean_and_validate_email(record.get("email", ""))
        if not email:
            continue
        row = dict(record)
        row["email"] = email
        result.append(row)
    return result
