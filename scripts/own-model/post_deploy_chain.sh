#!/usr/bin/env bash
# Cadeia: esperar readiness -> smoke admin -> snapshot (falha rápida se algum passo falhar).
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${TOKEN}" ]; then
  echo "Uso: post_deploy_chain.sh <api_base> <admin_jwt>"
  exit 1
fi
"${ROOT}/watch_readiness.sh" "${API}" "${TOKEN}" 36 10
"${ROOT}/smoke_admin_llm.sh" "${API}" "${TOKEN}"
"${ROOT}/snapshot_ops_bundle.sh" "${API}" "${TOKEN}" "${3:-./artifacts/ops-snapshots}"
echo "[chain] OK"
