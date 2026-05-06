#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy backend em todos os nós em config/syntexa-prod-nodes.txt, valida health + download desktop em cada IP, limpa caches/build locais.

.DESCRIPTION
  Replica a lógica de scripts/deploy-backend-bash.sh (tar -> scp -> remote_deploy_back.sh) para cada host.
  Validação: HTTPS com SNI forçado por IP (--resolve) para testar cada VM sem depender só do DNS round-robin.

.PARAMETER SkipDeploy
  Só validar e limpar (não gera tarball nem envia).

.PARAMETER SkipClean
  Não remove .next/out/dist/temp local.

.PARAMETER StartAzureVMs
  Tenta ligar as VMs do resource group SYNTEXABR-RG (requer az CLI logado).

.PARAMETER SyncDesktopArtifacts
  Copia vereda_backend/static/desktop/*.exe e *.tar.gz para cada nó (mantém downloads alinhados ao build local).

.EXAMPLE
  cd <repo>
  .\scripts\prod-two-nodes-deploy-validate-clean.ps1

.EXAMPLE
  .\scripts\prod-two-nodes-deploy-validate-clean.ps1 -StartAzureVMs -SyncDesktopArtifacts
#>
[CmdletBinding()]
param(
  [string] $RepoRoot = "",
  [string] $NodesFile = "",
  [string] $RemoteUser = "azureuser",
  [string] $RemoteBase = "/opt/syntexa",
  [string] $SshKey = "",
  [string] $PublicApiHost = "api.syntexabr.com.br",
  [string] $AzureResourceGroup = "SYNTEXABR-RG",
  [string[]] $AzureVmNames = @("Syntexabr", "Syntexabr-api-we"),
  [switch] $SkipDeploy,
  [switch] $SkipClean,
  [switch] $StartAzureVMs,
  [switch] $SyncDesktopArtifacts
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  param([string] $Hint)
  if ($Hint -and (Test-Path $Hint)) { return (Resolve-Path $Hint).Path }
  $here = $PSScriptRoot
  return (Resolve-Path (Join-Path $here "..")).Path
}

function Get-SshKeyPath {
  param([string] $Explicit)
  if ($Explicit -and (Test-Path $Explicit)) { return $Explicit }
  $envKey = $env:SYNTEXA_SSH_KEY
  if ($envKey -and (Test-Path $envKey)) { return $envKey }
  $ed = Join-Path $env:USERPROFILE ".ssh\id_ed25519"
  if (Test-Path $ed) { return $ed }
  $rsa = Join-Path $env:USERPROFILE ".ssh\id_rsa"
  if (Test-Path $rsa) { return $rsa }
  throw "Chave SSH não encontrada. Defina SYNTEXA_SSH_KEY ou coloque id_ed25519/id_rsa em ~/.ssh"
}

function Read-ProdNodes {
  param([string] $Path)
  if (-not (Test-Path $Path)) { throw "Ficheiro de nós não encontrado: $Path" }
  $lines = Get-Content -Path $Path -Encoding UTF8
  $out = @()
  foreach ($line in $lines) {
    $t = $line.Trim()
    if (-not $t -or $t.StartsWith("#")) { continue }
    $t = $t -replace "`r", ""
    $out += $t
  }
  if ($out.Count -eq 0) { throw "Nenhum host em: $Path" }
  return $out
}

$root = Get-RepoRoot -Hint $RepoRoot
Set-Location $root

if (-not $NodesFile) { $NodesFile = Join-Path $root "config\syntexa-prod-nodes.txt" }
$key = Get-SshKeyPath -Explicit $SshKey
$nodes = Read-ProdNodes -Path $NodesFile

Write-Host "==> Repo: $root"
Write-Host "==> Nós ($($nodes.Count)): $($nodes -join ', ')"
Write-Host "==> SSH: $key"

if ($StartAzureVMs) {
  Write-Host "==> Azure: a ligar VMs em $AzureResourceGroup ..."
  foreach ($vm in $AzureVmNames) {
    try {
      az vm start -g $AzureResourceGroup -n $vm --only-show-errors 2>$null | Out-Null
      Write-Host "    [OK] $vm"
    } catch {
      Write-Warning "Falha ao ligar $vm : $_"
    }
  }
}

$TAR_NAME = "syntexa-deploy.tar.gz"
$tarPath = Join-Path $env:TEMP $TAR_NAME

if (-not $SkipDeploy) {
  if (Test-Path $tarPath) { Remove-Item -Force $tarPath }
  Write-Host "==> tar (exclui scripts\*.ps1)"
  & tar.exe -czf $tarPath `
    --exclude="scripts/*.ps1" `
    --exclude="*.pyc" `
    vereda_backend vereda_ai llm-server requirements.txt scripts
  if ($LASTEXITCODE -ne 0) { throw "tar falhou" }

  $chownSpec = "${RemoteUser}:${RemoteUser}"
  foreach ($h in $nodes) {
    Write-Host "==> Deploy -> $RemoteUser@$h"
    ssh.exe -i $key -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 `
      "$RemoteUser@$h" "sudo mkdir -p $RemoteBase && sudo chown -R $chownSpec $RemoteBase"
    if ($LASTEXITCODE -ne 0) { throw "ssh prep falhou em $h" }

    scp.exe -i $key -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 `
      $tarPath "${RemoteUser}@${h}:${RemoteBase}/"
    if ($LASTEXITCODE -ne 0) { throw "scp falhou em $h" }

    $remoteBody = "set -e; cd $RemoteBase; sudo tar --overwrite -xzf $TAR_NAME; sudo chown -R $chownSpec $RemoteBase; bash scripts/remote_deploy_back.sh"
    ssh.exe -i $key -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=120 `
      "$RemoteUser@$h" $remoteBody
    if ($LASTEXITCODE -ne 0) { throw "remote_deploy falhou em $h" }
  }
  Remove-Item -Force $tarPath -ErrorAction SilentlyContinue
  Write-Host "[OK] Deploy concluído em todos os nós."
} else {
  Write-Host "==> SkipDeploy: não enviei tarball."
}

if ($SyncDesktopArtifacts) {
  $desk = Join-Path $root "vereda_backend\static\desktop"
  $artifacts = @(
    Join-Path $desk "SyntexaAI-Setup-1.0.0.exe",
    Join-Path $desk "SyntexaAI-linux-x64.tar.gz"
  )
  foreach ($f in $artifacts) {
    if (-not (Test-Path $f)) {
      Write-Warning "Artefacto em falta (ignore ou faça build desktop): $f"
    }
  }
  foreach ($h in $nodes) {
    Write-Host "==> Desktop artefacts -> $h"
    ssh.exe -i $key -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=15 `
      "$RemoteUser@$h" "mkdir -p $RemoteBase/vereda_backend/static/desktop"
    foreach ($f in $artifacts) {
      if (Test-Path $f) {
        scp.exe -i $key -o BatchMode=yes -o StrictHostKeyChecking=no `
          $f "${RemoteUser}@${h}:${RemoteBase}/vereda_backend/static/desktop/"
        if ($LASTEXITCODE -ne 0) { throw "scp desktop falhou em $h" }
      }
    }
  }
  Write-Host "[OK] Artefactos desktop sincronizados."
}

Write-Host "==> Validação por IP (SNI $PublicApiHost; TLS 1.2 para evitar resets Schannel no Windows)"
$healthUrl = "https://${PublicApiHost}/health"
$exeUrl = "https://${PublicApiHost}/v1/desktop/binary/SyntexaAI-Setup-1.0.0.exe"
$fail = $false
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
foreach ($h in $nodes) {
  $hc = & curl.exe --tls-max 1.2 -sS -o NUL -w "%{http_code}" --resolve "${PublicApiHost}:443:${h}" $healthUrl
  if (-not $hc) { $hc = "000" }
  $ec = & curl.exe --tls-max 1.2 -sS -o NUL -w "%{http_code}" --resolve "${PublicApiHost}:443:${h}" $exeUrl
  if (-not $ec) { $ec = "000" }
  Write-Host "    $h  health=$hc  exe=$ec"
  if ($hc -ne "200") { $fail = $true }
  if ($ec -ne "200") { $fail = $true }
}

Write-Host "==> Validação DNS (pode alternar entre nós)"
$dh = & curl.exe --tls-max 1.2 -sS -o NUL -w "%{http_code}" $healthUrl
if (-not $dh) { $dh = "000" }
Write-Host "    api DNS round-robin health=$dh (esperado 200 se ambos OK)"
$ErrorActionPreference = $prevEap

if (-not $SkipClean) {
  Write-Host "==> Limpeza local (build/temp/cache)"
  $patterns = @(
    (Join-Path $root "desktop\dist"),
    (Join-Path $root "desktop\dist-pack")
  )
  Get-ChildItem -Path (Join-Path $root "desktop") -Directory -Filter "dist-run-*" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
  foreach ($p in $patterns) {
    if (Test-Path $p) { Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue }
  }
  foreach ($sub in @(".next", "out")) {
    $fp = Join-Path $root "frontend\$sub"
    if (Test-Path $fp) { Remove-Item $fp -Recurse -Force -ErrorAction SilentlyContinue }
  }
  Get-ChildItem -Path $env:TEMP -Filter "syntexa-*" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
  npm cache clean --force 2>$null
  Write-Host "[OK] Limpeza concluída."
} else {
  Write-Host "==> SkipClean: não limpei ficheiros locais."
}

if ($fail) {
  Write-Error "Validação falhou em pelo menos um nó (ver health/exe acima)."
  exit 1
}
Write-Host "[OK] Tudo concluído."
exit 0
