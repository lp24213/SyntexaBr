#!/usr/bin/env bash
set -euo pipefail

MANIFEST="${1:-checkpoints/syntexa_small/manifest.json}"
PORT="${2:-9000}"
DEVICE="${3:-cuda}"

echo "[own-model] starting runtime on port ${PORT} (device=${DEVICE})"
python training/serve_model.py --checkpoint "${MANIFEST}" --host 0.0.0.0 --port "${PORT}" --device "${DEVICE}"
