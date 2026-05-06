param(
  [string]$Api = "http://127.0.0.1:8000",
  [string]$Token,
  [string]$Model = "syntexa_small"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Token)) {
  Write-Host "Uso: .\switch_active_model.ps1 -Api http://... -Token <bearer> -Model syntexa_small"
  exit 1
}

$headers = @{
  Authorization = "Bearer $Token"
  "Content-Type" = "application/json"
}
$body = @{ model_name = $Model } | ConvertTo-Json
Invoke-RestMethod "$Api/v1/admin/llm/active" -Method Post -Headers $headers -Body $body | ConvertTo-Json -Depth 5
