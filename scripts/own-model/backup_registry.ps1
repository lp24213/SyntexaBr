param(
  [string]$OutDir = "backups/own-model"
)

$ErrorActionPreference = "Stop"
$src = "config/syntexa_model_registry.json"
if (-not (Test-Path $src)) {
  Write-Error "Registry não encontrado: $src"
  exit 1
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dst = Join-Path $OutDir "syntexa_model_registry-$stamp.json"
Copy-Item $src $dst -Force
Write-Host "Backup criado: $dst"
