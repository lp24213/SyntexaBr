#!/usr/bin/env bash
# Chamado no servidor após: scp syntexa-deploy.tar.gz -> /opt/syntexa/
# Uso: cd /opt/syntexa && tar -xzf syntexa-deploy.tar.gz && bash scripts/remote_deploy_back.sh
set -euo pipefail
REMOTE_BASE="/opt/syntexa"
cd "$REMOTE_BASE"
# Tarball já extraído pelo comando SSH: tar -xzf ... && bash este script
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
systemctl enable nginx 2>/dev/null || true
systemctl start nginx 2>/dev/null || true
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q 'Status: active'; then
  ufw allow 80/tcp 2>/dev/null || true
  ufw allow 443/tcp 2>/dev/null || true
fi
echo 'Aguardando uvicorn (systemd)...'
sleep 6
for _attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25; do
  if curl -sf --connect-timeout 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo '[OK] uvicorn responde em :8000'
    break
  fi
  sleep 1
done
if ! curl -sf --connect-timeout 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo '[ERRO] uvicorn nao subiu. Journal:'
  journalctl -u syntexa-backend -n 60 --no-pager
  exit 1
fi
API_HOST="api.syntexabr.com.br"
# Valida HTTPS no proprio servidor (SNI -> 127.0.0.1): nao depende de DNS na internet nem do PC.
if curl -sf --connect-timeout 10 --resolve "${API_HOST}:443:127.0.0.1" "https://${API_HOST}/health" >/dev/null 2>&1; then
  echo "[OK] HTTPS (nginx + cert) neste host"
  curl -s --resolve "${API_HOST}:443:127.0.0.1" "https://${API_HOST}/health"
  echo ''
elif curl -sf --connect-timeout 10 "https://${API_HOST}/health" >/dev/null 2>&1; then
  echo '[OK] API HTTPS (DNS global OK)'
  curl -s "https://${API_HOST}/health"
  echo ''
else
  echo '[INFO] TLS/nginx ainda nao testavel ou nao configurado. Uvicorn OK em :8000.'
  echo "  Neste servidor: bash $REMOTE_BASE/scripts/setup_nginx_api.sh"
fi
