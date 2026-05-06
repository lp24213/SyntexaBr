#!/usr/bin/env bash
# Fragmento executado na VM (invocado por deploy-hetzner.ps1). Placeholders: __REMOTE_BASE__ __TAR_NAME__
set -e
cd __REMOTE_BASE__

echo '--- [SYNTEXA] Extraindo tarball ---'
tar -xzf __TAR_NAME__

# Scripts vindos de Windows podem ter CRLF e quebrar bash (set: pipefail\r: invalid option)
find scripts -maxdepth 2 -name '*.sh' -exec sed -i 's/\r$//' {} \; 2>/dev/null || true

echo '--- [SYNTEXA] Aplicando patch vereda_ai/core/config.py ---'
python3 scripts/patch_vereda_ai_config.py || echo 'AVISO: patch_vereda_ai_config.py falhou'
find vereda_ai -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find vereda_ai -name '*.pyc' -delete 2>/dev/null || true

echo '--- [SYNTEXA] Pacotes do sistema (python3-venv, docker) ---'
sudo apt-get update -y 2>/dev/null || apt-get update -y 2>/dev/null || true
sudo apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 2>/dev/null || apt-get install -y python3-pip python3-venv docker.io docker-compose-v2 2>/dev/null || true
if ! command -v docker-compose >/dev/null 2>&1 && [ -x /usr/lib/docker/cli-plugins/docker-compose ]; then
  mkdir -p /usr/local/bin
  ln -sf /usr/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
fi

echo '--- [SYNTEXA] venv Python ---'
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
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
if grep -q '^DEFAULT_LLM=' .env 2>/dev/null; then
  echo 'DEFAULT_LLM já definido no .env; mantendo valor existente.'
else
  if grep -q '^AZURE_TGI_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=azure_tgi' >> .env
  elif grep -q '^EXLLAMA_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=exllama' >> .env
  elif grep -q '^REMOTE_LLM_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=remote' >> .env
  elif grep -q '^OLLAMA_ENDPOINT=' .env 2>/dev/null; then
    echo 'DEFAULT_LLM=ollama' >> .env
  else
    echo 'DEFAULT_LLM não definido e nenhum endpoint LLM detectado; deixando em branco (use .env para definir).'
  fi
fi

echo '--- [SYNTEXA] LLM server (docker) — só se Ollama local :11434 ou ENABLE_LOCAL_LLM_STACK ---'
_ollama_ep=""
if grep -q '^OLLAMA_ENDPOINT=' .env 2>/dev/null; then
  _ollama_ep=$(grep '^OLLAMA_ENDPOINT=' .env | cut -d= -f2- | tr -d '\r' | tr -d '"' | tr -d "'")
fi
if grep -q '^ENABLE_LOCAL_LLM_STACK=true' .env 2>/dev/null; then
  cd llm-server
  docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
  cd ..
elif grep -q '^DEFAULT_LLM=ollama' .env 2>/dev/null && [ -n "$_ollama_ep" ]; then
  case "$_ollama_ep" in
    http://127.0.0.1*|http://localhost*|http://0.0.0.0*)
      cd llm-server
      docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
      cd ..
      ;;
  esac
else
  echo '  (Ollama Cloud / externo — sem stack Docker llm-server)'
fi

echo '--- [SYNTEXA] Migração DB (coluna subscription_plan) ---'
echo '(migração ignorada neste deploy)'

echo '--- [SYNTEXA] Backend: systemd (preferencial) ou nohup ---'
rm -rf .venv/lib/python3.12/site-packages/vereda_ai .venv/lib/python3.12/site-packages/vereda_backend 2>/dev/null || true

export PYTHONPATH=__REMOTE_BASE__
export PYTHONDONTWRITEBYTECODE=1

if [ -f /etc/systemd/system/syntexa-backend.service ]; then
  echo 'Reiniciando syntexa-backend.service (systemd)...'
  sudo systemctl restart syntexa-backend.service 2>/dev/null || systemctl restart syntexa-backend.service
  sleep 10
else
  echo 'Sem unit systemd; subindo com nohup...'
  pkill -9 -f uvicorn 2>/dev/null || true
  sleep 4
  rm -f backend.log
  nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
  sleep 24
fi

echo 'Aguardando uvicorn...'
for _try in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf --connect-timeout 5 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

if curl -sf --connect-timeout 10 http://127.0.0.1:8000/health >/dev/null; then
  echo ''
  echo '=== API OK: /health respondeu ==='
  curl -s http://127.0.0.1:8000/health
  echo ''
  exit 0
else
  echo ''
  echo '=== ERRO: API NAO RESPONDEU ==='
  echo '--- ps aux | grep uvicorn ---'
  ps aux | grep -i uvicorn | grep -v grep || echo '(nenhum uvicorn rodando)'
  echo '--- ss -tulpn | grep 8000 ---'
  ss -tulpn | grep ':8000' || echo '(porta 8000 fechada ou ss indisponível)'
  echo '--- backend.log (últimas 200 linhas) ---'
  tail -n 200 backend.log 2>/dev/null || echo '(backend.log vazio ou inexistente)'
  echo '--- fim do diagnóstico ---'
  exit 1
fi
