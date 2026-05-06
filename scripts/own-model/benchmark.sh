#!/usr/bin/env bash
set -euo pipefail

MANIFEST="${1:-checkpoints/syntexa_small/manifest.json}"
PROMPT="${2:-Monte um plano de crescimento para empresa de tecnologia.}"
RUNS="${3:-5}"

python training/benchmark_own_model.py \
  --manifest "${MANIFEST}" \
  --prompt "${PROMPT}" \
  --runs "${RUNS}" \
  --max-new-tokens 1024 \
  --temperature 0.8 \
  --top-k 80
