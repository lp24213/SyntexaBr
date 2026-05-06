#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${1:-backups/disaster-recovery/${STAMP}}"
mkdir -p "${OUT_DIR}"

cp "config/syntexa_model_registry.json" "${OUT_DIR}/syntexa_model_registry.json"
if [ -d "checkpoints" ]; then
  cp -r "checkpoints" "${OUT_DIR}/checkpoints"
fi
if [ -d "dist/own-model-bundle" ]; then
  cp -r "dist/own-model-bundle" "${OUT_DIR}/own-model-bundle"
fi

echo "Backup DR criado em: ${OUT_DIR}"
