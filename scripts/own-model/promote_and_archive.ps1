param(
    [string]$Api = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [Parameter(Mandatory = $true)][string]$Candidate,
    [string]$OutDir = "./artifacts/promotions"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$headers = @{
    Authorization = "Bearer $Token"
    "Content-Type" = "application/json"
}
if ($env:FREEZE_BYPASS_SECRET) {
    $headers["X-Syntexa-Freeze-Bypass"] = $env:FREEZE_BYPASS_SECRET
}
$body = @{ candidate_model = $Candidate; rollback_on_fail = $true } | ConvertTo-Json
$outPath = Join-Path $OutDir "promote-bg-${Candidate}-${ts}.json"
$r = Invoke-RestMethod -Uri "$Api/v1/admin/llm/promote-blue-green" -Headers $headers -Method Post -Body $body
$r | ConvertTo-Json -Depth 25 | Set-Content -Encoding utf8 $outPath
Write-Host "[archive] $outPath"
