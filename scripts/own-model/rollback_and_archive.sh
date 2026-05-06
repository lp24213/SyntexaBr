#!/usr/bin/env bash
# Rollback via API (sem freeze) + grava resposta.
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
TARGET="${3:-}"
REASON="${4:-manual_cli}"
OUT_DIR="${5:-./artifacts/promotions}"
if [ -z "${TOKEN}" ] || [ -z "${TARGET}" ]; then
  echo "Uso: rollback_and_archive.sh <api_base> <admin_jwt> <target_model> [reason] [out_dir]"
  exit 1
fi
mkdir -p "${OUT_DIR}"
TS="$(date +%Y%m%d-%H%M%S)"
curl -fsS -X POST "${API}/v1/admin/llm/rollback" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"target_model\":\"${TARGET}\",\"reason\":\"${REASON}\"}" \
  | tee "${OUT_DIR}/rollback-${TARGET}-${TS}.json"
echo
echo "[archive] ${OUT_DIR}/rollback-${TARGET}-${TS}.json"
