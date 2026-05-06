param(
  [string]$Manifest = "checkpoints/syntexa_small/manifest.json",
  [string]$Prompt = "Monte um plano de crescimento para empresa de tecnologia.",
  [int]$Runs = 5
)

python "training/benchmark_own_model.py" `
  --manifest $Manifest `
  --prompt $Prompt `
  --runs $Runs `
  --max-new-tokens 1024 `
  --temperature 0.8 `
  --top-k 80
