#!/usr/bin/env bash
# Canary via API + grava JSON completo em artifacts/promotions.
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
CANDIDATE="${3:-}"
OUT_DIR="${4:-./artifacts/promotions}"
if [ -z "${TOKEN}" ] || [ -z "${CANDIDATE}" ]; then
  echo "Uso: canary_and_archive.sh <api_base> <admin_jwt> <candidate_model> [out_dir]"
  exit 1
fi
mkdir -p "${OUT_DIR}"
TS="$(date +%Y%m%d-%H%M%S)"
EXTRA=()
if [ -n "${FREEZE_BYPASS_SECRET:-}" ]; then
  EXTRA=( -H "X-Syntexa-Freeze-Bypass: ${FREEZE_BYPASS_SECRET}" )
fi
curl -fsS -X POST "${API}/v1/admin/llm/promote-canary" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  "${EXTRA[@]}" \
  -d "{\"candidate_model\":\"${CANDIDATE}\",\"checks\":5,\"interval_sec\":2,\"rollback_on_fail\":true,\"enforce_slo\":false}" \
  | tee "${OUT_DIR}/promote-canary-${CANDIDATE}-${TS}.json"
echo
echo "[archive] ${OUT_DIR}/promote-canary-${CANDIDATE}-${TS}.json"
