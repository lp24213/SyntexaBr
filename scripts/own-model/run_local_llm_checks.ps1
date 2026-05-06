$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$env:PYTHONPATH = "$Root" + $(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" })
Set-Location $Root
Write-Host "=== dump_local_llm_state ==="
python scripts/own-model/dump_local_llm_state.py | Select-Object -First 80
if ($env:RUN_VERIFY_NO_FALLBACK -eq "1") {
    Write-Host "=== verify_no_fallback ==="
    python scripts/own-model/verify_no_fallback.py
}
Write-Host "[run_local_llm_checks] fim"
