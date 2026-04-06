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
echo 'OLLAMA_ENDPOINT=http://172.17.0.1:11434' >> .env
echo 'OLLAMA_MODEL=llama3.2:1b' >> .env
echo 'DEFAULT_LLM=ollama' >> .env
cd llm-server
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
cd ..
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
