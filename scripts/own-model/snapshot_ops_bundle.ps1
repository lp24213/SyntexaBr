param(
    [string]$Api = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$OutDir = "./artifacts/ops-snapshots"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$h = @{ Authorization = "Bearer $Token"; Accept = "application/json" }
$pairs = @(
    @("readiness", "/v1/admin/llm/readiness"),
    @("slo", "/v1/admin/llm/slo-snapshot"),
    @("policy", "/v1/admin/compliance/policy"),
    @("registry", "/v1/admin/llm/registry")
)
foreach ($x in $pairs) {
    $name = $x[0]
    $path = $x[1]
    Invoke-RestMethod -Uri "$Api$path" -Headers $h -Method Get |
        ConvertTo-Json -Depth 12 |
        Set-Content -Encoding utf8 (Join-Path $OutDir "${name}-${ts}.json")
}
Write-Host "[snapshot] gravado em $OutDir (*-$ts.json)"
