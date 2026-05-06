param(
  [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $OutDir = "backups/disaster-recovery/$stamp"
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

Copy-Item "config/syntexa_model_registry.json" (Join-Path $OutDir "syntexa_model_registry.json") -Force
if (Test-Path "checkpoints") {
  Copy-Item "checkpoints" (Join-Path $OutDir "checkpoints") -Recurse -Force
}
if (Test-Path "dist/own-model-bundle") {
  Copy-Item "dist/own-model-bundle" (Join-Path $OutDir "own-model-bundle") -Recurse -Force
}
Write-Host "Backup DR criado em: $OutDir"
