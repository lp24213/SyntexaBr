#!/usr/bin/env bash
# Smoke: endpoints admin LLM/compliance (requer JWT).
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
if [ -z "${TOKEN}" ]; then
  echo "Uso: smoke_admin_llm.sh <api_base> <admin_jwt>"
  exit 1
fi
H=( -H "Authorization: Bearer ${TOKEN}" -H "Accept: application/json" )
for path in \
  /v1/admin/llm/readiness \
  /v1/admin/llm/slo-snapshot \
  /v1/admin/llm/registry \
  /v1/admin/compliance/policy \
  /v1/admin/system/status
do
  echo "== GET ${path}"
  curl -fsS "${API}${path}" "${H[@]}" | head -c 2000
  echo -e "\n"
done
echo "[smoke] OK"
