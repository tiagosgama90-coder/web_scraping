# Company Email Extractor - Instalador automatico Windows
# Instala Python portatil + dependencias sem mexer no sistema

$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $AppDir "runtime"
$PythonDir = Join-Path $RuntimeDir "python"
$PythonZip = Join-Path $RuntimeDir "python-embed.zip"
$PythonExe = Join-Path $PythonDir "python.exe"
$GetPip = Join-Path $RuntimeDir "get-pip.py"
$PythonVersion = "3.12.7"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$SitePackages = Join-Path $PythonDir "Lib\site-packages"

function Write-Step($msg) {
    Write-Host "  >> $msg" -ForegroundColor Cyan
}

Write-Host ""
Write-Step "A preparar instalacao em: $AppDir"

# 1. Descarregar Python portatil (embeddable)
if (-not (Test-Path $PythonExe)) {
    Write-Step "A descarregar Python $PythonVersion portatil (~25 MB)..."
    New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
    New-Item -ItemType Directory -Force -Path $PythonDir | Out-Null

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonZip -UseBasicParsing
    Expand-Archive -Path $PythonZip -DestinationPath $PythonDir -Force
    Remove-Item $PythonZip -Force

    # Activar site-packages no Python embeddable
    $pthFile = Get-ChildItem -Path $PythonDir -Filter "python*._pth" | Select-Object -First 1
    if ($pthFile) {
        $content = Get-Content $pthFile.FullName -Raw
        $content = $content -replace "#import site", "import site"
        if ($content -notmatch "Lib\\site-packages") {
            $content += "`nLib\site-packages`n"
        }
        Set-Content -Path $pthFile.FullName -Value $content -Encoding UTF8
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $PythonDir "Lib\site-packages") | Out-Null
    Write-Step "Python portatil instalado."
} else {
    Write-Step "Python portatil ja existe."
}

# 2. Instalar pip
if (-not (Test-Path (Join-Path $PythonDir "Scripts\pip.exe"))) {
    Write-Step "A instalar pip..."
    Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPip -UseBasicParsing
    & $PythonExe $GetPip --no-warn-script-location 2>&1 | Out-Null
    Remove-Item $GetPip -Force -ErrorAction SilentlyContinue
    Write-Step "pip instalado."
}

$PipExe = Join-Path $PythonDir "Scripts\pip.exe"
$env:PATH = "$PythonDir;$PythonDir\Scripts;$env:PATH"

# 3. Instalar dependencias do projeto
Write-Step "A instalar dependencias do software (pode demorar 3-7 minutos)..."
$ReqFile = Join-Path $AppDir "requirements.txt"
& $PipExe install --upgrade pip --quiet 2>&1 | Out-Null
& $PipExe install -r $ReqFile --quiet --no-warn-script-location
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERRO] Falha ao instalar dependencias." -ForegroundColor Red
    exit 1
}
Write-Step "Dependencias instaladas."

# 3b. Instalar browser Playwright para modo anti-bot (opcional mas recomendado)
Write-Step "A instalar browser para modo anti-bot (Chromium)..."
$PythonW = Join-Path $PythonDir "python.exe"
& $PythonW -m playwright install chromium 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Step "Browser anti-bot instalado."
} else {
    Write-Host "  [AVISO] Playwright nao instalado - modo anti-bot basico apenas." -ForegroundColor Yellow
}

# 4. Criar atalho no ambiente de trabalho
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Company Email Extractor.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $AppDir "ABRIR SOFTWARE.bat"
$Shortcut.WorkingDirectory = $AppDir
$Shortcut.Description = "Extrator de emails - App nativo Windows (sem browser)"
$Shortcut.Save()
Write-Step "Atalho criado no Ambiente de Trabalho."

# 5. Marcar instalacao como concluida
$VersionFile = Join-Path $RuntimeDir "installed.txt"
Set-Content -Path $VersionFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Write-Host ""
Write-Host "  ========================================================" -ForegroundColor Green
Write-Host "   INSTALACAO CONCLUIDA COM SUCESSO!" -ForegroundColor Green
Write-Host "  ========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Para abrir o software:"
Write-Host "    - Duplo clique em: ABRIR SOFTWARE.bat"
Write-Host "    - Ou use o atalho no Ambiente de Trabalho"
Write-Host ""
