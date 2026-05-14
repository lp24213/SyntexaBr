#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Deploy AWS GPU Cluster
# ============================================================
set -euo pipefail

AWS_HOST="${AWS_HOST:-}"
AWS_KEY="${AWS_KEY:-}"
LOCAL_DIR="${LOCAL_DIR:-./infrastructure/aws-gpu-cluster}"
REMOTE_DIR="/opt/syntexa-gpu"

echo "[VEREDA] Deploy AWS GPU Cluster"
echo "  Host: $AWS_HOST"
echo "  Dir:  $REMOTE_DIR"

if [ -z "$AWS_HOST" ] || [ -z "$AWS_KEY" ]; then
    echo "[ERRO] Configure AWS_HOST e AWS_KEY"
    echo "  export AWS_HOST=ec2-xx-xx-xx-xx.compute.amazonaws.com"
    echo "  export AWS_KEY=/caminho/para/key.pem"
    exit 1
fi

# Copiar arquivos
echo "[VEREDA] Copiando arquivos..."
rsync -avz -e "ssh -i $AWS_KEY -o StrictHostKeyChecking=accept-new" \
    --exclude='__pycache__' \
    "$LOCAL_DIR/" \
    "ubuntu@$AWS_HOST:$REMOTE_DIR/"

# Executar setup remoto
echo "[VEREDA] Executando setup remoto..."
ssh -i "$AWS_KEY" -o StrictHostKeyChecking=accept-new "ubuntu@$AWS_HOST" \
    "sudo bash $REMOTE_DIR/scripts/setup-aws.sh"

echo "[OK] AWS GPU deploy concluído"
