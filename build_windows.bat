@echo off
chcp 65001 >nul
title Company Email Extractor - Build
cd /d "%~dp0"

echo.
echo  ========================================================
echo   A gerar executavel Windows NATIVO (sem browser)...
echo  ========================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.10+ de python.org
    pause
    exit /b 1
)

python -m pip install -r requirements.txt -r requirements-build.txt --quiet
python -m PyInstaller company_email_extractor.spec --noconfirm

if errorlevel 1 (
    echo [ERRO] Build falhou.
    pause
    exit /b 1
)

echo.
echo  Executavel criado: dist\CompanyEmailExtractor.exe
echo.
echo  Para criar instalador Setup (.exe):
echo    1. Instale Inno Setup: https://jrsoftware.org/isinfo.php
echo    2. Abra installer\setup.iss e compile
echo.
pause
