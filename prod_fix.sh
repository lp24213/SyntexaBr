set -euo pipefail

APP_DIR="/opt/syntexa"
cd "$APP_DIR"

upsert() {
  k="$1"; v="$2"
  touch .env
  if grep -q "^${k}=" .env; then
    sed -i "s|^${k}=.*|${k}=${v}|g" .env
  else
    echo "${k}=${v}" >> .env
  fi
}

upsert DEFAULT_LLM ollama
upsert OLLAMA_ENDPOINT http://127.0.0.1:11434
upsert OLLAMA_MODEL qupsert LLM_CHAT_TIMEOUT 25
upsert LLM_CONNECT_TIMEOUT 5
upsert LLM_READ_TIMEOUT 25
upsert LLM_RETRY_COUNT 1
upsert LLM_RETRY_BACKOFF_MS 200
upsert LLM_MAX_CONCURRENCY 4
upsert CHAT_CACHE_TTL_SEC 60
upsert CHAT_SINGLEFLIGHT_WAIT_SEC 8

if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
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

