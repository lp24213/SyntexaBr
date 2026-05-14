#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Deploy Completo (All-in-One)
# ============================================================
set -euo pipefail

ENV="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo "  VEREDA / SYNTEXA — DEPLOY COMPLETO v3.0"
echo "  Ambiente: $ENV"
echo "============================================================"

# ── 1. VALIDATE ENV ────────────────────────────────────────
echo ""
echo "[1/8] Validando ambiente..."
if [ -f "$SCRIPT_DIR/../../.env" ]; then
    source "$SCRIPT_DIR/../../.env"
else
    echo "[WARN] .env não encontrado — usando valores padrão"
fi

# ── 2. TESTS ───────────────────────────────────────────────
echo ""
echo "[2/8] Executando testes..."
if [ -d "$SCRIPT_DIR/../../tests" ]; then
    (cd "$SCRIPT_DIR/../.." && python -m pytest tests/ -q --tb=short) || {
        echo "[ERRO] Testes falharam — abortando deploy"
        exit 1
    }
else
    echo "[SKIP] Diretório tests/ não encontrado"
fi

# ── 3. BUILD DOCKER IMAGES ───────────────────────────────
echo ""
echo "[3/8] Build Docker images..."
if command -v docker &> /dev/null; then
    (cd "$SCRIPT_DIR/../.." && docker build -t syntexa/backend:v3.0.0 -f Dockerfile.railway .)
    (cd "$SCRIPT_DIR/../../infrastructure/aws-gpu-cluster" && docker build -t syntexa/ai-worker-gpu:v3.0.0 -f Dockerfile.gpu .)
    (cd "$SCRIPT_DIR/../../infrastructure/local-hybrid" && docker build -t syntexa/local-hybrid:v3.0.0 -f Dockerfile.local .)
    echo "[OK] Imagens Docker buildadas"
else
    echo "[SKIP] Docker não disponível"
fi

# ── 4. DEPLOY CLOUDFLARE WORKER ──────────────────────────
echo ""
echo "[4/8] Deploy Cloudflare Worker..."
if command -v npx &> /dev/null; then
    (cd "$SCRIPT_DIR/../.." && npx wrangler deploy --env "$ENV") || echo "[WARN] Worker deploy falhou"
else
    echo "[SKIP] Wrangler CLI não disponível"
fi

# ── 5. DEPLOY RAILWAY ────────────────────────────────────
echo ""
echo "[5/8] Deploy Railway..."
if command -v railway &> /dev/null; then
    (cd "$SCRIPT_DIR/../.." && railway up --environment "$ENV") || echo "[WARN] Railway deploy falhou"
else
    echo "[SKIP] Railway CLI não disponível"
fi

# ── 6. DEPLOY AWS GPU ────────────────────────────────────
echo ""
echo "[6/8] Deploy AWS GPU Cluster..."
if [ -n "${AWS_HOST:-}" ] && [ -n "${AWS_KEY:-}" ]; then
    bash "$SCRIPT_DIR/deploy-aws-gpu.sh"
else
    echo "[SKIP] AWS_HOST/AWS_KEY não configurados"
fi

# ── 7. DEPLOY K8s (se disponível) ─────────────────────────
echo ""
echo "[7/8] Deploy Kubernetes..."
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
    bash "$SCRIPT_DIR/deploy-k8s.sh" "syntexa" "$ENV"
else
    echo "[SKIP] Kubernetes não disponível"
fi

# ── 8. VALIDATION ──────────────────────────────────────────
echo ""
echo "[8/8] Validação..."
bash "$SCRIPT_DIR/validate-deploy.sh" || echo "[WARN] Algumas validações falharam"

# ── SUMMARY ────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  DEPLOY v3.0 CONCLUÍDO"
echo "============================================================"
echo "  Gateway:   https://api.syntexabr.com.br"
echo "  Frontend:  https://syntexabr.com.br"
echo "  AWS GPU:   $AWS_BASE_URL"
echo "  Local:     $LOCAL_BASE_URL"
echo "============================================================"
