#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${1:-backups/own-model}"
mkdir -p "${OUT_DIR}"

SRC="config/syntexa_model_registry.json"
if [ ! -f "${SRC}" ]; then
  echo "Registry não encontrado: ${SRC}"
  exit 1
fi

cp "${SRC}" "${OUT_DIR}/syntexa_model_registry-${STAMP}.json"
echo "Backup criado: ${OUT_DIR}/syntexa_model_registry-${STAMP}.json"
