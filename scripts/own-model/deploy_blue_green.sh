#!/usr/bin/env bash
set -euo pipefail

API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
CANDIDATE="${3:-syntexa_small}"
ROLLBACK_ON_FAIL="${4:-true}"

if [ -z "${TOKEN}" ]; then
  echo "Uso: deploy_blue_green.sh <api_base> <admin_bearer_token> <candidate_model> [rollback_on_fail=true|false]"
  exit 1
fi

echo "[blue-green] registry atual"
curl -fsS "${API}/v1/admin/llm/registry" \
  -H "Authorization: Bearer ${TOKEN}" | sed 's/.*/  &/'
echo

echo "[blue-green] promovendo candidato=${CANDIDATE} rollback_on_fail=${ROLLBACK_ON_FAIL}"
curl -fsS -X POST "${API}/v1/admin/llm/promote-blue-green" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"candidate_model\":\"${CANDIDATE}\",\"rollback_on_fail\":${ROLLBACK_ON_FAIL}}"
echo

echo "[blue-green] readiness pós-promoção"
curl -fsS "${API}/v1/admin/llm/readiness" \
  -H "Authorization: Bearer ${TOKEN}" | sed 's/.*/  &/'
echo
