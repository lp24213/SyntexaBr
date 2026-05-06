param([string]$Base = "http://127.0.0.1:8000")
$ErrorActionPreference = "Stop"
$u = $Base.TrimEnd("/") + "/metrics"
(Invoke-WebRequest -Uri $u -UseBasicParsing).Content.Split("`n")[0..199] -join "`n"
Write-Host "..."
