#!/usr/bin/env python3
"""Captura screenshot da janela principal para documentação."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cnpj_extractor.ip_check import IpInfo  # noqa: E402
from desktop_app import CompanyEmailApp  # noqa: E402

OUT = Path("/opt/cursor/artifacts/app-screenshot-v215.png")
OUT.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    app = CompanyEmailApp()
    app.tabview.set("📊 Extrair")

    real = IpInfo(
        ip="85.243.12.88",
        country="Portugal",
        country_code="PT",
        city="Lisboa",
        via_proxy=False,
    )
    hidden = IpInfo(
        ip="47.238.130.212",
        country="Germany",
        country_code="DE",
        city="Frankfurt",
        via_proxy=True,
    )
    app._apply_privacy_displays(real_ip=real, hidden_ip=hidden, system_status="READY")
    app.start_btn.configure(state="normal")
    app.preview_btn.configure(state="normal")
    app.stat_country.configure(text="PT")
    app.stat_status.configure(text="Pronto")

    app.update_idletasks()
    app.update()
    time.sleep(1.5)

    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = max(app.winfo_width(), 1200)
    h = max(app.winfo_height(), 760)
    geom = f"{x},{y},{w},{h}"
    subprocess.run(["scrot", "-a", geom, str(OUT)], check=True)
    print(f"Saved: {OUT}")
    app.destroy()


if __name__ == "__main__":
    main()
