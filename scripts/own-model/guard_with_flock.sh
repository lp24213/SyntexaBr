#!/usr/bin/env bash
# Evita sobreposição de guards (cron): flock + periodic_canary_guard.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOCK="${LOCK_FILE:-/tmp/syntexa-llm-guard.lock}"
exec 9>"${LOCK}"
flock -n 9 || { echo "[guard] outra instância em execução"; exit 0; }
exec "$ROOT/periodic_canary_guard.sh" "$@"
