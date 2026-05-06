#!/usr/bin/env bash
# Deploy backend para VM (equivalente a deploy-hetzner.ps1) — bash/Git Bash/WSL
# Uso: bash deploy-producao.sh
# Opcional: SYNTEXA_SSH_KEY  SYNTEXA_REMOTE_USER  SYNTEXA_REMOTE_HOST  SYNTEXA_REMOTE_BASE

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

SSH_KEY="${SYNTEXA_SSH_KEY:-}"
if [[ -z "$SSH_KEY" ]]; then
  if [[ -f "$HOME/.ssh/id_rsa" ]]; then SSH_KEY="$HOME/.ssh/id_rsa"
  elif [[ -f "$HOME/.ssh/id_ed25519" ]]; then SSH_KEY="$HOME/.ssh/id_ed25519"
  else SSH_KEY="$HOME/.ssh/id_rsa"; fi
fi
REMOTE_USER="${SYNTEXA_REMOTE_USER:-azureuser}"
REMOTE_HOST="${SYNTEXA_REMOTE_HOST:-74.163.97.52}"
REMOTE_BASE="${SYNTEXA_REMOTE_BASE:-/opt/syntexa}"
TAR_NAME="syntexa-deploy.tar.gz"

if [[ ! -f "$SSH_KEY" ]]; then
  echo "Chave SSH não encontrada: $SSH_KEY"
  exit 1
fi

echo "[deploy] Preparando $REMOTE_BASE no servidor..."
ssh -i "$SSH_KEY" -o ServerAliveInterval=30 -T "${REMOTE_USER}@${REMOTE_HOST}" "sudo mkdir -p $REMOTE_BASE && sudo chown \$USER:\$USER $REMOTE_BASE"

echo "[deploy] Criando $TAR_NAME..."
rm -f "$TAR_NAME"
if [[ -f .env ]]; then
  tar -czf "$TAR_NAME" vereda_backend vereda_ai llm-server requirements.txt scripts .env
else
  tar -czf "$TAR_NAME" vereda_backend vereda_ai llm-server requirements.txt scripts
fi

echo "[deploy] Enviando tarball..."
scp -i "$SSH_KEY" -o ServerAliveInterval=30 -o ServerAliveCountMax=6 "$TAR_NAME" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/"

echo "[deploy] Executando remoto (mesma lógica que deploy-hetzner.ps1)..."
ssh -i "$SSH_KEY" -o ServerAliveInterval=120 -T "${REMOTE_USER}@${REMOTE_HOST}" "REMOTE_BASE='$REMOTE_BASE' TAR_NAME='$TAR_NAME' bash -s" << 'REMOTE_EOF'
set -euo pipefail
cd "$REMOTE_BASE"
tar -xzf "$TAR_NAME"
python3 scripts/patch_vereda_ai_config.py || true
find vereda_ai -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
apt-get update -y 2>/dev/null || true
apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 2>/dev/null || true
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
touch .env
grep -v '^FRONTEND_ORIGIN' .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env 2>/dev/null || true
echo 'FRONTEND_ORIGIN=https://syntexabr.com.br,https://www.syntexabr.com.br' >> .env
cp .env .env.syntexa_ai 2>/dev/null || true
if ! grep -q '^DEFAULT_LLM=' .env 2>/dev/null; then
  if grep -q '^OLLAMA_ENDPOINT=' .env 2>/dev/null; then echo 'DEFAULT_LLM=ollama' >> .env; fi
fi
_ollama_ep=""
grep -q '^OLLAMA_ENDPOINT=' .env 2>/dev/null && _ollama_ep=$(grep '^OLLAMA_ENDPOINT=' .env | cut -d= -f2- | tr -d '\r"'"'"'')
if grep -q '^ENABLE_LOCAL_LLM_STACK=true' .env 2>/dev/null; then
  (cd llm-server && docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true)
elif grep -q '^DEFAULT_LLM=ollama' .env 2>/dev/null && [[ -n "$_ollama_ep" ]]; then
  case "$_ollama_ep" in
    http://127.0.0.1*|http://localhost*|http://0.0.0.0*) (cd llm-server && docker compose up -d 2>/dev/null || true) ;;
  esac
fi
rm -rf .venv/lib/python3.12/site-packages/vereda_ai .venv/lib/python3.12/site-packages/vereda_backend 2>/dev/null || true
rm -rf .venv/lib/python3.11/site-packages/vereda_ai .venv/lib/python3.11/site-packages/vereda_backend 2>/dev/null || true
export PYTHONPATH="$REMOTE_BASE" PYTHONDONTWRITEBYTECODE=1
if [[ -f /etc/systemd/system/syntexa-backend.service ]]; then
  sudo systemctl restart syntexa-backend.service || systemctl restart syntexa-backend.service
  sleep 6
else
  pkill -9 -f uvicorn 2>/dev/null || true
  sleep 2
  nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
  sleep 20
fi
sleep 8
curl -sf --connect-timeout 15 http://127.0.0.1:8000/health && echo "" && curl -s http://127.0.0.1:8000/health
REMOTE_EOF

rm -f "$TAR_NAME"
echo "[deploy] Concluído."
