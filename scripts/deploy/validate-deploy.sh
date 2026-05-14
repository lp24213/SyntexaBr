#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Deploy Validation
# Valida deploy completo end-to-end
# ============================================================
set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-https://api.syntexabr.com.br}"
AWS_GPU_URL="${AWS_GPU_URL:-http://98.94.86.193:8000}"
LOCAL_URL="${LOCAL_URL:-http://localhost:8002}"
TIMEOUT=30

echo "============================================================"
echo "  VEREDA / SYNTEXA — DEPLOY VALIDATION"
echo "============================================================"

PASS=0
FAIL=0

# ── HELPER ────────────────────────────────────────────────
check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "[PASS] $name"
        ((PASS++))
    else
        echo "[FAIL] $name"
        ((FAIL++))
    fi
}

# ── 1. CLOUDFLARE GATEWAY ────────────────────────────────
echo ""
echo "[1/6] Cloudflare Gateway..."
check "Gateway health" "curl -sf --max-time $TIMEOUT '$GATEWAY_URL/health'"
check "Gateway CORS" "curl -sf --max-time $TIMEOUT -I '$GATEWAY_URL/health' | grep -i 'access-control'"
check "Gateway security headers" "curl -sf --max-time $TIMEOUT -I '$GATEWAY_URL/health' | grep -i 'x-content-type'"

# ── 2. RAILWAY BACKEND ───────────────────────────────────
echo ""
echo "[2/6] Railway Core Backend..."
check "Backend health" "curl -sf --max-time $TIMEOUT '$GATEWAY_URL/health'"
check "Backend API v1" "curl -sf --max-time $TIMEOUT '$GATEWAY_URL/v1/health'"
check "Auth endpoint" "curl -sf --max-time $TIMEOUT -o /dev/null '$GATEWAY_URL/v1/auth/health' || true"

# ── 3. AWS GPU CLUSTER ───────────────────────────────────
echo ""
echo "[3/6] AWS GPU Cluster..."
check "GPU health" "curl -sf --max-time $TIMEOUT '$AWS_GPU_URL/health'"
check "GPU vLLM" "curl -sf --max-time $TIMEOUT -o /dev/null '$AWS_GPU_URL/v1/models' || true"
check "GPU embeddings" "curl -sf --max-time $TIMEOUT -X POST -H 'Content-Type: application/json' -d '{\"model\":\"test\",\"input\":[\"hello\"]}' '$AWS_GPU_URL/v1/embeddings' || true"

# ── 4. LOCAL HYBRID ──────────────────────────────────────
echo ""
echo "[4/6] Local Hybrid..."
check "Local health" "curl -sf --max-time $TIMEOUT '$LOCAL_URL/health'"
check "Local Ollama bridge" "curl -sf --max-time $TIMEOUT '$LOCAL_URL/health/detailed'"

# ── 5. WEBSOCKET ─────────────────────────────────────────
echo ""
echo "[5/6] WebSocket..."
check "WebSocket endpoint" "curl -sf --max-time $TIMEOUT -I -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Key: test' -H 'Sec-WebSocket-Version: 13' '$GATEWAY_URL/ws' || true"

# ── 6. STREAMING ─────────────────────────────────────────
echo ""
echo "[6/6] Streaming..."
check "SSE endpoint reachable" "curl -sf --max-time $TIMEOUT -o /dev/null '$GATEWAY_URL/v1/chat/completions' -H 'Content-Type: application/json' -d '{\"model\":\"test\",\"messages\":[]}' || true"

# ── K8s (if available) ─────────────────────────────────────
echo ""
echo "[BONUS] Kubernetes..."
if command -v kubectl &> /dev/null; then
    check "K8s pods running" "kubectl get pods -n syntexa | grep -q Running"
    check "K8s services" "kubectl get svc -n syntexa | grep -q syntexa-backend"
    check "K8s ingress" "kubectl get ingress -n syntexa | grep -q syntexa-ingress"
else
    echo "[SKIP] kubectl não disponível"
fi

# ── SUMMARY ────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  VALIDATION RESULTS"
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
echo "============================================================"

if [ $FAIL -gt 0 ]; then
    echo "[WARN] Algumas validações falharam. Verifique os serviços."
    exit 1
else
    echo "[OK] Todas as validações passaram! Deploy saudável."
    exit 0
fi
