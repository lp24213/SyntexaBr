#!/usr/bin/env bash
# Corrida local: estado em disco + opcional verify_no_fallback.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"
echo "=== dump_local_llm_state ==="
python scripts/own-model/dump_local_llm_state.py | head -n 80
echo "..."
if [ "${RUN_VERIFY_NO_FALLBACK:-0}" = "1" ]; then
  echo "=== verify_no_fallback ==="
  python scripts/own-model/verify_no_fallback.py
fi
echo "[run_local_llm_checks] fim"
