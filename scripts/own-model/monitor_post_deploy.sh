#!/usr/bin/env bash
set -euo pipefail

API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
PREVIOUS_MODEL="${3:-syntexa_native}"
WINDOW_SEC="${4:-300}"
POLL_SEC="${5:-15}"
MAX_ERROR_RATE="${6:-0.10}"
MAX_P95_MS="${7:-4000}"

if [ -z "${TOKEN}" ]; then
  echo "Uso: monitor_post_deploy.sh <api_base> <admin_token> <previous_model> [window_sec=300] [poll_sec=15] [max_error_rate=0.10] [max_p95_ms=4000]"
  exit 1
fi

end_ts=$(( $(date +%s) + WINDOW_SEC ))
echo "[monitor] janela de observação ${WINDOW_SEC}s"
while [ "$(date +%s)" -lt "${end_ts}" ]; do
  json="$(curl -fsS "${API}/v1/admin/llm/slo-snapshot" -H "Authorization: Bearer ${TOKEN}")"
  err="$(python - <<'PY'
import json,sys
o=json.loads(sys.stdin.read() or "{}")
print(float((o.get("slo") or {}).get("error_rate",0.0)))
PY
<<< "${json}")"
  p95="$(python - <<'PY'
import json,sys
o=json.loads(sys.stdin.read() or "{}")
print(float((o.get("slo") or {}).get("p95_latency_ms",0.0)))
PY
<<< "${json}")"
  echo "[monitor] error_rate=${err} p95_ms=${p95}"
  violate="$(python - <<PY
err=${err}
p95=${p95}
print("1" if (err>${MAX_ERROR_RATE} or p95>${MAX_P95_MS}) else "0")
PY
)"
  if [ "${violate}" = "1" ]; then
    echo "[monitor] SLO violado, rollback automático para ${PREVIOUS_MODEL}"
    hdr=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json")
    if [ -n "${FREEZE_BYPASS_SECRET:-}" ]; then
      hdr+=(-H "X-Syntexa-Freeze-Bypass: ${FREEZE_BYPASS_SECRET}")
    fi
    curl -fsS -X POST "${API}/v1/admin/llm/active" "${hdr[@]}" \
      -d "{\"model_name\":\"${PREVIOUS_MODEL}\"}" >/dev/null
    echo "[monitor] rollback concluído"
    exit 2
  fi
  sleep "${POLL_SEC}"
done
echo "[monitor] janela concluída sem violação de SLO"
