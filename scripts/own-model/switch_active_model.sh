#!/usr/bin/env bash
set -euo pipefail

API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
MODEL="${3:-syntexa_small}"

if [ -z "${TOKEN}" ]; then
  echo "Uso: switch_active_model.sh <api_base> <admin_bearer_token> <model_name>"
  exit 1
fi

curl -fsS -X POST "${API}/v1/admin/llm/active" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"model_name\":\"${MODEL}\"}"
echo
