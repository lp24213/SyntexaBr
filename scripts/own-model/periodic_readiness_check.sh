#!/usr/bin/env bash
# Verificação periódica de readiness + política (cron / systemd timer).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
export ENVIRONMENT="${ENVIRONMENT:-production}"
export DEFAULT_LLM="${DEFAULT_LLM:-syntexa_native}"
export OWN_MODEL_STRICT_NO_FALLBACK="${OWN_MODEL_STRICT_NO_FALLBACK:-1}"
cd "$ROOT"
python scripts/own-model/verify_no_fallback.py
echo "readiness_ok $(date -Iseconds)"
