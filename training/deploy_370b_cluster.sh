#!/bin/bash
# SYNTEXA 370B CLUSTER DEPLOY
# Setup para treinamento distribuído em cluster GPU
# Requer: 66x H100 80GB (ou equivalente) para treino BF16
#          5x H100 80GB para inference BF16
#          3x H100 80GB para inference INT4

set -e

NODES=${NODES:-8}
GPUS_PER_NODE=${GPUS_PER_NODE:-8}
MASTER_ADDR=${MASTER_ADDR:-$(hostname -I | awk '{print $1}')}
MASTER_PORT=${MASTER_PORT:-29500}
WORLD_SIZE=$((NODES * GPUS_PER_NODE))

echo "=================================================="
echo "SYNTEXA 370B CLUSTER DEPLOY"
echo "=================================================="
echo "  Nodes:         $NODES"
echo "  GPUs/node:     $GPUS_PER_NODE"
echo "  World size:    $WORLD_SIZE"
echo "  Master:        $MASTER_ADDR:$MASTER_PORT"
echo "=================================================="

# Verificações
command -v python3 >/dev/null 2>&1 || { echo "python3 não encontrado"; exit 1; }
command -v nvcc >/dev/null 2>&1 || { echo "CUDA não encontrado"; exit 1; }

# Instalar dependências
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -q deepspeed accelerate
pip install -q sentencepiece protobuf

echo "[OK] Dependências instaladas"

# Testar NCCL
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'Devices: {torch.cuda.device_count()}')"

# Iniciar treinamento com torchrun / deepspeed
DEEPSPEED_CONFIG="training/deepspeed_370b_zero3.json"
DATA="data/syntexa_corpus_curated.jsonl"
OUTPUT="checkpoints/foundation_370b"

echo "[INFO] Iniciando treinamento 370B..."

torchrun \
    --nnodes=$NODES \
    --nproc_per_node=$GPUS_PER_NODE \
    --rdzv_id=syntexa_370b \
    --rdzv_backend=c10d \
    --rdzv_endpoint=$MASTER_ADDR:$MASTER_PORT \
    training/train_370b.py \
    --data $DATA \
    --output-dir $OUTPUT \
    --epochs 1 \
    --batch-size 1 \
    --seq-len 4096 \
    --steps-per-epoch 10000 \
    --lr 1e-4 \
    --checkpoint-every 500 \
    --deepspeed-config $DEEPSPEED_CONFIG

echo "[OK] Treinamento iniciado"
