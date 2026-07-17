# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — gera executável Windows do Company Email Extractor."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None
root = Path(SPEC).parent

# Recolher todos os ficheiros do Streamlit e dependências
streamlit_datas, streamlit_binaries, streamlit_hidden = collect_all("streamlit")
pandas_hidden = collect_submodules("pandas")
pkg_datas = [
    (str(root / "app.py"), "."),
    (str(root / "cnpj_extractor"), "cnpj_extractor"),
]

a = Analysis(
    [str(root / "launcher.py")],
    pathex=[str(root)],
    binaries=streamlit_binaries,
    datas=streamlit_datas + pkg_datas,
    hiddenimports=[
        *streamlit_hidden,
        *pandas_hidden,
        "streamlit.web.cli",
        "streamlit.runtime.scriptrunner.magic_funcs",
        "click",
        "altair",
        "pyarrow",
        "tornado",
        "watchdog",
        "git",
        "pydeck",
        "PIL",
        "lxml",
        "lxml.etree",
        "bs4",
        "cnpj_extractor",
        "cnpj_extractor.cli",
        "cnpj_extractor.database",
        "cnpj_extractor.sitemap",
        "cnpj_extractor.sources",
        "cnpj_extractor.sources.fiz_portugal",
        "cnpj_extractor.sources.sitemap_generic",
        "cnpj_extractor.sources.receita_federal",
        "cnpj_extractor.sources.dadosbrasil_api",
        "cnpj_extractor.sources.dadosbrasil_scraper",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CompanyEmailExtractor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CompanyEmailExtractor",
)
