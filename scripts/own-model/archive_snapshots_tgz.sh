#!/usr/bin/env bash
# Compacta pasta de snapshots para arquivo datado.
set -euo pipefail
DIR="${1:-./artifacts/ops-snapshots}"
OUT="${2:-./artifacts}"
if [ ! -d "${DIR}" ]; then
  echo "Pasta inexistente: ${DIR}"
  exit 1
fi
mkdir -p "${OUT}"
TS="$(date +%Y%m%d-%H%M%S)"
tar -czf "${OUT}/ops-snapshots-${TS}.tar.gz" -C "$(dirname "${DIR}")" "$(basename "${DIR}")"
echo "[tar] ${OUT}/ops-snapshots-${TS}.tar.gz"
