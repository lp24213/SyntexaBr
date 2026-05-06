param(
  [string]$Api = "http://127.0.0.1:8000",
  [string]$Token,
  [string]$PreviousModel = "syntexa_native",
  [int]$WindowSec = 300,
  [int]$PollSec = 15,
  [double]$MaxErrorRate = 0.10,
  [double]$MaxP95Ms = 4000
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Token)) {
  Write-Host "Uso: .\monitor_post_deploy.ps1 -Api http://... -Token <bearer> -PreviousModel syntexa_native"
  exit 1
}

$headers = @{ Authorization = "Bearer $Token"; "Content-Type" = "application/json" }
$deadline = (Get-Date).AddSeconds($WindowSec)
Write-Host "[monitor] janela de observação ${WindowSec}s"
while ((Get-Date) -lt $deadline) {
  $snap = Invoke-RestMethod "$Api/v1/admin/llm/slo-snapshot" -Headers $headers
  $slo = $snap.slo
  $err = [double]($slo.error_rate)
  $p95 = [double]($slo.p95_latency_ms)
  Write-Host "[monitor] error_rate=$err p95_ms=$p95"
  if ($err -gt $MaxErrorRate -or $p95 -gt $MaxP95Ms) {
    Write-Host "[monitor] SLO violado, rollback automático para $PreviousModel"
    $body = @{ model_name = $PreviousModel } | ConvertTo-Json
    Invoke-RestMethod "$Api/v1/admin/llm/active" -Method Post -Headers $headers -Body $body | Out-Null
    Write-Host "[monitor] rollback concluído"
    exit 2
  }
  Start-Sleep -Seconds $PollSec
}
Write-Host "[monitor] janela concluída sem violação de SLO"
