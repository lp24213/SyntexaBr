#!/bin/bash
# Rode NO SERVIDOR (após ssh): bash fix-llm-on-server.sh
# Corrige .env para usar Ollama na 11434 (não 8001) e reinicia backend.
set -e
cd /opt/syntexa

echo "--- Ajustando .env LLM (não força Ollama) ---"
# Remove apenas entradas antigas relativas a LOCAL_LLM/OLLAMA defaults
grep -v '^LOCAL_LLM_ENDPOINT' .env > .env.tmp 2>/dev/null || true
grep -v '^OLLAMA_ENDPOINT' .env.tmp > .env.tmp2 2>/dev/null || true
grep -v '^DEFAULT_LLM' .env.tmp2 > .env.tmp3 2>/dev/null || true
grep -v '^OLLAMA_MODEL' .env.tmp3 > .env 2>/dev/null || true
rm -f .env.tmp .env.tmp2 .env.tmp3 || true

# Se desejar definir Ollama localmente, o administrador deve explicitamente definir OLLAMA_ENDPOINT ou
# definir ENABLE_LOCAL_LLM_STACK=true e DEFAULT_LLM=ollama no .env. Este script não força isso.
echo "OK .env (ajustada)"

if grep -q '^DEFAULT_LLM=ollama' .env 2>/dev/null || grep -q '^ENABLE_LOCAL_LLM_STACK=true' .env 2>/dev/null; then
	echo "--- Subindo Ollama (Docker) ---"
	cd llm-server
	docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
	cd /opt/syntexa
	sleep 3
	echo "--- Baixando modelo pequeno (1B) se ainda não tiver ---"
	docker exec syntexa-ollama ollama pull llama3.2:1b 2>/dev/null || true
else
	echo "--- Ollama local não está configurado; pulando start de Docker/ollama ---"
fi

echo "--- Reiniciando backend ---"
pkill -9 -f uvicorn 2>/dev/null || true
sleep 2
export PYTHONPATH=/opt/syntexa
nohup .venv/bin/python -m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 5
curl -sS --connect-timeout 15 https://api.syntexabr.com.br/health && echo "" && echo "Backend OK (API pública). Teste o chat."
