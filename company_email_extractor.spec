# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — aplicação desktop nativa Windows (sem browser)."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None
root = Path(SPEC).parent

ctk_datas, ctk_binaries, ctk_hidden = collect_all("customtkinter")

a = Analysis(
    [str(root / "launcher.py")],
    pathex=[str(root)],
    binaries=ctk_binaries,
    datas=ctk_datas + [(str(root / "cnpj_extractor"), "cnpj_extractor")],
    hiddenimports=[
        *ctk_hidden,
        *collect_submodules("cnpj_extractor"),
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "lxml",
        "lxml.etree",
        "bs4",
        "pandas",
        "curl_cffi",
        "cloudscraper",
        "cnpj_extractor.antibot",
        "cnpj_extractor.browser_stealth",
        "playwright",
        "nodriver",
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["streamlit", "matplotlib", "scipy", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="CompanyEmailExtractor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
