param(
    [string]$Api = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token
)
$ErrorActionPreference = "Stop"
$h = @{ Authorization = "Bearer $Token"; Accept = "application/json" }
foreach ($path in @(
        "/v1/admin/llm/readiness",
        "/v1/admin/llm/slo-snapshot",
        "/v1/admin/llm/registry",
        "/v1/admin/compliance/policy",
        "/v1/admin/system/status")) {
    Write-Host "== GET $path"
    $r = Invoke-RestMethod -Uri "$Api$path" -Headers $h -Method Get
    $j = ($r | ConvertTo-Json -Depth 10)
    if ($j.Length -gt 2000) { $j = $j.Substring(0, 2000) + "..." }
    Write-Host $j
}
Write-Host "[smoke] OK"
