param(
    [string]$Api = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [int]$Limit = 80
)
$ErrorActionPreference = "Stop"
$h = @{ Authorization = "Bearer $Token" }
Invoke-RestMethod -Uri "$Api/v1/admin/compliance/audit?action_prefix=llm_&limit=$Limit" -Headers $h -Method Get |
    ConvertTo-Json -Depth 8
