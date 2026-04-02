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
grep -v '^OLLAMA_ENDPOINT\|^OLLAMA_MODEL\|^DEFAULT_LLM' .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env 2>/dev/null || true
echo 'OLLAMA_ENDPOINT=http://127.0.0.1:11434' >> .env
echo 'OLLAMA_MODEL=llama3.2:1b' >> .env
echo 'DEFAULT_LLM=ollama' >> .env
cd llm-server
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
cd ..
python3 scripts/patch_vereda_ai_config.py
pkill -9 -f uvicorn 2>/dev/null || true
sleep 4
rm -f backend.log
export PYTHONPATH="$REMOTE_BASE" PYTHONDONTWRITEBYTECODE=1 SYNTEXA_USE_AI_ENV=1
unset FRONTEND_ORIGIN
nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo "Aguardando API (15s)..."
sleep 15
if curl -sf --connect-timeout 5 http://127.0.0.1:8000/health >/dev/null; then
  echo "[OK] API no ar"
  curl -s http://127.0.0.1:8000/health
  echo ""
else
  echo "[ERRO] API nao respondeu"
  tail -80 backend.log || true
  exit 1
fi
