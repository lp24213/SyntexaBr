param(
  [string]$Api = "http://127.0.0.1:8000",
  [string]$Token,
  [string]$Candidate = "syntexa_small",
  [int]$Checks = 3,
  [double]$IntervalSec = 2.0,
  [bool]$RollbackOnFail = $true,
  [bool]$EnforceSlo = $true,
  [double]$MaxErrorRate = 0.08,
  [double]$MaxP95LatencyMs = 3500,
  [int]$MinRequestsForSlo = 50
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Token)) {
  Write-Host "Uso: .\promote_canary.ps1 -Api http://... -Token <bearer> -Candidate syntexa_small -Checks 3 -IntervalSec 2.0 -RollbackOnFail `$true -EnforceSlo `$true -MaxErrorRate 0.08 -MaxP95LatencyMs 3500 -MinRequestsForSlo 50"
  exit 1
}

$headers = @{ Authorization = "Bearer $Token"; "Content-Type" = "application/json" }
$body = @{
  candidate_model = $Candidate
  checks = $Checks
  interval_sec = $IntervalSec
  rollback_on_fail = $RollbackOnFail
  enforce_slo = $EnforceSlo
  max_error_rate = $MaxErrorRate
  max_p95_latency_ms = $MaxP95LatencyMs
  min_requests_for_slo = $MinRequestsForSlo
} | ConvertTo-Json

Invoke-RestMethod "$Api/v1/admin/llm/promote-canary" -Method Post -Headers $headers -Body $body | ConvertTo-Json -Depth 20
