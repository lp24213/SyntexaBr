#!/usr/bin/env bash
# Grava snapshot JSON (readiness + SLO + policy) para pasta de artefactos.
set -euo pipefail
API="${1:-http://127.0.0.1:8000}"
TOKEN="${2:-}"
OUT_DIR="${3:-./artifacts/ops-snapshots}"
if [ -z "${TOKEN}" ]; then
  echo "Uso: snapshot_ops_bundle.sh <api_base> <admin_jwt> [out_dir]"
  exit 1
fi
mkdir -p "${OUT_DIR}"
TS="$(date +%Y%m%d-%H%M%S)"
H=( -H "Authorization: Bearer ${TOKEN}" -H "Accept: application/json" )
curl -fsS "${API}/v1/admin/llm/readiness" "${H[@]}" -o "${OUT_DIR}/readiness-${TS}.json"
curl -fsS "${API}/v1/admin/llm/slo-snapshot" "${H[@]}" -o "${OUT_DIR}/slo-${TS}.json"
curl -fsS "${API}/v1/admin/compliance/policy" "${H[@]}" -o "${OUT_DIR}/policy-${TS}.json"
curl -fsS "${API}/v1/admin/llm/registry" "${H[@]}" -o "${OUT_DIR}/registry-${TS}.json"
echo "[snapshot] gravado em ${OUT_DIR} (*-${TS}.json)"
