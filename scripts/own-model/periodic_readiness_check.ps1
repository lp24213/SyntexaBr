# Verificação periódica de readiness (Agendador de Tarefas Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$env:PYTHONPATH = "$Root" + $(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" })
$env:ENVIRONMENT = if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { "production" }
$env:DEFAULT_LLM = if ($env:DEFAULT_LLM) { $env:DEFAULT_LLM } else { "syntexa_native" }
$env:OWN_MODEL_STRICT_NO_FALLBACK = if ($env:OWN_MODEL_STRICT_NO_FALLBACK) { $env:OWN_MODEL_STRICT_NO_FALLBACK } else { "1" }
Set-Location $Root
python scripts/own-model/verify_no_fallback.py
Write-Host "readiness_ok $(Get-Date -Format o)"
