param(
  [string]$Api = "http://127.0.0.1:9000",
  [string]$Gateway = "http://127.0.0.1:9010"
)

$ErrorActionPreference = "Stop"

Write-Host "[health] own-model"
Invoke-RestMethod "$Api/health" | ConvertTo-Json -Depth 5

Write-Host "[health] gateway"
Invoke-RestMethod "$Gateway/health" | ConvertTo-Json -Depth 5

Write-Host "[health] completion"
$body = @{
  model = "syntexa_small"
  messages = @(@{ role = "user"; content = "Escreva um resumo executivo curto." })
  max_tokens = 64
  temperature = 0.7
} | ConvertTo-Json -Depth 10

Invoke-RestMethod "$Gateway/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 10

Write-Host "[health] no-fallback readiness"
$env:ENVIRONMENT = "production"
$env:DEFAULT_LLM = "syntexa_native"
$env:OWN_MODEL_STRICT_NO_FALLBACK = "1"
python "scripts/own-model/verify_no_fallback.py"
