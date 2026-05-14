#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Deploy na Instância AWS Existente
# i-0068bdc3f2152d1f1 (us-east-1, 98.94.86.193)
# ============================================================
set -euo pipefail

AWS_HOST="${AWS_HOST:-98.94.86.193}"
AWS_KEY="${AWS_KEY:-$HOME/Downloads/vereda-key.pem}"
REMOTE_DIR="/opt/vereda"

echo "============================================================"
echo "  VEREDA / SYNTEXA — Deploy na Instância Existente"
echo "  Host: $AWS_HOST"
echo "============================================================"

# ── VALIDAÇÃO ──────────────────────────────────────────────
if [ ! -f "$AWS_KEY" ]; then
    echo "[ERRO] Chave SSH não encontrada: $AWS_KEY"
    echo "       Configure: export AWS_KEY=/caminho/para/key.pem"
    exit 1
fi

chmod 400 "$AWS_KEY" 2>/dev/null || true

# ── AGUARDAR SSH ───────────────────────────────────────────
echo "[VEREDA] Aguardando SSH..."
TRIES=0
while [ $TRIES -lt 30 ]; do
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i "$AWS_KEY" "ubuntu@$AWS_HOST" "echo OK" > /dev/null 2>&1; then
        echo "[OK] SSH conectado"
        break
    fi
    sleep 2
    ((TRIES++))
done

if [ $TRIES -ge 30 ]; then
    echo "[ERRO] SSH indisponível. Verifique:"
    echo "  1. Security Group permite porta 22"
    echo "  2. Instância está running"
    echo "  3. Chave SSH correta"
    exit 1
fi

# ── PREPARAR DIRETÓRIO REMOTO ─────────────────────────────
echo "[VEREDA] Preparando diretório remoto..."
ssh -i "$AWS_KEY" "ubuntu@$AWS_HOST" "sudo mkdir -p $REMOTE_DIR && sudo chown ubuntu:ubuntu $REMOTE_DIR"

# ── COPIAR ARQUIVOS ──────────────────────────────────────
echo "[VEREDA] Copiando arquivos..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# GPU cluster files
rsync -avz -e "ssh -i $AWS_KEY -o StrictHostKeyChecking=accept-new" \
    --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    "$PROJECT_ROOT/infrastructure/aws-gpu-cluster/scripts/" \
    "ubuntu@$AWS_HOST:$REMOTE_DIR/scripts/"

scp -i "$AWS_KEY" -o StrictHostKeyChecking=accept-new \
    "$PROJECT_ROOT/infrastructure/aws-gpu-cluster/docker-compose.gpu.yml" \
    "ubuntu@$AWS_HOST:$REMOTE_DIR/"

scp -i "$AWS_KEY" -o StrictHostKeyChecking=accept-new \
    "$PROJECT_ROOT/infrastructure/aws-gpu-cluster/config/nginx.gpu.conf" \
    "ubuntu@$AWS_HOST:$REMOTE_DIR/"

scp -i "$AWS_KEY" -o StrictHostKeyChecking=accept-new \
    "$PROJECT_ROOT/infrastructure/aws-gpu-cluster/main.py" \
    "ubuntu@$AWS_HOST:$REMOTE_DIR/"

# ── EXECUTAR SETUP ─────────────────────────────────────────
echo "[VEREDA] Executando setup remoto..."
ssh -i "$AWS_KEY" "ubuntu@$AWS_HOST" "bash $REMOTE_DIR/scripts/setup-aws.sh"

# ── VERIFICAR SAÚDE ──────────────────────────────────────
echo "[VEREDA] Verificando saúde dos serviços..."
sleep 10
for port in 8000 8001 8002 8003; do
    if ssh -i "$AWS_KEY" "ubuntu@$AWS_HOST" "curl -sf http://localhost:$port/health" > /dev/null 2>&1; then
        echo "[OK] Porta $port: SAUDÁVEL"
    else
        echo "[WARN] Porta $port: NÃO RESPONDEU"
    fi
done

# ── CONFIGURAR COMO ORCHESTRATOR ─────────────────────────
echo "[VEREDA] Configurando como orchestrator..."
ssh -i "$AWS_KEY" "ubuntu@$AWS_HOST" "bash -c 'cat > /etc/systemd/system/vereda-orchestrator.service << EOF
[Unit]
Description=VEREDA Orchestrator
After=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$REMOTE_DIR
ExecStart=/usr/bin/docker compose -f docker-compose.gpu.yml up
ExecStop=/usr/bin/docker compose -f docker-compose.gpu.yml down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable vereda-orchestrator'
"

echo ""
echo "============================================================"
echo "  DEPLOY NA INSTÂNCIA EXISTENTE CONCLUÍDO"
echo "  Host: $AWS_HOST"
echo "  Diretório: $REMOTE_DIR"
echo "============================================================"
