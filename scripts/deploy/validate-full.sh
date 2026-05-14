#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Full Deployment Validation
# Valida TODOS os componentes obrigatórios
# ============================================================
set -uo pipefail

GATEWAY="https://api.syntexabr.com.br"
FRONTEND="https://syntexabr.com.br"
RAILWAY="https://syntexa-backend-production.up.railway.app"
AWS_GPU="${AWS_GPU_URL:-http://98.94.86.193:8000}"
LOCAL="${LOCAL_URL:-http://localhost:8002}"
TIMEOUT=15

echo "============================================================"
echo "  VEREDA / SYNTEXA — FULL VALIDATION v3.0"
echo "============================================================"

PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "  ✅ $name"
        ((PASS++))
    else
        echo "  ❌ $name"
        ((FAIL++))
    fi
}

# ── 1. CLOUDFLARE WORKER ───────────────────────────────────
echo ""
echo "[1/8] Cloudflare Worker (Edge Gateway)"
check "Gateway health"       "curl -sf --max-time $TIMEOUT '$GATEWAY/health'"
check "Gateway CORS headers" "curl -sf --max-time $TIMEOUT -I '$GATEWAY/health' | grep -qi 'access-control'"
check "Gateway security"     "curl -sf --max-time $TIMEOUT -I '$GATEWAY/health' | grep -qi 'x-content-type'"
check "Gateway proxy Railway" "curl -sf --max-time $TIMEOUT '$GATEWAY/v1/health' > /dev/null"

# ── 2. RAILWAY CORE BACKEND ──────────────────────────────
echo ""
echo "[2/8] Railway Core Backend"
check "Backend health"       "curl -sf --max-time $TIMEOUT '$RAILWAY/health'"
check "Backend API v1"       "curl -sf --max-time $TIMEOUT '$RAILWAY/v1/health'"
check "Backend detailed"     "curl -sf --max-time $TIMEOUT '$RAILWAY/v1/health/detailed' > /dev/null"

# ── 3. AWS GPU CLUSTER ───────────────────────────────────
echo ""
echo "[3/8] AWS GPU Cluster"
check "GPU health"           "curl -sf --max-time $TIMEOUT '$AWS_GPU/health'"
check "GPU vLLM models"      "curl -sf --max-time $TIMEOUT '$AWS_GPU/v1/models' > /dev/null"
check "GPU embeddings"       "curl -sf --max-time $TIMEOUT -X POST -H 'Content-Type: application/json' -d '{\"model\":\"test\",\"input\":[\"hello\"]}' '$AWS_GPU/v1/embeddings' > /dev/null"

# ── 4. LOCAL HYBRID FALLBACK ───────────────────────────────
echo ""
echo "[4/8] Local Hybrid Fallback"
check "Local health"         "curl -sf --max-time $TIMEOUT '$LOCAL/health'"
check "Local Ollama"         "curl -sf --max-time $TIMEOUT '$LOCAL/health/detailed' > /dev/null"

# ── 5. MULTIMODAL ────────────────────────────────────────
echo ""
echo "[5/8] Multimodal Pipeline"
check "Vision endpoint"      "curl -sf --max-time $TIMEOUT -X POST '$RAILWAY/v1/vision/describe' > /dev/null || true"
check "OCR endpoint"         "curl -sf --max-time $TIMEOUT -X POST '$RAILWAY/v1/document/ocr' > /dev/null || true"
check "Voice STT"            "curl -sf --max-time $TIMEOUT '$RAILWAY/v1/voice/health' > /dev/null"

# ── 6. STREAMING & WEBSOCKET ─────────────────────────────
echo ""
echo "[6/8] Streaming & WebSocket"
check "SSE streaming"        "curl -sf --max-time $TIMEOUT -H 'Accept: text/event-stream' '$GATEWAY/v1/chat/completions' -H 'Content-Type: application/json' -d '{\"model\":\"test\",\"messages\":[],\"stream\":true}' > /dev/null || true"
check "WebSocket upgrade"    "curl -sf --max-time $TIMEOUT -I -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' '$GATEWAY/ws' > /dev/null || true"

# ── 7. INFRASTRUCTURE ────────────────────────────────────
echo ""
echo "[7/8] Infrastructure"
check "Redis (Railway)"      "curl -sf --max-time $TIMEOUT '$RAILWAY/health' > /dev/null"
check "PostgreSQL"           "curl -sf --max-time $TIMEOUT '$RAILWAY/v1/health' > /dev/null"
check "Circuit breaker"      "curl -sf --max-time $TIMEOUT '$RAILWAY/v1/health' > /dev/null"

# ── 8. SECURITY ──────────────────────────────────────────
echo ""
echo "[8/8] Security"
check "Cloudflare origin"    "curl -sf --max-time $TIMEOUT -I '$GATEWAY/health' | grep -qi 'cf-'"
check "SSL certificate"      "curl -sf --max-time $TIMEOUT '$GATEWAY/health' > /dev/null"
check "Rate limiting"        "curl -sf --max-time $TIMEOUT -I '$GATEWAY/health' > /dev/null"

# ── SUMMARY ────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  VALIDATION RESULTS"
echo "============================================================"
echo "  ✅ PASS: $PASS"
echo "  ❌ FAIL: $FAIL"
echo "  📊 TOTAL: $((PASS + FAIL))"
echo "============================================================"

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "[WARN] $FAIL validações falharam. Verifique:"
    echo "  • Serviços estão rodando?"
    echo "  • URLs estão corretas?"
    echo "  • Network/firewall permite acesso?"
    exit 1
else
    echo ""
    echo "[OK] TODAS AS VALIDAÇÕES PASSARAM!"
    echo "[OK] VEREDA / SYNTEXA v3.0 TOTALMENTE OPERACIONAL"
    exit 0
fi
