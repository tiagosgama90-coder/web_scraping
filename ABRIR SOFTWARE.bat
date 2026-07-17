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

set "PATH=%~dp0runtime\python;%~dp0runtime\python\Scripts;%PATH%"
set "PYTHONPATH=%~dp0"

start "" runtime\python\pythonw.exe desktop_app.py 2>nul
if errorlevel 1 (
    runtime\python\python.exe desktop_app.py
)
