from __future__ import annotations

import re

# Rótulos por país para a interface
SECTOR_LABELS = {
    "BR": "CNAE (setor de atividade)",
    "PT": "CAE / ISIC (setor)",
    "OUTRO": "Código setor (CNAE / CAE / ISIC)",
}

SECTOR_PLACEHOLDERS = {
    "BR": "Ex: 6202300, 62, 4711 (vários separados por vírgula)",
    "PT": "Ex: 6201, 47, 86 (ISIC Rev.4)",
    "OUTRO": "Ex: 6201, 62 (prefixo ou código completo)",
}

SECTOR_HINTS = {
    "BR": (
        "CNAE Brasil — use código completo (7 dígitos) ou prefixo:\n"
        "  62 = tecnologia/TI | 47 = comércio | 86 = saúde | 41 = construção"
    ),
    "PT": (
        "CAE/ISIC Portugal (campo isicV4 no FIZ):\n"
        "  62 = TI | 47 = comércio | 86 = saúde | 41 = construção"
    ),
    "OUTRO": (
        "Aceita CNAE (BR), CAE/ISIC (PT/EU) ou códigos similares.\n"
        "Separe vários com vírgula. Prefixo funciona: 62 inclui 6201, 6202…"
    ),
}

# Prefixos comuns (referência rápida na UI)
COMMON_SECTORS = [
    ("62", "Tecnologia / TI / Software"),
    ("47", "Comércio retalhista"),
    ("86", "Saúde"),
    ("41", "Construção"),
    ("56", "Restauração / catering"),
    ("49", "Transportes"),
    ("85", "Educação"),
    ("68", "Imobiliário"),
]


def normalize_sector_code(value: str) -> str:
    """Mantém apenas dígitos e letras (alguns ISIC têm letras)."""
    return re.sub(r"[^a-zA-Z0-9]", "", (value or "").strip())


def parse_sector_filters(text: str) -> list[str]:
    """Converte texto do utilizador em lista de códigos/prefixos."""
    if not text or not text.strip():
        return []
    parts = re.split(r"[,;\n]+", text)
    codes: list[str] = []
    seen: set[str] = set()
    for part in parts:
        code = normalize_sector_code(part)
        if code and code not in seen:
            seen.add(code)
            codes.append(code)
    return codes


def matches_sector(record_sector: str, filter_text: str) -> bool:
    """
    Verifica se o setor do registo corresponde ao filtro.
    Suporta múltiplos códigos e correspondência por prefixo.
    """
    filters = parse_sector_filters(filter_text)
    if not filters:
        return True

    sector = normalize_sector_code(record_sector)
    if not sector:
        return False

    for code in filters:
        if sector == code or sector.startswith(code) or code.startswith(sector):
            return True
    return False


def get_sector_label(country: str) -> str:
    return SECTOR_LABELS.get(country, SECTOR_LABELS["OUTRO"])


def get_sector_placeholder(country: str) -> str:
    return SECTOR_PLACEHOLDERS.get(country, SECTOR_PLACEHOLDERS["OUTRO"])


def get_sector_hint(country: str) -> str:
    return SECTOR_HINTS.get(country, SECTOR_HINTS["OUTRO"])
