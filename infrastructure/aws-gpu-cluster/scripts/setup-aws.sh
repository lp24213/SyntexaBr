#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — AWS GPU Cluster Setup
# Executar na EC2 GPU (g5.xlarge / g5.2xlarge / p4d)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="syntexa-gpu"

echo "[VEREDA] Iniciando setup do cluster GPU na AWS..."

# 1. Atualizar sistema
echo "[VEREDA] Atualizando pacotes..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Instalar Docker
echo "[VEREDA] Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    sudo systemctl enable docker
    sudo systemctl start docker
fi

# 3. Instalar NVIDIA Container Toolkit
echo "[VEREDA] Instalando NVIDIA Container Toolkit..."
if ! command -v nvidia-ctk &> /dev/null; then
    distribution=$(. /etc/os-release; echo "$ID$VERSION_ID")
    curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
    curl -s -L "https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list" | \
        sudo tee /etc/apt/sources.list.d/libnvidia-container.list
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
fi

# 4. Verificar GPU
echo "[VEREDA] Verificando GPU..."
nvidia-smi

# 5. Criar diretório do projeto
echo "[VEREDA] Configurando diretório do projeto..."
mkdir -p /opt/$PROJECT_NAME
cd /opt/$PROJECT_NAME

# 6. Copiar arquivos (assumir que foram scp/rsync antes)
echo "[VEREDA] Verificando arquivos de configuração..."
if [ ! -f "docker-compose.gpu.yml" ]; then
    echo "[ERRO] docker-compose.gpu.yml não encontrado. Faça upload dos arquivos primeiro."
    exit 1
fi

# 7. Subir cluster
echo "[VEREDA] Subindo cluster GPU com Docker Compose..."
sudo docker compose -f docker-compose.gpu.yml pull
sudo docker compose -f docker-compose.gpu.yml up -d

# 8. Verificar saúde
echo "[VEREDA] Verificando saúde dos serviços..."
sleep 30
for port in 8000 8001 8002 8003; do
    if curl -sf "http://localhost:$port/health" > /dev/null; then
        echo "[OK] Serviço na porta $port saudável"
    else
        echo "[WARN] Serviço na porta $port não respondeu ainda (pode estar carregando)"
    fi
done

# 9. Configurar Cloudflare Tunnel (se configurado)
if [ -f "/etc/systemd/system/cloudflared.service" ]; then
    echo "[VEREDA] Reiniciando Cloudflare Tunnel..."
    sudo systemctl restart cloudflared
fi

echo "[VEREDA] Setup completo! GPU cluster operacional."
echo "[VEREDA] Portas: vLLM(8000) Embeddings(8001) Vision(8002) Voice(8003)"
