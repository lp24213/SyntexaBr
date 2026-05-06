#!/usr/bin/env bash
# Guard periódico estilo probe OSS: se readiness falhar, rollback via API (sem passar pelo change-freeze).
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
PREVIOUS_MODEL="${3:-}"
if [ -z "${TOKEN}" ] || [ -z "${PREVIOUS_MODEL}" ]; then
  echo "Uso: periodic_canary_guard.sh <api_base> <admin_jwt> <previous_model_para_rollback>"
  exit 1
fi
json="$(curl -fsS "${API}/v1/admin/llm/readiness" -H "Authorization: Bearer ${TOKEN}")"
ok="$(python - <<'PY'
import json,sys
r=json.loads(sys.stdin.read() or "{}")
print("1" if r.get("runtime",{}).get("ready") else "0")
PY
<<< "${json}")"
if [ "${ok}" = "1" ]; then
  echo "[guard] readiness OK"
  exit 0
fi
echo "[guard] readiness FALHOU — rollback para ${PREVIOUS_MODEL}"
curl -fsS -X POST "${API}/v1/admin/llm/rollback" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"target_model\":\"${PREVIOUS_MODEL}\",\"reason\":\"periodic_canary_guard\"}"
echo
echo "[guard] rollback solicitado (ver resposta JSON acima)"
exit 2
