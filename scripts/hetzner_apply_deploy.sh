#!/usr/bin/env bash
# Aplica pacote já enviado: /opt/syntexa/syntexa-deploy.tar.gz
# Rode no servidor: bash /opt/syntexa/scripts/hetzner_apply_deploy.sh
set -euo pipefail

REMOTE_BASE="${REMOTE_BASE:-/opt/syntexa}"

cd "$REMOTE_BASE"
# Pacote syntexa-deploy.tar.gz já foi extraído pelo comando SSH antes de chamar este script.
apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 -q 2>/dev/null || true
python3 -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
grep -v '^FRONTEND_ORIGIN' .env > .env.tmp 2>/dev/null || cp .env .env.tmp 2>/dev/null || touch .env.tmp
mv .env.tmp .env
echo 'FRONTEND_ORIGIN=https://syntexabr.com.br,https://www.syntexabr.com.br' >> .env
# Não sobrescrever variáveis LLM existentes. Aplica fallback inteligente se DEFAULT_LLM ausente.
if ! grep -q '^DEFAULT_LLM=' .env 2>/dev/null; then
  if grep -q '^AZURE_TGI_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=azure_tgi' >> .env
  elif grep -q '^EXLLAMA_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=exllama' >> .env
  elif grep -q '^REMOTE_LLM_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=remote' >> .env
  elif grep -q '^OLLAMA_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=ollama' >> .env
  else
    echo 'DEFAULT_LLM não definido; deixe .env com a configuração desejada.'
  fi
fi

# Docker Ollama na VM só se pedires stack local OU endpoint apontar para :11434 neste host.
# Ollama Cloud (https://ollama.com + OLLAMA_API_KEY) não precisa de container — evita conflito e “moagem”.
_ollama_ep=""
if grep -q '^OLLAMA_ENDPOINT=' .env 2>/dev/null; then
  _ollama_ep=$(grep '^OLLAMA_ENDPOINT=' .env | cut -d= -f2- | tr -d '\r' | tr -d '"' | tr -d "'")
fi
if grep -q '^ENABLE_LOCAL_LLM_STACK=true' .env 2>/dev/null; then
  cd llm-server
  docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
  cd ..
elif grep -q '^DEFAULT_LLM=ollama' .env 2>/dev/null && [[ -n "$_ollama_ep" ]]; then
  case "$_ollama_ep" in
    http://127.0.0.1*|http://localhost*|http://0.0.0.0*)
      cd llm-server
      docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
      cd ..
      ;;
  esac
fi
python3 scripts/patch_vereda_ai_config.py
install -m 644 "$REMOTE_BASE/scripts/syntexa-backend.service" /etc/systemd/system/syntexa-backend.service
systemctl daemon-reload
systemctl enable syntexa-backend
command -v pm2 >/dev/null 2>&1 && pm2 delete syntexa-backend 2>/dev/null || true
pkill -9 -f 'uvicorn vereda_backend.main:app' 2>/dev/null || true
sleep 2
export PYTHONPATH="$REMOTE_BASE" PYTHONDONTWRITEBYTECODE=1 SYNTEXA_USE_AI_ENV=1
systemctl restart syntexa-backend
systemctl start nginx 2>/dev/null || true
sleep 6
if ! curl -sf --connect-timeout 5 "http://127.0.0.1:8000/health" >/dev/null; then
  echo "[ERRO] uvicorn não responde — journal:"
  journalctl -u syntexa-backend -n 80 --no-pager
  exit 1
fi
if curl -sf --connect-timeout 15 "https://api.syntexabr.com.br/health" >/dev/null; then
  echo "[OK] API HTTPS pública"
  curl -s "https://api.syntexabr.com.br/health"
  echo ""
else
  echo "[AVISO] HTTPS público falhou — confirme nginx/DNS (fix-proxy)"
fi
