param(
  [string]$Manifest = "checkpoints/syntexa_small/manifest.json",
  [int]$Port = 9000,
  [string]$Device = "cuda"
)

$ErrorActionPreference = "Stop"
Write-Host "[own-model] starting runtime on port $Port (device=$Device)"
python "training/serve_model.py" --checkpoint $Manifest --host "0.0.0.0" --port $Port --device $Device
