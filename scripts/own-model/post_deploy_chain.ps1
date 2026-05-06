param(
    [string]$Api = "http://127.0.0.1:8000",
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$SnapshotDir = "./artifacts/ops-snapshots"
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
& "$here/watch_readiness.ps1" -Api $Api -Token $Token
& "$here/smoke_admin_llm.ps1" -Api $Api -Token $Token
& "$here/snapshot_ops_bundle.ps1" -Api $Api -Token $Token -OutDir $SnapshotDir
Write-Host "[chain] OK"
