param(
    [string]$Api = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [int]$MaxAttempts = 30,
    [int]$SleepSec = 10
)
$ErrorActionPreference = "Stop"
$h = @{ Authorization = "Bearer $Token" }
for ($i = 0; $i -lt $MaxAttempts; $i++) {
    $r = Invoke-RestMethod -Uri "$Api/v1/admin/llm/readiness" -Headers $h -Method Get
    $ok = [bool]$r.runtime.ready
    Write-Host "[watch] tentativa $($i+1)/$MaxAttempts ready=$ok"
    if ($ok) {
        Write-Host "[watch] readiness OK"
        exit 0
    }
    Start-Sleep -Seconds $SleepSec
}
Write-Error "[watch] timeout sem readiness"
exit 1
