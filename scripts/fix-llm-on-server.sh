#!/bin/bash
# Rode NO SERVIDOR (após ssh): bash fix-llm-on-server.sh
# Corrige .env para usar Ollama na 11434 (não 8001) e reinicia backend.
set -e
cd /opt/syntexa

echo "--- Corrigindo .env para Ollama (porta 11434) ---"
grep -v '^LOCAL_LLM_ENDPOINT' .env > .env.tmp 2>/dev/null || true
grep -v '^OLLAMA_ENDPOINT' .env.tmp > .env.tmp2 2>/dev/null || true
grep -v '^DEFAULT_LLM' .env.tmp2 > .env.tmp3 2>/dev/null || true
grep -v '^OLLAMA_MODEL' .env.tmp3 > .env 2>/dev/null || true
rm -f .env.tmp .env.tmp2 .env.tmp3
echo 'OLLAMA_ENDPOINT=http://172.17.0.1:11434' >> .env
echo 'OLLAMA_MODEL=llama3.2:1b' >> .env
echo 'DEFAULT_LLM=ollama' >> .env
echo "OK .env"

echo "--- Subindo Ollama (Docker) ---"
cd llm-server
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
cd /opt/syntexa
sleep 3

echo "--- Baixando modelo pequeno (1B) se ainda não tiver ---"
docker exec syntexa-ollama ollama pull llama3.2:1b 2>/dev/null || true

echo "--- Reiniciando backend ---"
pkill -9 -f uvicorn 2>/dev/null || true
sleep 2
export PYTHONPATH=/opt/syntexa
nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 5
curl -sS --connect-timeout 15 https://api.syntexabr.com.br/health && echo "" && echo "Backend OK (API pública). Teste o chat."
