param(
  [string]$Api = "http://127.0.0.1:8000",
  [string]$Gateway = "http://127.0.0.1:9010",
  [string]$Token = ""
)

$ErrorActionPreference = "Stop"

Write-Host "[preflight] health backend"
Invoke-RestMethod "$Api/health" | Out-Null
Write-Host "  ok"

Write-Host "[preflight] health gateway"
Invoke-RestMethod "$Gateway/health" | Out-Null
Write-Host "  ok"

if (-not [string]::IsNullOrWhiteSpace($Token)) {
  Write-Host "[preflight] admin readiness"
  Invoke-RestMethod "$Api/v1/admin/llm/readiness" -Headers @{ Authorization = "Bearer $Token" } | Out-Null
  Write-Host "  ok"
}

Write-Host "[preflight] strict no fallback runtime"
$env:ENVIRONMENT = "production"
$env:DEFAULT_LLM = "syntexa_native"
$env:OWN_MODEL_STRICT_NO_FALLBACK = "1"
python "scripts/own-model/verify_no_fallback.py" | Out-Null
Write-Host "  ok"

Write-Host "[preflight] smoke completion"
$body = @{
  model = "syntexa_small"
  messages = @(@{ role = "user"; content = "Teste enterprise." })
  max_tokens = 64
  temperature = 0.7
} | ConvertTo-Json -Depth 10
Invoke-RestMethod "$Gateway/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body | Out-Null
Write-Host "  ok"

Write-Host "[preflight] enterprise checks passed"
