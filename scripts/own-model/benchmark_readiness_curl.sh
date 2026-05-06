#!/usr/bin/env bash
# Mede latência de N pedidos GET readiness (admin).
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
N="${3:-10}"
if [ -z "${TOKEN}" ]; then
  echo "Uso: benchmark_readiness_curl.sh <api_base> <admin_jwt> [N=10]"
  exit 1
fi
for i in $(seq 1 "${N}"); do
  ts="$(date +%s%N)"
  curl -fsS -o /dev/null "${API}/v1/admin/llm/readiness" -H "Authorization: Bearer ${TOKEN}"
  te="$(date +%s%N)"
  echo "$i $(( (te - ts) / 1000000 )) ms"
done
