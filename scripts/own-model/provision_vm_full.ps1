param(
  [string]$Host = "",
  [string]$User = "root",
  [string]$KeyPath = "$HOME\.ssh\id_rsa"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Host)) {
  Write-Host "Uso: .\provision_vm_full.ps1 -Host <ip-ou-dominio> [-User root] [-KeyPath ...]"
  exit 1
}

$remote = @'
set -euo pipefail
cd /opt/syntexa
bash scripts/own-model/provision_vm_full.sh
'@

ssh -i $KeyPath "$User@$Host" $remote
