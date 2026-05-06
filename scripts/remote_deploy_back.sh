#!/usr/bin/env bash
# Chamado no servidor após: scp syntexa-deploy.tar.gz -> /opt/syntexa/
# Uso: cd /opt/syntexa && tar --overwrite -xzf syntexa-deploy.tar.gz && bash scripts/remote_deploy_back.sh
set -euo pipefail
REMOTE_BASE="/opt/syntexa"
cd "$REMOTE_BASE"
# .env vindo de Windows (CRLF) quebra o EnvironmentFile do systemd — normaliza sempre.
if [[ -f .env ]]; then
  sed -i 's/\r$//' .env 2>/dev/null || true
fi
# Privilegios (VM Azure/Ubuntu: azureuser com sudo)
SUDO=""
if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  SUDO="sudo"
fi
# Tarball já extraído pelo comando SSH: tar -xzf ... && bash este script
$SUDO apt-get update -qq 2>/dev/null || true
$SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 ffmpeg -q 2>/dev/null || true
if [[ ! -f .venv/bin/activate ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
grep -v '^FRONTEND_ORIGIN' .env > .env.tmp 2>/dev/null || cp .env .env.tmp 2>/dev/null || touch .env.tmp
mv .env.tmp .env
echo 'FRONTEND_ORIGIN=https://syntexabr.com.br,https://www.syntexabr.com.br' >> .env
# Motor padrão: syntexa_native (proprietário). Sem Ollama.
if ! grep -q '^DEFAULT_LLM=' .env 2>/dev/null; then
  if grep -q '^AZURE_TGI_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=azure_tgi' >> .env
  elif grep -q '^EXLLAMA_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=exllama' >> .env
  elif grep -q '^REMOTE_LLM_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=remote' >> .env
  elif grep -q '^LOCAL_LLM_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=local_http' >> .env
  elif grep -q '^OLLAMA_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=ollama' >> .env
  else
    echo 'DEFAULT_LLM=syntexa_native' >> .env
  fi
fi
# vereda_ai usa VEREDA_DATABASE_URL; espelha DATABASE_URL se só um estiver definido (PostgreSQL na Azure, etc.)
if grep -q '^DATABASE_URL=' .env 2>/dev/null && ! grep -q '^VEREDA_DATABASE_URL=' .env 2>/dev/null; then
  grep '^DATABASE_URL=' .env | sed 's/^DATABASE_URL=/VEREDA_DATABASE_URL=/' >> .env
fi
# Multi-VM + produção: as duas réplicas devem apontar para o MESMO PostgreSQL (Azure), não ficheiro SQLite local.
if grep -q '^ENVIRONMENT=production' .env 2>/dev/null; then
  if grep -qE '^DATABASE_URL=.*sqlite' .env 2>/dev/null; then
    echo '[AVISO] produção com SQLite: não é adequado a 2+ VMs. Use Azure PostgreSQL (DATABASE_URL com sslmode=require) e a mesma URL em todos os nós: scripts/push-pg-url-to-syntexa-vms.sh'
  fi
fi

# Ollama Cloud (https://ollama.com) = sem Docker. Só sobe llm-server se ENABLE_LOCAL_LLM_STACK ou :11434 local.
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
if [[ -f "$REMOTE_BASE/scripts/run_uvicorn_prod.sh" ]]; then
  sed -i 's/\r$//' "$REMOTE_BASE/scripts/run_uvicorn_prod.sh" 2>/dev/null || true
  chmod +x "$REMOTE_BASE/scripts/run_uvicorn_prod.sh"
fi
$SUDO install -m 644 "$REMOTE_BASE/scripts/syntexa-backend.service" /etc/systemd/system/syntexa-backend.service
$SUDO systemctl daemon-reload
$SUDO systemctl enable syntexa-backend
command -v pm2 >/dev/null 2>&1 && pm2 delete syntexa-backend 2>/dev/null || true
pkill -9 -f 'uvicorn vereda_backend.main:app' 2>/dev/null || true
sleep 2
export PYTHONPATH="$REMOTE_BASE" PYTHONDONTWRITEBYTECODE=1 SYNTEXA_USE_AI_ENV=1
$SUDO systemctl restart syntexa-backend
$SUDO systemctl enable nginx 2>/dev/null || true
$SUDO systemctl start nginx 2>/dev/null || true
if command -v ufw >/dev/null 2>&1 && $SUDO ufw status 2>/dev/null | grep -q 'Status: active'; then
  $SUDO ufw allow 80/tcp 2>/dev/null || true
  $SUDO ufw allow 443/tcp 2>/dev/null || true
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
  $SUDO journalctl -u syntexa-backend -n 60 --no-pager
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

# Pacotes desktop (Electron) em vereda_backend/static/desktop — obrigatório para download real.
if [[ -f "$REMOTE_BASE/vereda_backend/static/desktop/SyntexaAI-Setup-1.0.0.exe" ]]; then
  echo '[OK] Binário Windows presente em vereda_backend/static/desktop/'
else
  echo '[AVISO] Falta SyntexaAI-Setup-1.0.0.exe — no PC: cd desktop && npm run build, depois deploy-back de novo.'
fi
if curl -sfI --connect-timeout 5 -o /dev/null "http://127.0.0.1:8000/v1/desktop/binary/SyntexaAI-Setup-1.0.0.exe" 2>/dev/null; then
  echo '[OK] GET /v1/desktop/binary/SyntexaAI-Setup-1.0.0.exe responde (uvicorn)'
else
  echo '[AVISO] /v1/desktop/binary/ não devolve 200 — verifique ficheiros em static/desktop e reinício do serviço.'
fi
