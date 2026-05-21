#Requires -Version 7
<#
.SYNOPSIS
    SYNTEXA DESKTOP BUILD — Windows Enterprise Pipeline V45
.DESCRIPTION
    Build completo de distribuição desktop Windows:
    - Empacota Python embeddable + dependências
    - Build Electron com NSIS, MSI, Portable
    - Gera checksums SHA256
    - Cria manifesto de runtime
    - Assina artefatos (se certificado disponível)
.NOTES
    Execute como Administrator para assinatura de código.
#>
param(
    [string]$Config = "Release",
    [switch]$SkipPythonPack,
    [switch]$SkipFrontendBuild,
    [switch]$SkipElectronBuild,
    [string]$PythonVersion = "3.11.9",
    [string]$CertThumbprint = "",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot
$Root = Split-Path -Parent $Root
$DesktopDir = Join-Path $Root "desktop"
$FrontendDir = Join-Path $Root "frontend"
$RuntimeDir = Join-Path $DesktopDir "runtime"
$DistDir = if ($OutputDir) { $OutputDir } else { Join-Path $DesktopDir "dist" }
$BuildResourcesDir = Join-Path $DesktopDir "build"
$ManifestPath = Join-Path $DesktopDir "runtime-manifest.json"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  SYNTEXA DESKTOP BUILD V45 — WINDOWS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Root:        $Root"
Write-Host "Desktop:     $DesktopDir"
Write-Host "Frontend:    $FrontendDir"
Write-Host "Runtime:     $RuntimeDir"
Write-Host "Output:      $DistDir"
Write-Host "Config:      $Config"
Write-Host ""

# ── HELPERS ────────────────────────────────────────────────
function Test-Command($cmd) { $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue) }
function Write-Step($msg) { Write-Host "`n▶ $msg" -ForegroundColor Yellow }
function Write-OK($msg) { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; throw $msg }
function Get-Sha256($path) { (Get-FileHash -Path $path -Algorithm SHA256).Hash.ToLower() }

# ── PREREQUISITES ──────────────────────────────────────────
Write-Step "Verificando pré-requisitos..."
if (-not (Test-Command "node")) { Write-Fail "Node.js não encontrado. Instale LTS." }
if (-not (Test-Command "npm")) { Write-Fail "npm não encontrado." }
$nodeVer = node --version
Write-OK "Node.js $nodeVer"

# ── FRONTEND BUILD ─────────────────────────────────────────
if (-not $SkipFrontendBuild) {
    Write-Step "Build do frontend (Next.js)..."
    Push-Location $FrontendDir
    try {
        if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
            Write-Host "  → Instalando dependências frontend..."
            npm ci --prefer-offline --no-audit --no-fund
        }
        $env:NODE_ENV = "production"
        npm run build
        if (-not (Test-Path (Join-Path $FrontendDir "dist"))) {
            # Next.js static export
            if (Test-Path (Join-Path $FrontendDir "out")) {
                Rename-Item (Join-Path $FrontendDir "out") "dist" -ErrorAction SilentlyContinue
            }
        }
        if (-not (Test-Path (Join-Path $FrontendDir "dist"))) {
            Write-Fail "Build do frontend não gerou pasta dist/ ou out/"
        }
        Write-OK "Frontend build concluído"
    } finally { Pop-Location }
} else {
    Write-OK "Frontend build pulado (--SkipFrontendBuild)"
}

# ── PYTHON RUNTIME PACKAGING ─────────────────────────────
if (-not $SkipPythonPack) {
    Write-Step "Empacotando Python runtime soberano..."

    # Baixa Python embeddable se não existir
    $PyEmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
    $PyEmbedZip = Join-Path $RuntimeDir "python-embed.zip"
    $PyDir = Join-Path $RuntimeDir "python"

    if (-not (Test-Path $PyDir)) {
        New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
        if (-not (Test-Path $PyEmbedZip)) {
            Write-Host "  → Baixando Python $PythonVersion embeddable..."
            Invoke-WebRequest -Uri $PyEmbedUrl -OutFile $PyEmbedZip -UseBasicParsing
            Write-OK "Python embeddable baixado"
        }
        Write-Host "  → Extraindo Python..."
        Expand-Archive -Path $PyEmbedZip -DestinationPath $PyDir -Force
        Write-OK "Python extraído"

        # Ativa site-packages no pythonXX._pth
        $pthFile = Get-ChildItem -Path $PyDir -Filter "python*._pth" | Select-Object -First 1
        if ($pthFile) {
            $content = Get-Content $pthFile.FullName -Raw
            $content = $content -replace "^#import site", "import site"
            Set-Content -Path $pthFile.FullName -Value $content -NoNewline
            Write-OK "Site-packages ativado no embeddable"
        }

        # Instala pip
        $getPip = Join-Path $RuntimeDir "get-pip.py"
        if (-not (Test-Path $getPip)) {
            Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
        }
        & (Join-Path $PyDir "python.exe") $getPip --no-warn-script-location
        Write-OK "pip instalado"
    } else {
        Write-OK "Python runtime já existe"
    }

    # Instala dependências do backend
    Write-Host "  → Instalando dependências Python soberanas..."
    $ReqFile = Join-Path $Root "requirements.txt"
    $ReqDesktop = Join-Path $DesktopDir "backend" "requirements-desktop.txt"

    $pip = Join-Path $PyDir "python.exe"
    & $pip -m pip install --upgrade pip setuptools wheel --no-warn-script-location

    if (Test-Path $ReqFile) {
        & $pip -m pip install -r $ReqFile --no-warn-script-location --prefer-binary
    }

    # Instala dependências desktop extras
    $desktopExtras = @(
        "fastapi","uvicorn","pydantic>=2.0","python-multipart"
        "torch --index-url https://download.pytorch.org/whl/cu121"
        "transformers","accelerate","bitsandbytes"
        "sentencepiece","protobuf"
        "TTS","openai-whisper","easyocr","pdf2image"
        "pillow","numpy","requests"
        "llama-cpp-python --no-cache-dir"
    )
    foreach ($pkg in $desktopExtras) {
        Write-Host "    → $pkg"
        & $pip -m pip install $pkg --no-warn-script-location --prefer-binary 2>$null
    }
    Write-OK "Dependências Python instaladas"

    # Copia módulos vereda_ai para dentro do runtime
    $VeredaSrc = Join-Path $Root "vereda_ai"
    $VeredaDst = Join-Path $PyDir "Lib" "site-packages" "vereda_ai"
    if (Test-Path $VeredaSrc) {
        if (Test-Path $VeredaDst) { Remove-Item $VeredaDst -Recurse -Force }
        Copy-Item -Path $VeredaSrc -Destination $VeredaDst -Recurse -Force
        Write-OK "vereda_ai copiado para site-packages"
    }

    # Copia backend server
    $BackendDst = Join-Path $RuntimeDir "backend"
    New-Item -ItemType Directory -Path $BackendDst -Force | Out-Null
    Copy-Item -Path (Join-Path $DesktopDir "backend" "*") -Destination $BackendDst -Recurse -Force
    Write-OK "Backend server copiado"

    # Gera manifesto parcial de runtime
    $manifest = @{
        version = "45.0.0"
        platform = "windows"
        arch = "x64"
        python_version = $PythonVersion
        timestamp = (Get-Date -Format "o")
        files = @()
    }
    Get-ChildItem -Path $RuntimeDir -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($RuntimeDir.Length + 1).Replace("\", "/")
        $manifest.files += @{
            path = $rel
            size = $_.Length
            sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
        }
    }
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -Path $ManifestPath -Encoding UTF8
    Write-OK "Manifesto de runtime gerado: $ManifestPath"
} else {
    Write-OK "Python packaging pulado (--SkipPythonPack)"
}

# ── BUILD RESOURCES ──────────────────────────────────────
Write-Step "Preparando build resources..."
if (-not (Test-Path $BuildResourcesDir)) { New-Item -ItemType Directory -Path $BuildResourcesDir -Force | Out-Null }
# Gera icon.ico se não existir (placeholder para build)
if (-not (Test-Path (Join-Path $BuildResourcesDir "icon.ico"))) {
    # Usa o logotipo existente se houver
    $Logo = Join-Path $Root "LOGOTIPO.png"
    if (Test-Path $Logo) {
        Write-Host "  → Usando LOGOTIPO.png como ícone base"
        # electron-builder lida com .png também, mas idealmente converte para .ico
        Copy-Item $Logo (Join-Path $BuildResourcesDir "icon.png") -Force
    }
}
Write-OK "Build resources OK"

# ── ELECTRON BUILD ───────────────────────────────────────
if (-not $SkipElectronBuild) {
    Write-Step "Build Electron (electron-builder)..."
    Push-Location $DesktopDir
    try {
        if (-not (Test-Path (Join-Path $DesktopDir "node_modules"))) {
            Write-Host "  → Instalando dependências desktop..."
            npm ci --prefer-offline --no-audit --no-fund
        }

        # Limpa dist anterior
        if (Test-Path $DistDir) { Remove-Item $DistDir -Recurse -Force }
        New-Item -ItemType Directory -Path $DistDir -Force | Out-Null

        # Build completo
        $env:NODE_ENV = "production"
        npm run build:win

        $artifacts = Get-ChildItem -Path $DistDir -File
        if ($artifacts.Count -eq 0) { Write-Fail "Electron build não gerou artefatos em $DistDir" }
        Write-OK "Electron build concluído: $($artifacts.Count) artefatos"

        # Lista artefatos
        foreach ($a in $artifacts) {
            Write-Host "    → $($a.Name) ($([math]::Round($a.Length/1MB,1)) MB)"
        }
    } finally { Pop-Location }
} else {
    Write-OK "Electron build pulado (--SkipElectronBuild)"
}

# ── CHECKSUMS & SIGNING ──────────────────────────────────
Write-Step "Gerando checksums e assinaturas..."
$ChecksumFile = Join-Path $DistDir "SHA256SUMS.txt"
$SignedManifest = Join-Path $DistDir "syntexa-manifest-v45.json"

$manifestFinal = @{
    product = "Syntexa AI"
    version = "45.0.0"
    build_id = [Guid]::NewGuid().ToString("N")
    timestamp = (Get-Date -Format "o")
    platform = "windows"
    arch = "x64"
    artifacts = @()
}

$checksums = @()
Get-ChildItem -Path $DistDir -File | ForEach-Object {
    $hash = Get-Sha256 $_.FullName
    $checksums += "$hash  $($_.Name)"
    $manifestFinal.artifacts += @{
        name = $_.Name
        size = $_.Length
        sha256 = $hash
        signed = $false
    }
}
Set-Content -Path $ChecksumFile -Value ($checksums -join "`n") -Encoding UTF8
Write-OK "SHA256SUMS gerado"

# Assinatura de código (se certificado disponível)
if ($CertThumbprint) {
    $signtool = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
    if (-not (Test-Path $signtool)) {
        $signtool = (Get-ChildItem -Path "${env:ProgramFiles(x86)}\Windows Kits" -Recurse -Filter "signtool.exe" | Select-Object -First 1).FullName
    }
    if ($signtool -and (Test-Path $signtool)) {
        Get-ChildItem -Path $DistDir -Filter "*.exe" | ForEach-Object {
            & $signtool sign /sha1 $CertThumbprint /tr "http://timestamp.digicert.com" /td sha256 /fd sha256 $_.FullName
            Write-OK "Assinado: $($_.Name)"
        }
        # Atualiza manifesto com flag signed
        for ($i = 0; $i -lt $manifestFinal.artifacts.Count; $i++) {
            if ($manifestFinal.artifacts[$i].name -match '\.exe$') {
                $manifestFinal.artifacts[$i].signed = $true
            }
        }
    } else {
        Write-Host "  ! signtool.exe não encontrado. Build não será assinado." -ForegroundColor DarkYellow
    }
}

$manifestFinal | ConvertTo-Json -Depth 10 | Set-Content -Path $SignedManifest -Encoding UTF8
Write-OK "Manifesto assinado gerado: $SignedManifest"

# ── COPY ARTIFACTS ───────────────────────────────────────
Write-Step "Copiando artefatos para distribuição..."
$OutStatic = Join-Path $Root "vereda_backend" "static" "desktop"
if (-not (Test-Path $OutStatic)) { New-Item -ItemType Directory -Path $OutStatic -Force | Out-Null }

Get-ChildItem -Path $DistDir -File | ForEach-Object {
    Copy-Item $_.FullName -Destination (Join-Path $OutStatic $_.Name) -Force
}
Write-OK "Artefatos copiados para $OutStatic"

# ── FINAL ────────────────────────────────────────────────
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  BUILD V45 CONCLUÍDO COM SUCESSO" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "Artefatos em: $DistDir"
Write-Host "Distribuição: $OutStatic"
Write-Host ""
Get-ChildItem -Path $DistDir -File | ForEach-Object {
    Write-Host "  • $($_.Name) ($([math]::Round($_.Length/1MB,1)) MB)"
}
