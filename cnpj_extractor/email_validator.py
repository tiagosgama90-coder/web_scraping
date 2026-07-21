from __future__ import annotations

import socket
import threading
from typing import Callable

from cnpj_extractor.utils import clean_and_validate_email, normalize_email

_mx_cache: dict[str, bool] = {}
_mx_lock = threading.Lock()


def domain_has_mx(domain: str, timeout: float = 4.0) -> bool:
    """Verifica se o domínio tem registos MX ou A (servidor de email)."""
    domain = (domain or "").strip().lower().rstrip(".")
    if not domain or "." not in domain:
        return False

    with _mx_lock:
        if domain in _mx_cache:
            return _mx_cache[domain]

    ok = _lookup_mx(domain, timeout)
    with _mx_lock:
        _mx_cache[domain] = ok
    return ok


def _lookup_mx(domain: str, timeout: float) -> bool:
    try:
        import dns.resolver

        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout
        answers = resolver.resolve(domain, "MX")
        if len(answers) > 0:
            return True
    except Exception:
        pass

    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(domain, 25, type=socket.SOCK_STREAM)
        return True
    except OSError:
        return False
    finally:
        socket.setdefaulttimeout(None)


def validate_email_full(
    value: str,
    *,
    check_mx: bool = False,
) -> tuple[str | None, str]:
    """
    Valida email em camadas.
    Retorna (email_limpo ou None, estado: ok|formato|mx_falhou).
    """
    email = clean_and_validate_email(value)
    if not email:
        return None, "formato"

    if not check_mx:
        return email, "ok"

    _, _, domain = email.partition("@")
    if domain_has_mx(domain):
        return email, "ok"
    return None, "mx_falhou"


def filter_records_with_mx(
    records: list[dict],
    *,
    check_mx: bool = True,
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[list[dict], dict[str, int]]:
    """Valida emails com DNS/MX — usa cache por domínio."""
    stats = {"ok": 0, "formato": 0, "mx_falhou": 0}
    result: list[dict] = []
    total = len(records)

    for index, record in enumerate(records):
        email, status = validate_email_full(record.get("email", ""), check_mx=check_mx)
        stats[status] = stats.get(status, 0) + 1
        if not email:
            continue
        row = dict(record)
        row["email"] = email
        result.append(row)
        if progress_callback and total and index % 50 == 0:
            progress_callback((index + 1) / total, f"MX {index + 1:,}/{total:,} — {len(result):,} válidos")

    if progress_callback:
        progress_callback(1.0, f"Validação MX: {len(result):,} emails com domínio ativo")

    return result, stats


def clear_mx_cache() -> None:
    with _mx_lock:
        _mx_cache.clear()
