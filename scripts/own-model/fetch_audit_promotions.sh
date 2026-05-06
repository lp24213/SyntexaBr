#!/usr/bin/env bash
# Lista últimas entradas de auditoria relacionadas a LLM (prefixo llm_).
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
LIMIT="${3:-80}"
if [ -z "${TOKEN}" ]; then
  echo "Uso: fetch_audit_promotions.sh <api_base> <admin_jwt> [limit=80]"
  exit 1
fi
curl -fsS "${API}/v1/admin/compliance/audit?action_prefix=llm_&limit=${LIMIT}" \
  -H "Authorization: Bearer ${TOKEN}" | python -m json.tool
