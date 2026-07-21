from __future__ import annotations

import random
import secrets
import string
import threading
from dataclasses import dataclass

_lock = threading.Lock()
_masking_enabled = False
_rotate_each_request = False
_current_profile: FingerprintProfile | None = None


@dataclass
class FingerprintProfile:
    """Perfil digital aleatório — randomiza o que os sites conseguem ver no browser."""

    user_agent: str
    accept_language: str
    locale: str
    timezone_id: str
    viewport_width: int
    viewport_height: int
    platform: str
    fake_machine_id: str
    fake_mac_address: str
    fake_hostname: str


USER_AGENTS_POOL = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.2 Safari/605.1.15"
    ),
]

ACCEPT_LANGUAGES = [
    "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,pt;q=0.8",
    "es-ES,es;q=0.9,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "it-IT,it;q=0.9,en;q=0.8",
]

LOCALES = ["pt-PT", "en-US", "es-ES", "fr-FR", "de-DE", "it-IT"]
TIMEZONES = ["Europe/Lisbon", "Europe/London", "Europe/Madrid", "Europe/Paris", "Europe/Berlin"]
PLATFORMS = ["Win32", "MacIntel", "Linux x86_64"]
HOSTNAME_PREFIXES = ["DESKTOP", "LAPTOP", "PC", "WORKSTATION", "NB"]


def _random_mac() -> str:
    """Gera MAC aleatório (formato localmente administrado)."""
    octets = [random.randint(0, 255) for _ in range(6)]
    octets[0] = (octets[0] | 0x02) & 0xFE  # locally administered, unicast
    return ":".join(f"{b:02X}" for b in octets)


def _random_machine_id() -> str:
    return secrets.token_hex(16).upper()


def _random_hostname() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=7))
    return f"{random.choice(HOSTNAME_PREFIXES)}-{suffix}"


def generate_fingerprint_profile() -> FingerprintProfile:
    width = random.choice([1280, 1366, 1440, 1536, 1920])
    height = random.choice([720, 768, 800, 864, 900, 1080])
    return FingerprintProfile(
        user_agent=random.choice(USER_AGENTS_POOL),
        accept_language=random.choice(ACCEPT_LANGUAGES),
        locale=random.choice(LOCALES),
        timezone_id=random.choice(TIMEZONES),
        viewport_width=width,
        viewport_height=height,
        platform=random.choice(PLATFORMS),
        fake_machine_id=_random_machine_id(),
        fake_mac_address=_random_mac(),
        fake_hostname=_random_hostname(),
    )


def set_fingerprint_masking(enabled: bool, *, rotate_each_request: bool = True) -> FingerprintProfile | None:
    global _masking_enabled, _rotate_each_request, _current_profile
    with _lock:
        _masking_enabled = enabled
        _rotate_each_request = rotate_each_request
        if enabled:
            _current_profile = generate_fingerprint_profile()
            return _current_profile
        _current_profile = None
        return None


def clear_fingerprint_masking() -> None:
    set_fingerprint_masking(False)


def is_fingerprint_masking_enabled() -> bool:
    with _lock:
        return _masking_enabled


def get_fingerprint_profile(*, rotate: bool = False) -> FingerprintProfile | None:
    global _current_profile
    with _lock:
        if not _masking_enabled:
            return None
        if rotate or _rotate_each_request or _current_profile is None:
            _current_profile = generate_fingerprint_profile()
        return _current_profile


def profile_summary(profile: FingerprintProfile) -> str:
    return (
        f"ID máquina (falso): {profile.fake_machine_id[:12]}… | "
        f"MAC (falso): {profile.fake_mac_address} | "
        f"Host (falso): {profile.fake_hostname}"
    )


def playwright_stealth_script(profile: FingerprintProfile) -> str:
    return f"""
Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
Object.defineProperty(navigator, 'platform', {{get: () => '{profile.platform}'}});
Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {random.choice([4, 6, 8, 12, 16])}}});
"""
