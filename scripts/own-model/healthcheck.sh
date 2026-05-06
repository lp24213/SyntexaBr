#!/usr/bin/env bash
set -euo pipefail

API="${1:-http://127.0.0.1:9000}"
GW="${2:-http://127.0.0.1:9010}"

echo "[health] own-model"
curl -fsS "${API}/health" | sed 's/.*/  &/'

echo "[health] gateway"
curl -fsS "${GW}/health" | sed 's/.*/  &/'

echo "[health] completion"
curl -fsS -X POST "${GW}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"syntexa_small","messages":[{"role":"user","content":"Escreva um resumo executivo curto."}],"max_tokens":64,"temperature":0.7}' \
  | sed 's/.*/  &/'

echo "[health] no-fallback readiness"
ENVIRONMENT=production DEFAULT_LLM=syntexa_native OWN_MODEL_STRICT_NO_FALLBACK=1 \
  python scripts/own-model/verify_no_fallback.py | sed 's/.*/  &/'
