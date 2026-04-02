# ============================================================
# SyntexaBR — Deploy só BACKEND (Hetzner)
# ============================================================
# Uso: .\deploy-hetzner.ps1
# Envia um ÚNICO tarball (evita "Connection reset" do SCP com muitos arquivos).
# No servidor: extrai, venv, pip, docker, uvicorn, health check.
# ============================================================

Param()

$ErrorActionPreference = "Stop"

# --- CONFIG: chave SSH (obrigatória para SSH/SCP) ---
$SshKeyPath  = "C:\Users\luisp\.ssh\id_ed25519"
$RemoteUser  = "root"
$RemoteHost  = "91.98.123.197"
$RemoteBase  = "/opt/syntexa"

if (-not (Test-Path -LiteralPath $SshKeyPath)) { throw "Chave SSH nao encontrada: $SshKeyPath" }
$SshKeyPath  = (Resolve-Path -LiteralPath $SshKeyPath).Path

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$TarName     = "syntexa-deploy.tar.gz"

# --- 1) Preparar diretório remoto ---
Write-Host "[deploy-hetzner] Preparando diretório remoto..." -ForegroundColor Cyan
ssh -i $SshKeyPath "$RemoteUser@$RemoteHost" @"
set -e
mkdir -p /root/.ssh
touch /root/.ssh/authorized_keys
grep -qxF 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIINa81q3WlTt02lTd5Lv1F57Z0pVGqy3SsS5l5P+gLgi syntexabr-hetzner' /root/.ssh/authorized_keys || echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIINa81q3WlTt02lTd5Lv1F57Z0pVGqy3SsS5l5P+gLgi syntexabr-hetzner' >> /root/.ssh/authorized_keys
sudo mkdir -p $RemoteBase
sudo chown `$USER:`$USER $RemoteBase
"@
if ($LASTEXITCODE -ne 0) { throw "SSH preparação falhou" }

# --- 2) Criar tarball (um arquivo só = sem Connection reset) ---
Write-Host "[deploy-hetzner] Criando $TarName (SYNTEXA-BACKEND: vereda_backend, vereda_ai, llm-server, requirements.txt, .env)..." -ForegroundColor Cyan
Remove-Item $TarName -ErrorAction SilentlyContinue

# Um tarball só: evita Connection reset ao enviar centenas de arquivos
$tarList = @("vereda_backend", "vereda_ai", "llm-server", "requirements.txt", "scripts")
if (Test-Path "$Root\.env") { $tarList += ".env" }
$tarArgs = @("-czf", $TarName) + $tarList
& tar @tarArgs
if ($LASTEXITCODE -ne 0) { throw "tar falhou" }

# --- 3) Enviar UM único arquivo (com tentativas/retry) ---
Write-Host "[deploy-hetzner] Enviando $TarName (um arquivo, conexão estável)..." -ForegroundColor Cyan
$maxAttempts = 5
$ok = $false
for ($i = 1; $i -le $maxAttempts -and -not $ok; $i++) {
  Write-Host "[deploy-hetzner] SCP tentativa $i de $maxAttempts..." -ForegroundColor Yellow
  scp -v -i $SshKeyPath -o ServerAliveInterval=30 -o ServerAliveCountMax=6 "$Root\$TarName" "${RemoteUser}@${RemoteHost}:$RemoteBase/"
  if ($LASTEXITCODE -eq 0) {
    $ok = $true
  } else {
    Write-Host "[deploy-hetzner] SCP falhou (código $LASTEXITCODE). Aguardando 3s para tentar de novo..." -ForegroundColor Red
    Start-Sleep -Seconds 3
  }
}
if (-not $ok) { throw "SCP falhou após $maxAttempts tentativas (conexão SSH/Hetzner está resetando)." }

# --- 4) No servidor: extrair, venv, pip, uvicorn, health check (robusto) ---
Write-Host "[deploy-hetzner] No servidor: extrair, venv, pip, docker, uvicorn, health check..." -ForegroundColor Cyan
ssh -i $SshKeyPath -o ServerAliveInterval=30 "$RemoteUser@$RemoteHost" @"
set -e
cd $RemoteBase

echo '--- [SYNTEXA] Extraindo tarball ---'
tar -xzf $TarName

echo '--- [SYNTEXA] Aplicando patch vereda_ai/core/config.py ---'
python3 scripts/patch_vereda_ai_config.py || echo 'AVISO: patch_vereda_ai_config.py falhou'
find vereda_ai -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find vereda_ai -name '*.pyc' -delete 2>/dev/null || true

echo '--- [SYNTEXA] Pacotes do sistema (python3-venv, docker) ---'
apt-get update -y 2>/dev/null || true
apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 2>/dev/null || true
if ! command -v docker-compose >/dev/null 2>&1 && [ -x /usr/lib/docker/cli-plugins/docker-compose ]; then
  mkdir -p /usr/local/bin
  ln -sf /usr/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
fi

echo '--- [SYNTEXA] venv Python ---'
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo '--- [SYNTEXA] .env e variáveis ---'
touch .env
grep -v '^FRONTEND_ORIGIN' .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env 2>/dev/null || true
grep -v '^FRONTEND_ORIGINS' .env > .env.tmp2 2>/dev/null || true
mv .env.tmp2 .env 2>/dev/null || true
echo 'FRONTEND_ORIGIN=https://syntexabr.com.br,https://www.syntexabr.com.br' >> .env
cp .env .env.syntexa_ai 2>/dev/null || true
# Ollama na 11434 (docker llm-server). NÃO usar 8001 (nada escuta lá).
grep -v '^LOCAL_LLM_ENDPOINT' .env > .env.tmp 2>/dev/null || true; mv .env.tmp .env 2>/dev/null || true
grep -v '^OLLAMA_ENDPOINT' .env > .env.tmp 2>/dev/null || true; mv .env.tmp .env 2>/dev/null || true
grep -v '^DEFAULT_LLM' .env > .env.tmp 2>/dev/null || true; mv .env.tmp .env 2>/dev/null || true
echo 'OLLAMA_ENDPOINT=http://127.0.0.1:11434' >> .env
echo 'OLLAMA_MODEL=llama3.2:1b' >> .env
echo 'DEFAULT_LLM=ollama' >> .env

echo '--- [SYNTEXA] LLM server (docker compose) ---'
cd llm-server
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
cd ..

echo '--- [SYNTEXA] Migração DB (coluna subscription_plan) ---'
echo '(migração ignorada neste deploy)'

echo '--- [SYNTEXA] Backend: systemd (preferencial) ou nohup ---'
rm -rf .venv/lib/python3.12/site-packages/vereda_ai .venv/lib/python3.12/site-packages/vereda_backend 2>/dev/null || true

export PYTHONPATH=$RemoteBase
export PYTHONDONTWRITEBYTECODE=1

if [ -f /etc/systemd/system/syntexa-backend.service ]; then
  echo 'Reiniciando syntexa-backend.service (systemd)...'
  systemctl restart syntexa-backend.service
  sleep 6
else
  echo 'Sem unit systemd; subindo com nohup...'
  pkill -9 -f uvicorn 2>/dev/null || true
  sleep 4
  rm -f backend.log
  nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
  sleep 24
fi

echo 'Aguardando uvicorn...'
sleep 24

if curl -sf --connect-timeout 10 http://127.0.0.1:8000/health >/dev/null; then
  echo ''
  echo '=== API OK: /health respondeu ==='
  curl -s http://127.0.0.1:8000/health
  echo ''
else
  echo ''
  echo '=== ERRO: API NAO RESPONDEU ==='
  echo '--- ps aux | grep uvicorn ---'
  ps aux | grep -i uvicorn | grep -v grep || echo '(nenhum uvicorn rodando)'
  echo '--- ss -tulpn | grep 8000 ---'
  ss -tulpn | grep ':8000' || netstat -tulpn | grep ':8000' || echo '(porta 8000 fechada)'
  echo '--- backend.log (últimas 200 linhas) ---'
  tail -n 200 backend.log 2>/dev/null || echo '(backend.log vazio ou inexistente)'
  echo '--- fim do diagnóstico ---'
  exit 1
fi
"@

if ($LASTEXITCODE -ne 0) {
  Write-Host ""
  Write-Host "[deploy-hetzner] API nao respondeu. Veja o diagnóstico acima (ps/ss/backend.log)." -ForegroundColor Red
  exit 1
}

Remove-Item $TarName -ErrorAction SilentlyContinue
Write-Host "[deploy-hetzner] Backend no ar. API respondendo em :8000" -ForegroundColor Green
