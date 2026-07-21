"""Formatação do painel HUD de privacidade — estilo rádio digital de carro."""

from __future__ import annotations

from cnpj_extractor.fingerprint_privacy import FingerprintProfile
from cnpj_extractor.ip_check import IpInfo

HUD_WIDTH = 54


def _pad(label: str, value: str, width: int = 18) -> str:
    label = label.upper()[:width].ljust(width)
    return f"  {label} {value}"


def _place(info: IpInfo | None) -> str:
    if not info:
        return "SCAN..."
    parts = []
    if info.city:
        parts.append(info.city)
    if info.country_code:
        parts.append(info.country_code)
    elif info.country:
        parts.append(info.country[:12])
    return " / ".join(parts) if parts else "?"


def format_privacy_hud(
    *,
    real_ip: IpInfo | None,
    hidden_ip: IpInfo | None,
    hide_ip_enabled: bool,
    fingerprint_enabled: bool,
    profile: FingerprintProfile | None,
    system_status: str = "READY",
) -> str:
    border = "═" * HUD_WIDTH
    thin = "─" * HUD_WIDTH

    lines = [
        f"╔{border}╗",
        f"║  PRIVACY HUD  │  SYS: {system_status[:28].ljust(28)}║",
        f"╠{border}╣",
    ]

    if real_ip:
        lines.append(_pad("IP REAL", f"{real_ip.ip}  [{_place(real_ip)}]") + " " * 8 + "║")
    else:
        lines.append(_pad("IP REAL", "A DETETAR...") + " " * 18 + "║")

    hide_state = "[ON ]" if hide_ip_enabled else "[OFF]"
    lines.append(_pad("HIDE IP", hide_state) + " " * 28 + "║")

    if hide_ip_enabled:
        if hidden_ip:
            lines.append(_pad("IP SITES", f"{hidden_ip.ip}  [{_place(hidden_ip)}]") + " " * 6 + "║")
            if real_ip and real_ip.ip != hidden_ip.ip:
                lines.append(_pad("STATUS", "IP OCULTO — OK") + " " * 22 + "║")
            elif real_ip:
                lines.append(_pad("STATUS", "AGUARDE PROXY...") + " " * 20 + "║")
            else:
                lines.append(_pad("STATUS", "CALIBRANDO...") + " " * 24 + "║")
        else:
            lines.append(_pad("IP SITES", "PROCURANDO SERVIDOR...") + " " * 10 + "║")
            lines.append(_pad("STATUS", "WARMUP...") + " " * 28 + "║")
    else:
        lines.append(_pad("IP SITES", "= IP REAL (sem mascara)") + " " * 14 + "║")
        lines.append(_pad("STATUS", "DIRECT MODE") + " " * 26 + "║")

    lines.append(f"╠{thin}╣")

    if fingerprint_enabled and profile:
        browser = "CHROME"
        if "Firefox" in profile.user_agent:
            browser = "FIREFOX"
        elif "Edg" in profile.user_agent:
            browser = "EDGE"
        elif "Safari" in profile.user_agent and "Chrome" not in profile.user_agent:
            browser = "SAFARI"
        lines.append(_pad("BROWSER", f"{browser} {profile.viewport_width}x{profile.viewport_height}") + " " * 8 + "║")
        lang = profile.accept_language.split(",")[0][:14]
        lines.append(_pad("IDIOMA", lang) + " " * 28 + "║")
        lines.append(_pad("PLATFORM", profile.platform) + " " * 28 + "║")
        lines.append(_pad("DIGITAL", "RANDOMIZADO") + " " * 24 + "║")
    else:
        lines.append(_pad("BROWSER", "PADRAO DO SISTEMA") + " " * 20 + "║")
        lines.append(_pad("DIGITAL", "DESATIVADO") + " " * 26 + "║")

    lines.append(f"╚{border}╝")
    lines.append("")
    lines.append("  MAC da placa NUNCA vai a internet — so IP e browser mudam.")

    return "\n".join(lines)
