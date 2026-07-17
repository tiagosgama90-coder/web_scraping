@echo off
chcp 65001 >nul
title Company Email Extractor - Build Windows
cd /d "%~dp0"

echo.
echo  ========================================================
echo   A gerar executavel Windows...
echo   (Requer Python instalado neste PC)
echo  ========================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.10+ de python.org
    pause
    exit /b 1
)

echo >> A instalar dependencias de build...
python -m pip install -r requirements.txt -r requirements-build.txt --quiet

echo >> A compilar executavel (pode demorar 5-10 minutos)...
python -m PyInstaller company_email_extractor.spec --noconfirm

if errorlevel 1 (
    echo [ERRO] Build falhou.
    pause
    exit /b 1
)

echo.
echo  ========================================================
echo   BUILD CONCLUIDO!
echo   Pasta: dist\CompanyEmailExtractor\
echo   Executavel: dist\CompanyEmailExtractor\CompanyEmailExtractor.exe
echo  ========================================================
echo.
echo  Copie a pasta inteira para outro PC Windows - funciona sem Python.
echo.
pause
