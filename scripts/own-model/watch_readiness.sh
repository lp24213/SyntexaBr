#!/usr/bin/env bash
# Poll readiness até ficar OK ou esgotar tentativas (útil após deploy).
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
MAX="${3:-30}"
SLEEP="${4:-10}"
if [ -z "${TOKEN}" ]; then
  echo "Uso: watch_readiness.sh <api_base> <admin_jwt> [max_tentativas=30] [sleep_sec=10]"
  exit 1
fi
i=0
while [ "${i}" -lt "${MAX}" ]; do
  json="$(curl -fsS "${API}/v1/admin/llm/readiness" -H "Authorization: Bearer ${TOKEN}")"
  ok="$(python - <<'PY'
import json,sys
r=json.loads(sys.stdin.read() or "{}")
print("1" if r.get("runtime",{}).get("ready") else "0")
PY
<<< "${json}")"
  echo "[watch] tentativa $((i+1))/${MAX} ready=${ok}"
  if [ "${ok}" = "1" ]; then
    echo "[watch] readiness OK"
    exit 0
  fi
  i=$((i+1))
  sleep "${SLEEP}"
done
echo "[watch] timeout sem readiness"
exit 1
