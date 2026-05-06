# Limpeza rapida de temporarios (sem varrer tamanho = sem demora de "um ano")
# Isto liberta DISCO (disco rígido), nao "memoria" RAM. Apps a correr: feche o Chrome/Edge se quiser esvaziar cache de browser.
# Executar: powershell -ExecutionPolicy Bypass -File scripts\limpeza-temp-c-rapida.ps1
# Para C:\Windows\Temp: abra o PowerShell "Executar como administrador" e volte a correr.
$ErrorActionPreference = "SilentlyContinue"
function Free-Bytes { param($p) try { (Get-PSDrive $p[0] -ErrorAction Stop).Free } catch { 0 } }
$before = Free-Bytes "C"
Write-Host "C: ~livre ANTES: $([math]::Round($before/1GB,2)) GB" -ForegroundColor Cyan

# 1) Lixeira (ficheiros "apagados" ainda la dentro)
try { Clear-RecycleBin -DriveLetter C -Force } catch { Clear-RecycleBin -Force -ErrorAction SilentlyContinue }
Write-Host "[ok] Lixeira C:" -ForegroundColor DarkGray

# 2) Temps de utilizador (evita Get-ChildItem em pastas com milhoes de ficheiros: usa cmd)
$UserTemps = @(
  $env:TEMP
  (Join-Path $env:LOCALAPPDATA "Temp")
  (Join-Path $env:USERPROFILE "AppData\Local\Temp")
  (Join-Path $env:LOCALAPPDATA "D3DSCache")
)
foreach ($d in $UserTemps) {
  if (Test-Path -LiteralPath $d) {
    cmd /c "rd /s /q `"$d`" 2>nul"
    New-Item -ItemType Directory -Path $d -Force -ErrorAction SilentlyContinue | Out-Null
  }
}
# INetCache: pastas a parte (travam menos com apagar o interior)
$inet = (Join-Path $env:USERPROFILE "AppData\Local\Microsoft\Windows\INetCache")
if (Test-Path -LiteralPath $inet) { cmd /c "rd /s /q `"$inet`" 2>nul"; New-Item -ItemType Directory -Path $inet -Force -ErrorAction SilentlyContinue | Out-Null }
Write-Host "[ok] Temps de utilizador + INetCache" -ForegroundColor DarkGray

# 3) C:\Windows\Temp (se nao tiver permissoes, a maior parte fica; normal)
$WinTemp = "C:\Windows\Temp"
if (Test-Path -LiteralPath $WinTemp) {
  $n = 0
  Get-ChildItem -LiteralPath $WinTemp -Force -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $n++
  }
  Write-Host "[ok] Windows\Temp (tentou $n itens; faltou admin? restam trancados)" -ForegroundColor DarkGray
}

# 4) Caches de build / dev (grandes) — so pastas conhecidas, sem "Calcular tamanho"
$DevCaches = @(
  "$env:LOCALAPPDATA\electron-builder\Cache"
  "$env:LOCALAPPDATA\electron\Cache"
  "$env:LOCALAPPDATA\npm-cache"
  (Join-Path $PSScriptRoot "..\frontend\node_modules\.cache")
  (Join-Path $PSScriptRoot "..\frontend\.next\cache")
  (Join-Path $PSScriptRoot "..\.next")
  (Join-Path $PSScriptRoot "..\desktop\dist")
)
foreach ($c in $DevCaches) {
  if (Test-Path -LiteralPath $c) { Remove-Item -LiteralPath $c -Recurse -Force -ErrorAction SilentlyContinue }
}
# Partials electron
Get-ChildItem -Path $env:LOCALAPPDATA\electron, $env:LOCALAPPDATA\electron-builder -Filter "*.part*" -Recurse -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }
Write-Host "[ok] Caches electron / npm-frontend / .next" -ForegroundColor DarkGray

# 5) Temp root e padroes Syntexa
foreach ($root in @($env:TEMP, (Join-Path $env:LOCALAPPDATA "Temp"))) {
  if (-not (Test-Path $root)) { continue }
  foreach ($pat in @("syntexa-*", "Syntexa*")) {
    Get-ChildItem -LiteralPath $root -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
      Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}
Remove-Item -LiteralPath (Join-Path $env:TEMP "syntexa-deploy.tar.gz") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path (Split-Path $PSScriptRoot -Parent) "syntexa-deploy.tar.gz") -Force -ErrorAction SilentlyContinue

# npm global cache (pode ser grande)
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if ($npm) { cmd /c "npm cache clean --force" 2>$null }
$pip = Get-Command pip -ErrorAction SilentlyContinue
if ($pip) { & $pip.Source cache purge 2>$null }
Write-Host "[ok] npm/pip cache" -ForegroundColor DarkGray

$after = Free-Bytes "C"
Write-Host "C: ~livre DEPOIS: $([math]::Round($after/1GB,2)) GB" -ForegroundColor Green
$delta = $after - $before
if ($delta -gt 0) { Write-Host "Ganho aprox.: +$([math]::Round($delta/1GB,2)) GB" -ForegroundColor Green }
Write-Host ""
Write-Host "Se ainda faltar espaco: Definicoes do Windows > Sistema > Armazenamento > Ficheiros temporarios (ali limpa o que o SO permite)." -ForegroundColor Yellow
Write-Host "Ficheiros de apps apagados a pesar: muitas vezes e Lixeira, WinSxS, ou ponto de restauracao; nao basta apagar a pasta de Programas." -ForegroundColor Yellow
