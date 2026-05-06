# Guard periódico: readiness falhou -> POST /v1/admin/llm/rollback
param(
    [string]$Api = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [Parameter(Mandatory = $true)][string]$PreviousModel
)
$ErrorActionPreference = "Stop"
$headers = @{ Authorization = "Bearer $Token" }
$readiness = Invoke-RestMethod -Uri "$Api/v1/admin/llm/readiness" -Headers $headers -Method Get
if ($readiness.runtime.ready) {
    Write-Host "[guard] readiness OK"
    exit 0
}
Write-Host "[guard] readiness FALHOU — rollback para $PreviousModel"
$body = @{ target_model = $PreviousModel; reason = "periodic_canary_guard" } | ConvertTo-Json
Invoke-RestMethod -Uri "$Api/v1/admin/llm/rollback" -Headers $headers -Method Post -Body $body -ContentType "application/json"
exit 2
