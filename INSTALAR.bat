@echo off
chcp 65001 >nul
title Company Email Extractor - Instalador
color 0A

echo.
echo  ========================================================
echo   COMPANY EMAIL EXTRACTOR - Instalador Automatico
echo  Software NATIVO - janela propria, sem browser
echo  ========================================================
echo.

cd /d "%~dp0"

:: Executar instalador PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
    echo.
    echo  [ERRO] A instalacao falhou.
    pause
    exit /b 1
)

echo.
echo  Instalacao concluida!
echo  Podes agora usar: ABRIR SOFTWARE.bat
echo.
pause
