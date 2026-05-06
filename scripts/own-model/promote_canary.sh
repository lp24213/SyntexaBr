#!/usr/bin/env bash
set -euo pipefail

API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
CANDIDATE="${3:-syntexa_small}"
CHECKS="${4:-3}"
INTERVAL="${5:-2.0}"
ROLLBACK_ON_FAIL="${6:-true}"
ENFORCE_SLO="${7:-true}"
MAX_ERROR_RATE="${8:-0.08}"
MAX_P95_MS="${9:-3500}"
MIN_REQ="${10:-50}"

if [ -z "${TOKEN}" ]; then
  echo "Uso: promote_canary.sh <api_base> <admin_token> <candidate_model> [checks=3] [interval_sec=2.0] [rollback_on_fail=true|false] [enforce_slo=true|false] [max_error_rate=0.08] [max_p95_ms=3500] [min_requests_for_slo=50]"
  exit 1
fi

curl -fsS -X POST "${API}/v1/admin/llm/promote-canary" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"candidate_model\":\"${CANDIDATE}\",\"checks\":${CHECKS},\"interval_sec\":${INTERVAL},\"rollback_on_fail\":${ROLLBACK_ON_FAIL},\"enforce_slo\":${ENFORCE_SLO},\"max_error_rate\":${MAX_ERROR_RATE},\"max_p95_latency_ms\":${MAX_P95_MS},\"min_requests_for_slo\":${MIN_REQ}}"
echo
