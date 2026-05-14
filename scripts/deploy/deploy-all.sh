#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Deploy Completo (Hybrid)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENVIRONMENT="${1:-staging}"

echo "============================================================"
echo "  VEREDA / SYNTEXA — DEPLOY COMPLETO"
echo "  Ambiente: $ENVIRONMENT"
echo "============================================================"

# ── VALIDAÇÃO ──────────────────────────────────────────────
if [ ! -f "$PROJECT_ROOT/wrangler.toml" ]; then
    echo "[ERRO] wrangler.toml não encontrado"
    exit 1
fi

# ── 1. DEPLOY CLOUDFLARE WORKERS ──────────────────────────
echo ""
echo "[1/4] Deploy Cloudflare Workers..."
cd "$PROJECT_ROOT"
if command -v npx &> /dev/null; then
    npx wrangler deploy --env "$ENVIRONMENT" || echo "[WARN] Worker deploy falhou — verifique wrangler login"
else
    echo "[WARN] wrangler CLI não encontrado — pulando deploy do Worker"
fi

# ── 2. DEPLOY RAILWAY ─────────────────────────────────────
echo ""
echo "[2/4] Deploy Railway Core..."
cd "$PROJECT_ROOT"
if command -v railway &> /dev/null; then
    railway up --environment "$ENVIRONMENT" || echo "[WARN] Railway deploy falhou"
else
    echo "[WARN] Railway CLI não encontrado — pulando deploy Railway"
fi

# ── 3. DEPLOY AWS GPU CLUSTER ─────────────────────────────
echo ""
echo "[3/4] Deploy AWS GPU Cluster..."
AWS_HOST="${AWS_HOST:-}"
AWS_KEY="${AWS_KEY:-}"
if [ -n "$AWS_HOST" ] && [ -n "$AWS_KEY" ]; then
    echo "[VEREDA] Copiando arquivos para AWS GPU..."
    rsync -avz -e "ssh -i $AWS_KEY -o StrictHostKeyChecking=accept-new" \
        --exclude='.git' --exclude='frontend/node_modules' \
        "$PROJECT_ROOT/infrastructure/aws-gpu-cluster/" \
        "ubuntu@$AWS_HOST:/opt/syntexa-gpu/"

    echo "[VEREDA] Executando setup remoto..."
    ssh -i "$AWS_KEY" -o StrictHostKeyChecking=accept-new "ubuntu@$AWS_HOST" \
        "sudo bash /opt/syntexa-gpu/scripts/setup-aws.sh"
else
    echo "[WARN] AWS_HOST ou AWS_KEY não configurados — pulando deploy AWS"
    echo "       Configure: export AWS_HOST=ec2-xx-xx-xx-xx.compute.amazonaws.com"
    echo "       Configure: export AWS_KEY=/caminho/para/key.pem"
fi

# ── 4. VERIFICAÇÃO PÓS-DEPLOY ─────────────────────────────
echo ""
echo "[4/4] Verificação pós-deploy..."

# Worker health (via Cloudflare)
if curl -sf "https://api.syntexabr.com.br/health" > /dev/null 2>&1; then
    echo "[OK] Cloudflare Gateway: SAUDÁVEL"
else
    echo "[WARN] Cloudflare Gateway: NÃO VERIFICADO"
fi

# Railway health
if curl -sf "https://syntexa-backend-production.up.railway.app/health" > /dev/null 2>&1; then
    echo "[OK] Railway Core: SAUDÁVEL"
else
    echo "[WARN] Railway Core: NÃO VERIFICADO"
fi

# AWS GPU health
if [ -n "$AWS_HOST" ]; then
    if ssh -i "$AWS_KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 "ubuntu@$AWS_HOST" \
        "curl -sf http://localhost:8000/health > /dev/null" 2>/dev/null; then
        echo "[OK] AWS GPU Cluster: SAUDÁVEL"
    else
        echo "[WARN] AWS GPU Cluster: NÃO VERIFICADO"
    fi
fi

echo ""
echo "============================================================"
echo "  DEPLOY CONCLUÍDO"
echo "============================================================"
