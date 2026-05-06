param(
  [string]$Api = "http://127.0.0.1:8000",
  [string]$Token,
  [string]$Candidate = "syntexa_small",
  [bool]$RollbackOnFail = $true
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Token)) {
  Write-Host "Uso: .\deploy_blue_green.ps1 -Api http://... -Token <bearer> -Candidate syntexa_small -RollbackOnFail `$true"
  exit 1
}

$headers = @{
  Authorization = "Bearer $Token"
  "Content-Type" = "application/json"
}

Write-Host "[blue-green] registry atual"
Invoke-RestMethod "$Api/v1/admin/llm/registry" -Headers $headers | ConvertTo-Json -Depth 10

Write-Host "[blue-green] promovendo candidato=$Candidate rollback_on_fail=$RollbackOnFail"
$body = @{
  candidate_model = $Candidate
  rollback_on_fail = $RollbackOnFail
} | ConvertTo-Json
Invoke-RestMethod "$Api/v1/admin/llm/promote-blue-green" -Method Post -Headers $headers -Body $body | ConvertTo-Json -Depth 10

Write-Host "[blue-green] readiness pós-promoção"
Invoke-RestMethod "$Api/v1/admin/llm/readiness" -Headers $headers | ConvertTo-Json -Depth 10
