#!/usr/bin/env bash
set -euo pipefail

DATA="${1:-datasets/syntexa_corpus.jsonl}"
OUT="${2:-checkpoints/syntexa_small}"

python training/train_small_model.py \
  --data "${DATA}" \
  --checkpoints "${OUT}" \
  --epochs 2 \
  --batch-size 4 \
  --steps-per-epoch 300 \
  --hidden-size 512 \
  --layers 8 \
  --heads 8 \
  --seq-len 1024 \
  --vocab-size 32000 \
  --model-name syntexa_small

python training/activate_model.py --name syntexa_small --manifest "${OUT}/manifest.json"
