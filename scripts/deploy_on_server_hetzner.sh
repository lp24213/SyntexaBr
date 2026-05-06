#!/usr/bin/env bash
# =============================================================================
# Deploy COMPLETO no servidor Hetzner (bash) — equivalente ao remoto do
# deploy-hetzner.ps1 + instalação systemd/nginx do remote_deploy_back.sh
#
# PRÉ-REQUISITO: código em /opt/syntexa (tarball já enviado e extraído, OU
#   existe /opt/syntexa/syntexa-deploy.tar.gz e este script extrai).
#
# Uso (no servidor, como root):
#   cd /opt/syntexa && bash scripts/deploy_on_server_hetzner.sh
#
# Disco:
#   - App: /opt/syntexa
#   - Docker volumes (llm-server/docker-compose.yml): ollama_data, hf_cache
#     listar: docker volume ls | grep -E 'ollama|hf_cache'
#
# Docker / YML:
#   - Compose: llm-server/docker-compose.yml (Ollama :11434, image-gpu :8010)
#   - Só sobe se .env tiver ENABLE_LOCAL_LLM_STACK=true
#   - Depois: docker exec -it syntexa-ollama ollama pull <modelo>
#
# Backend: systemd syntexa-backend.service → uvicorn :8000
# =============================================================================
set -euo pipefail

REMOTE_BASE="${REMOTE_BASE:-/opt/syntexa}"
TAR_NAME="${TAR_NAME:-syntexa-deploy.tar.gz}"

cd "$REMOTE_BASE"

echo "=== [1] Pacotes sistema (pip/venv/docker) ==="
apt-get update -y 2>/dev/null || true
apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 ca-certificates curl -q 2>/dev/null || true
if ! command -v docker-compose >/dev/null 2>&1 && [ -x /usr/lib/docker/cli-plugins/docker-compose ]; then
  mkdir -p /usr/local/bin
  ln -sf /usr/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
fi
systemctl enable docker 2>/dev/null || true
systemctl start docker 2>/dev/null || true

if [[ -f "$REMOTE_BASE/$TAR_NAME" ]] && [[ ! -f "$REMOTE_BASE/vereda_backend/main.py" ]]; then
  echo "=== [2] Extraindo $TAR_NAME ==="
  tar -xzf "$REMOTE_BASE/$TAR_NAME"
fi

if [[ ! -f "$REMOTE_BASE/vereda_backend/main.py" ]]; then
  echo "ERRO: Nao ha codigo em $REMOTE_BASE (esperado vereda_backend/)."
  echo "  Envie e extraia o tarball, ou copie o repo para $REMOTE_BASE"
  exit 1
fi

echo "=== [3] Limpeza __pycache__ / .pyc ==="
find vereda_ai -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find vereda_ai -name '*.pyc' -delete 2>/dev/null || true
find vereda_backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "=== [4] venv Python + requirements.txt ==="
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "=== [5] .env (FRONTEND_ORIGIN + DEFAULT_LLM fallback) ==="
touch .env
grep -v '^FRONTEND_ORIGIN' .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env 2>/dev/null || true
grep -v '^FRONTEND_ORIGINS' .env > .env.tmp2 2>/dev/null || true
mv .env.tmp2 .env 2>/dev/null || true
if ! grep -q '^FRONTEND_ORIGIN=' .env 2>/dev/null; then
  echo 'FRONTEND_ORIGIN=https://syntexabr.com.br,https://www.syntexabr.com.br' >> .env
fi
cp .env .env.syntexa_ai 2>/dev/null || true
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
    echo 'DEFAULT_LLM não definido; deixe .env com o valor desejado.'
  fi
fi

echo "=== [6] Docker Compose (llm-server/docker-compose.yml) ==="
# Volumes Docker: ollama_data e hf_cache (ver docker volume ls). image-gpu exige NVIDIA.
if grep -q '^ENABLE_LOCAL_LLM_STACK=true' .env 2>/dev/null; then
  cd "$REMOTE_BASE/llm-server"
  docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || {
    echo "[AVISO] docker compose falhou (sem Docker, GPU, ou servico image-gpu). Ver: docker compose logs"
  }
  cd "$REMOTE_BASE"
else
  echo "  (ENABLE_LOCAL_LLM_STACK nao esta true — sem stack Docker; use OLLAMA_ENDPOINT no .env se Ollama for externo)"
fi

echo "=== [7] Evitar pacotes Python stale do site-packages ==="
rm -rf .venv/lib/python3.12/site-packages/vereda_ai .venv/lib/python3.12/site-packages/vereda_backend 2>/dev/null || true
rm -rf .venv/lib/python3.11/site-packages/vereda_ai .venv/lib/python3.11/site-packages/vereda_backend 2>/dev/null || true

echo "=== [8] systemd: syntexa-backend.service ==="
install -m 644 "$REMOTE_BASE/scripts/syntexa-backend.service" /etc/systemd/system/syntexa-backend.service
systemctl daemon-reload
systemctl enable syntexa-backend
command -v pm2 >/dev/null 2>&1 && pm2 delete syntexa-backend 2>/dev/null || true
pkill -9 -f 'uvicorn vereda_backend.main:app' 2>/dev/null || true
sleep 2
export PYTHONPATH="$REMOTE_BASE" PYTHONDONTWRITEBYTECODE=1
systemctl restart syntexa-backend

echo "=== [8b] systemd: syntexa-worker (opcional; exige REDIS_URL) ==="
if grep -q '^REDIS_URL=' "$REMOTE_BASE/.env" 2>/dev/null && [[ -f "$REMOTE_BASE/scripts/syntexa-worker.service" ]]; then
  if grep -q '^REDIS_URL=\s*$' "$REMOTE_BASE/.env" 2>/dev/null; then
    echo "  (REDIS_URL vazia — não iniciando worker ARQ)"
  else
    install -m 644 "$REMOTE_BASE/scripts/syntexa-worker.service" /etc/systemd/system/syntexa-worker.service
    systemctl daemon-reload
    systemctl enable syntexa-worker 2>/dev/null || true
    systemctl restart syntexa-worker 2>/dev/null || true
  fi
fi

systemctl enable nginx 2>/dev/null || true
systemctl start nginx 2>/dev/null || true
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q 'Status: active'; then
  ufw allow 80/tcp 2>/dev/null || true
  ufw allow 443/tcp 2>/dev/null || true
fi

echo "=== [9] Health :8000 ==="
for _ in $(seq 1 30); do
  if curl -sf --connect-timeout 3 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "[OK] $(curl -s http://127.0.0.1:8000/health)"
    break
  fi
  sleep 1
done
if ! curl -sf --connect-timeout 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "[ERRO] Backend nao respondeu. Journal:"
  journalctl -u syntexa-backend -n 80 --no-pager
  exit 1
fi

API_HOST="${API_HOST:-api.syntexabr.com.br}"
if curl -sf --connect-timeout 10 --resolve "${API_HOST}:443:127.0.0.1" "https://${API_HOST}/health" >/dev/null 2>&1; then
  echo "[OK] HTTPS local (SNI): https://${API_HOST}/health"
elif curl -sf --connect-timeout 10 "https://${API_HOST}/health" >/dev/null 2>&1; then
  echo "[OK] HTTPS (DNS): https://${API_HOST}/health"
else
  echo "[INFO] nginx/TLS nao testado; uvicorn OK em http://127.0.0.1:8000 — opcional: bash $REMOTE_BASE/scripts/setup_nginx_api.sh"
fi

echo "=== Deploy no servidor concluido. ==="
