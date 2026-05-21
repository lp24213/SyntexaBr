# Limpeza segura do sistema Windows - NAO apaga arquivos essenciais
$ErrorActionPreference = "SilentlyContinue"
$VerbosePreference = "Continue"

function Get-FreeSpaceGB {
    try { return [math]::Round((Get-PSDrive C -ErrorAction Stop).Free / 1GB, 2) } catch { return $null }
}

$before = Get-FreeSpaceGB
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LIMPEZA SEGURA DO SISTEMA" -ForegroundColor Cyan
Write-Host "  C: livre antes: ~$before GB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Limpar TEMP do usuario (arquivos com mais de 1 dia para evitar conflitos)
$tempPaths = @($env:TEMP, (Join-Path $env:LOCALAPPDATA "Temp"), $env:TMP) | Select-Object -Unique
foreach ($tp in $tempPaths) {
    if (-not (Test-Path $tp)) { continue }
    Write-Host "[TEMP] Limpando arquivos antigos em: $tp" -ForegroundColor DarkGray
    Get-ChildItem -Path $tp -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) -and -not $_.PSIsContainer } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    # Remove pastas vazias
    Get-ChildItem -Path $tp -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) } |
        ForEach-Object {
            try { Remove-Item $_.FullName -Recurse -Force -ErrorAction Stop } catch {}
        }
}

# 2. Limpar Prefetch (arquivos nao usados ha mais de 30 dias)
$prefetch = "C:\Windows\Prefetch"
if (Test-Path $prefetch) {
    Write-Host "[PREFETCH] Limpando arquivos antigos..." -ForegroundColor DarkGray
    Get-ChildItem -Path $prefetch -Filter "*.pf" -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# 3. Limpar Windows Update Downloads (SEGURO - apenas downloads pendentes)
$wuDownload = "C:\Windows\SoftwareDistribution\Download"
if (Test-Path $wuDownload) {
    Write-Host "[WINDOWS UPDATE] Limpando downloads pendentes..." -ForegroundColor DarkGray
    Get-ChildItem -Path $wuDownload -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# 4. Limpar caches de desenvolvimento comuns
$devCaches = @(
    "$env:LOCALAPPDATA\npm-cache",
    "$env:LOCALAPPDATA\Yarn\Cache",
    "$env:LOCALAPPDATA\pip\Cache",
    "$env:LOCALAPPDATA\electron\Cache",
    "$env:LOCALAPPDATA\electron-builder\Cache"
)
foreach ($dc in $devCaches) {
    if (Test-Path $dc) {
        Write-Host "[DEV CACHE] Limpando: $dc" -ForegroundColor DarkGray
        Remove-Item -Path "$dc\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 5. Limpar cache do Docker Desktop (se existir)
$dockerCache = "$env:LOCALAPPDATA\Docker"
if (Test-Path $dockerCache) {
    Write-Host "[DOCKER] Limpando cache de build..." -ForegroundColor DarkGray
    # Nao remove dados de volumes/containers, apenas cache de build
    $builderCache = Join-Path $dockerCache "buildx"
    if (Test-Path $builderCache) {
        Remove-Item -Path "$builderCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 6. Limpar Lixeira
Write-Host "[LIXEIRA] Esvaziando..." -ForegroundColor DarkGray
$shell = New-Object -ComObject Shell.Application
$recycleBin = $shell.Namespace(0xA)
$recycleBin.Items() | ForEach-Object { Remove-Item $_.Path -Recurse -Force -ErrorAction SilentlyContinue }

# 7. Flush DNS cache
Write-Host "[DNS] Limpando cache DNS..." -ForegroundColor DarkGray
ipconfig /flushdns | Out-Null

# 8. Executar limpeza de caches do projeto Syntexa
$projectClean = Join-Path $PSScriptRoot "clean-local-caches.ps1"
if (Test-Path $projectClean) {
    Write-Host "[PROJETO] Executando clean-local-caches.ps1..." -ForegroundColor DarkGray
    & $projectClean
}

# 9. Limpar arquivos de log antigos do IIS/ASP.NET se existirem (com cuidado)
$aspNetTemp = "$env:LOCALAPPDATA\Temp\Temporary ASP.NET Files"
if (Test-Path $aspNetTemp) {
    Write-Host "[ASP.NET] Limpando temporarios..." -ForegroundColor DarkGray
    Get-ChildItem -Path $aspNetTemp -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

$after = Get-FreeSpaceGB
Write-Host "========================================" -ForegroundColor Green
Write-Host "  LIMPEZA CONCLUIDA" -ForegroundColor Green
Write-Host "  C: livre antes: ~$before GB" -ForegroundColor Green
Write-Host "  C: livre depois: ~$after GB" -ForegroundColor Green
if ($before -and $after) {
    $diff = [math]::Round($after - $before, 2)
    Write-Host "  ESPACO LIBERADO: ~$diff GB" -ForegroundColor Green
}
Write-Host "========================================" -ForegroundColor Green
