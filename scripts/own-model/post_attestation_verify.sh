#!/usr/bin/env bash
# Envia um JSON de atestação ao endpoint de verificação (ou valida localmente).
set -euo pipefail
JSON_FILE="${1:-}"
API="${2:-http://127.0.0.1:8000}"
TOKEN="${3:-}"
MODE="${4:-local}"
if [ -z "${JSON_FILE}" ] || [ ! -f "${JSON_FILE}" ]; then
  echo "Uso: post_attestation_verify.sh <attestation.json> [api_base] [admin_jwt] [local|api]"
  exit 1
fi
if [ "${MODE}" = "api" ]; then
  if [ -z "${TOKEN}" ]; then
    echo "Modo api requer token"
    exit 1
  fi
  BODY="$(python -c "import json,sys; p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); print(json.dumps({'document':d}))" "${JSON_FILE}")"
  curl -fsS -X POST "${API}/v1/admin/llm/verify-attestation" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${BODY}"
  echo
else
  ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
  export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
  python "${ROOT}/scripts/own-model/verify_promotion_attestation.py" "${JSON_FILE}"
fi
