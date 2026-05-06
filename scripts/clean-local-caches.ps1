# Limpa caches e temporarios (Windows) para liberar espaco. Nao apaga codigo fonte.
$ErrorActionPreference = "SilentlyContinue"
Write-Host "Limpeza de caches / temp (Syntexa)..." -ForegroundColor Cyan
$patterns = @("syntexa-*.tar.gz", "syntexa-*.7z", "syntexa-electron-*", "syntexa-frontend-*", "SyntexaAI-*-test-*.exe")
foreach ($root in @($env:TEMP, (Join-Path $env:LOCALAPPDATA "Temp"), $env:TMP)) {
  if (-not (Test-Path -LiteralPath $root)) { continue }
  foreach ($p in $patterns) {
    Get-ChildItem -LiteralPath $root -Filter $p -ErrorAction SilentlyContinue | ForEach-Object {
      Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}
$paths = @(
  (Join-Path $PSScriptRoot "..\frontend\node_modules\.cache"),
  "$env:LOCALAPPDATA\electron-builder\Cache",
  "$env:LOCALAPPDATA\electron\Cache",
  (Join-Path $PSScriptRoot "..\.next"),
  (Join-Path $PSScriptRoot "..\frontend\.next\cache")
)
foreach ($path in $paths) {
  if (Test-Path -LiteralPath $path) {
    Write-Host "  removendo: $path" -ForegroundColor DarkGray
    Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
  }
}
$fe = Join-Path $PSScriptRoot "..\frontend"
if (Test-Path -LiteralPath $fe) {
  Push-Location $fe
  cmd /c "npm cache clean --force" 2>$null
  Pop-Location
}
try { & pip cache purge 2>$null } catch {}
Remove-Item -LiteralPath (Join-Path $env:TEMP "syntexa-deploy.tar.gz") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path (Split-Path $PSScriptRoot -Parent) "syntexa-deploy.tar.gz") -Force -ErrorAction SilentlyContinue
Write-Host "Concluido." -ForegroundColor Green
try {
  $free = (Get-PSDrive C -ErrorAction Stop).Free
  Write-Host "C: livre: ~$([math]::Round($free/1GB,2)) GB" -ForegroundColor Green
} catch { }
