#!/usr/bin/env bash
set -euo pipefail

API="${1:-http://127.0.0.1:8000}"
GW="${2:-http://127.0.0.1:9010}"
TOKEN="${3:-}"

echo "[preflight] health backend"
curl -fsS "${API}/health" >/dev/null
echo "  ok"

echo "[preflight] health gateway"
curl -fsS "${GW}/health" >/dev/null
echo "  ok"

if [ -n "${TOKEN}" ]; then
  echo "[preflight] admin readiness"
  curl -fsS "${API}/v1/admin/llm/readiness" -H "Authorization: Bearer ${TOKEN}" >/dev/null
  echo "  ok"
fi

echo "[preflight] strict no fallback runtime"
ENVIRONMENT=production DEFAULT_LLM=syntexa_native OWN_MODEL_STRICT_NO_FALLBACK=1 \
  python scripts/own-model/verify_no_fallback.py >/dev/null
echo "  ok"

echo "[preflight] smoke completion"
curl -fsS -X POST "${GW}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"syntexa_small","messages":[{"role":"user","content":"Teste enterprise."}],"max_tokens":64,"temperature":0.7}' >/dev/null
echo "  ok"

echo "[preflight] enterprise checks passed"
