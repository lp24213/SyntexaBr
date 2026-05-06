param(
  [Parameter(Mandatory = $true)]
  [string]$BackupFile
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $BackupFile)) {
  Write-Error "Arquivo não encontrado: $BackupFile"
  exit 1
}
Copy-Item $BackupFile "config/syntexa_model_registry.json" -Force
Write-Host "Registry restaurado em config/syntexa_model_registry.json"
