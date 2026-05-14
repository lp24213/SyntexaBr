# ============================================================
# VEREDA / SYNTEXA — Full Deployment Validation (PowerShell)
# ============================================================
$GATEWAY    = "https://api.syntexabr.com.br"
$RAILWAY    = "https://syntexa-backend-production.up.railway.app"
$AWS_ORCH   = "http://98.94.86.193"
$TIMEOUT    = 15

$PASS = 0
$FAIL = 0

function Test-Endpoint($Name, $Url) {
    try {
        $resp = Invoke-WebRequest -Uri $Url -TimeoutSec $TIMEOUT -UseBasicParsing -ErrorAction Stop
        Write-Host "  [OK]   $Name" -ForegroundColor Green
        $script:PASS++
    } catch {
        Write-Host "  [FAIL] $Name" -ForegroundColor Red
        $script:FAIL++
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  VEREDA / SYNTEXA — FULL VALIDATION v3.0" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n[1/6] Cloudflare Worker (Edge Gateway)" -ForegroundColor Yellow
Test-Endpoint "Gateway health"        "$GATEWAY/health"
Test-Endpoint "Gateway proxy Railway" "$GATEWAY/v1/health"

Write-Host "`n[2/6] Railway Core Backend" -ForegroundColor Yellow
Test-Endpoint "Backend health"       "$RAILWAY/health"
Test-Endpoint "Backend API v1"       "$RAILWAY/v1/health"

Write-Host "`n[3/6] AWS Orchestrator (t3.micro)" -ForegroundColor Yellow
Test-Endpoint "AWS orch health"      "$AWS_ORCH/health"
Test-Endpoint "AWS orch nginx"       "$AWS_ORCH"
Test-Endpoint "AWS redis"          "$AWS_ORCH:6379"  # This will likely fail from external

Write-Host "`n[4/6] Multimodal Pipeline (via Railway)" -ForegroundColor Yellow
Test-Endpoint "Voice STT health"    "$RAILWAY/v1/voice/health"

Write-Host "`n[5/6] Streaming & WebSocket" -ForegroundColor Yellow
Test-Endpoint "Gateway reachable"   "$GATEWAY"

Write-Host "`n[6/6] GPU Cluster (g5.xlarge)" -ForegroundColor Yellow
# GPU cluster not yet provisioned — mark as expected failure
Write-Host "  [SKIP] GPU cluster (aguardando provisionamento)" -ForegroundColor Yellow

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RESULTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PASS: $PASS" -ForegroundColor Green
Write-Host "  FAIL: $FAIL" -ForegroundColor Red
Write-Host "  SKIP: 1 (GPU cluster)" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

if ($FAIL -eq 0) {
    Write-Host "`n[OK] VALIDAÇÃO COMPLETA — SISTEMA OPERACIONAL" -ForegroundColor Green
} else {
    Write-Host "`n[WARN] $FAIL validações falharam" -ForegroundColor Yellow
}
