#!/usr/bin/env python3
"""Ponto de entrada para o executável Windows (PyInstaller)."""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path
from threading import Timer


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def get_data_dir() -> Path:
    """Pasta persistente para bases de dados exportadas pelo utilizador."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    data = base / "CompanyEmailExtractor"
    data.mkdir(parents=True, exist_ok=True)
    return data


def main() -> None:
    app_dir = get_app_dir()
    app_path = app_dir / "app.py"

    if not app_path.exists():
        app_path = Path(__file__).resolve().parent / "app.py"

    os.chdir(app_dir)
    os.environ.setdefault("BROWSER", "default")

    # Abrir browser automaticamente após arranque
    def open_browser() -> None:
        webbrowser.open("http://localhost:8501")

    Timer(2.5, open_browser).start()

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.port=8501",
        "--server.address=localhost",
    ]

    from streamlit.web import cli as stcli

    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
