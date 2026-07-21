@echo off
chcp 65001 >nul
title Company Email Extractor - Criar Setup.exe
cd /d "%~dp0\.."

echo.
echo  A gerar executavel...
call build_windows.bat
if errorlevel 1 exit /b 1

echo.
echo  A criar instalador Setup.exe (Inno Setup)...
where iscc >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    ) else (
        echo [ERRO] Inno Setup nao encontrado.
        echo Instale de: https://jrsoftware.org/isinfo.php
        pause
        exit /b 1
    )
) else (
    set ISCC=iscc
)

%ISCC% installer\setup.iss
if errorlevel 1 (
    echo [ERRO] Falha ao criar instalador.
    pause
    exit /b 1
)

echo.
echo  Instalador criado: dist\CompanyEmailExtractor-Setup.exe
echo.
pause
