# ============================================================
# SyntexaBR — Deploy só BACKEND (VM)
# ============================================================
# Uso: .\deploy-hetzner.ps1
# Envia um ÚNICO tarball (evita "Connection reset" do SCP com muitos arquivos).
# No servidor: extrai, venv, pip, docker, uvicorn, health check.
# ============================================================

Param()

$ErrorActionPreference = "Stop"

# --- CONFIG: chave SSH (obrigatória para SSH/SCP) ---
# Pode sobrescrever por variáveis de ambiente (recomendado):
#   $env:SYNTEXA_SSH_KEY="C:\caminho\chave.pem"
#   $env:SYNTEXA_REMOTE_USER="azureuser"
#   $env:SYNTEXA_REMOTE_HOST="74.163.97.52"
#   $env:SYNTEXA_REMOTE_BASE="/opt/syntexa"
$SshKeyPath  = $env:SYNTEXA_SSH_KEY
if (-not $SshKeyPath) {
  $tryRsa = "C:\Users\luisp\.ssh\id_rsa"
  $tryEd  = "C:\Users\luisp\.ssh\id_ed25519"
  if (Test-Path -LiteralPath $tryRsa) { $SshKeyPath = $tryRsa }
  elseif (Test-Path -LiteralPath $tryEd) { $SshKeyPath = $tryEd }
  else { $SshKeyPath = $tryRsa }
}

$RemoteUser  = $env:SYNTEXA_REMOTE_USER
if (-not $RemoteUser) { $RemoteUser = "azureuser" }

$RemoteHost  = $env:SYNTEXA_REMOTE_HOST
if (-not $RemoteHost) { $RemoteHost = "74.163.97.52" }

$RemoteBase  = $env:SYNTEXA_REMOTE_BASE
if (-not $RemoteBase) { $RemoteBase = "/opt/syntexa" }
$RemoteUser = ($RemoteUser -replace "`r", "").Trim()
$RemoteHost = ($RemoteHost -replace "`r", "").Trim()
$RemoteBase = ($RemoteBase -replace "`r", "").Trim()

if (-not (Test-Path -LiteralPath $SshKeyPath)) { throw "Chave SSH nao encontrada: $SshKeyPath" }
$SshKeyPath  = (Resolve-Path -LiteralPath $SshKeyPath).Path

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$TarName     = "syntexa-deploy.tar.gz"

function ConvertTo-BashScriptLf {
    param([string]$Script)
    if ([string]::IsNullOrEmpty($Script)) { return $Script }
    return (($Script -replace "`r`n", "`n") -replace "`r", "`n") -replace "`r", ""
}

# --- 1) Preparar diretório remoto (sem pipe: evita \r que quebra bash no Windows) ---
Write-Host "[deploy-vm] Preparando diretório remoto..." -ForegroundColor Cyan
& ssh.exe -i $SshKeyPath -o BatchMode=yes -T "${RemoteUser}@${RemoteHost}" "sudo mkdir -p '$RemoteBase' && sudo chown ${RemoteUser}:${RemoteUser} '$RemoteBase'"
if ($LASTEXITCODE -ne 0) { throw "SSH preparação falhou" }

# --- 2) Criar tarball (um arquivo só = sem Connection reset) ---
Write-Host "[deploy-vm] Criando $TarName (SYNTEXA-BACKEND: vereda_backend, vereda_ai, llm-server, requirements.txt, .env)..." -ForegroundColor Cyan
Remove-Item $TarName -ErrorAction SilentlyContinue

# Um tarball só: evita Connection reset ao enviar centenas de arquivos
$tarList = @("vereda_backend", "vereda_ai", "llm-server", "requirements.txt", "scripts")
if (Test-Path "$Root\.env") { $tarList += ".env" }
$tarArgs = @("-czf", $TarName) + $tarList
& tar @tarArgs
if ($LASTEXITCODE -ne 0) { throw "tar falhou" }

# --- 3) Enviar UM único arquivo (com tentativas/retry) ---
Write-Host "[deploy-vm] Enviando $TarName (um arquivo, conexão estável)..." -ForegroundColor Cyan
$maxAttempts = 5
$ok = $false
for ($i = 1; $i -le $maxAttempts -and -not $ok; $i++) {
  Write-Host "[deploy-vm] SCP tentativa $i de $maxAttempts..." -ForegroundColor Yellow
  scp -v -i $SshKeyPath -o ServerAliveInterval=30 -o ServerAliveCountMax=6 "$Root\$TarName" "${RemoteUser}@${RemoteHost}:$RemoteBase/"
  if ($LASTEXITCODE -eq 0) {
    $ok = $true
  } else {
    Write-Host "[deploy-vm] SCP falhou (código $LASTEXITCODE). Aguardando 3s para tentar de novo..." -ForegroundColor Red
    Start-Sleep -Seconds 3
  }
}
if (-not $ok) { throw "SCP falhou após $maxAttempts tentativas (conexão SSH/VM está resetando)." }

# --- 4) No servidor: extrair, venv, pip, uvicorn, health check (robusto) ---
# Script bash em ficheiro à parte: o PowerShell interpretava $(grep...) como subexpressão.
Write-Host "[deploy-vm] No servidor: extrair, venv, pip, docker, uvicorn, health check..." -ForegroundColor Cyan
$remoteBodyPath = Join-Path $Root "scripts\deploy_remote_body.sh"
if (-not (Test-Path -LiteralPath $remoteBodyPath)) { throw "Falta scripts/deploy_remote_body.sh" }
$rawBody = [System.IO.File]::ReadAllText($remoteBodyPath)
$rawBody = $rawBody -replace "`r`n", "`n" -replace "`r", "`n"
$remoteDeploy = $rawBody.Replace("__REMOTE_BASE__", $RemoteBase).Replace("__TAR_NAME__", $TarName)
$remoteDeploy = ConvertTo-BashScriptLf $remoteDeploy
$remoteDeploy = (($remoteDeploy -replace "`r", "").TrimEnd() + "`n")
$remoteDeploy | & ssh.exe -i $SshKeyPath -o ServerAliveInterval=120 -T "${RemoteUser}@${RemoteHost}" "bash -s"
$sshExit = $LASTEXITCODE

if ($sshExit -ne 0) {
  Write-Host ""
  Write-Host "[deploy-vm] API nao respondeu. Veja o diagnóstico acima (ps/ss/backend.log)." -ForegroundColor Red
  exit 1
}

Remove-Item $TarName -ErrorAction SilentlyContinue
Write-Host "[deploy-vm] Backend no ar. API respondendo em :8000" -ForegroundColor Green
