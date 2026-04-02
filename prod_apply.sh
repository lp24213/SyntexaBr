#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/syntexa"
cd "$APP_DIR"

set_kv () {
  local k="$1"; local v="$2"
  if grep -q "^${k}=" .env 2>/dev/null; then
    sed -i "s|^${k}=.*|${k}=${v}|g" .env
  else
    echo "${k}=${v}" >> .env
  fi
}

touch .env
set_kv DEFAULT_LLM ollama
set_kv OLLAMA_ENDPOINT http://127.0.0.1:11434
set_kv OLLAMA_MODEL qwen2.5:3b
set_kv LLM_CHAT_TIMEOUT 25
set_kv LLM_CONNECT_TIMEOUT 5
set_kv LLM_READ_TIMEOUT 25
set_kv LLM_RETRY_COUNT 1
set_kv LLM_RETRY_BACKOFF_MS 200
set_kv LLM_MAX_CONCURRENCY 4
set_kv CHAT_CACHE_TTL_SEC 60
set_kv CHAT_SINGLEFLIGHT_WAIT_SEC 8

if !  curl -fsSL https://ollama.com/install.sh | sh
fi
sudo systemctl enable ollama >/dev/null 2>&1 || true
sudo systemctl restart ollama
ollama pull qwen2.5:3b

python3 -m py_compile \
  "$APP_DIR/vereda_ai/core/config.py" \
  "$APP_DIR/vereda_ai/ai/llm_engine.py" \
  "$APP_DIR/vereda_backend/core/config.py" \
  "$APP_DIR/vereda_backend/services/chat_engine.py" \
  "$APP_DIR/vereda_backend/services/tools.py"

sudo systemctl restart syntexa-backend.service
sudo systemctl status syntexa-backend.service --no-pager -n 80

