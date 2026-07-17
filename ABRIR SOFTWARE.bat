@echo off
chcp 65001 >nul
title Company Email Extractor
cd /d "%~dp0"

if not exist "runtime\python\python.exe" (
    echo.
    echo  O software ainda nao foi instalado.
    echo  A executar instalador automatico...
    echo.
    call "%~dp0INSTALAR.bat"
    exit /b %errorlevel%
)

echo.
echo  ========================================================
echo   COMPANY EMAIL EXTRACTOR
echo   A abrir no browser... (http://localhost:8501)
echo   Para fechar: feche esta janela ou prima Ctrl+C
echo  ========================================================
echo.

set "PATH=%~dp0runtime\python;%~dp0runtime\python\Scripts;%PATH%"
set "PYTHONPATH=%~dp0"

runtime\python\python.exe -m streamlit run app.py ^
    --server.headless=true ^
    --browser.gatherUsageStats=false ^
    --server.port=8501

if errorlevel 1 (
    echo.
    echo  [ERRO] Nao foi possivel iniciar o software.
    pause
)
