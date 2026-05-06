param(
  [string]$Data = "datasets/syntexa_corpus.jsonl",
  [string]$Out = "checkpoints/syntexa_small"
)

$ErrorActionPreference = "Stop"

python "training/train_small_model.py" `
  --data $Data `
  --checkpoints $Out `
  --epochs 2 `
  --batch-size 4 `
  --steps-per-epoch 300 `
  --hidden-size 512 `
  --layers 8 `
  --heads 8 `
  --seq-len 1024 `
  --vocab-size 32000 `
  --model-name syntexa_small

python "training/activate_model.py" --name syntexa_small --manifest "$Out/manifest.json"
