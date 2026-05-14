#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — GPU Cluster Bootstrap
# Executado automaticamente na criação da instância GPU
# ============================================================
set -euo pipefail

exec > >(tee /var/log/vereda-gpu-bootstrap.log) 2>&1

echo "[VEREDA] GPU Cluster Bootstrap iniciado em $(date)"

# 1. Atualizar sistema
echo "[VEREDA] Atualizando sistema..."
apt-get update && apt-get upgrade -y

# 2. Instalar drivers NVIDIA
echo "[VEREDA] Instalando drivers NVIDIA..."
apt-get install -y --no-install-recommends \
    linux-headers-$(uname -r) \
    build-essential \
    dkms \
    curl \
    wget \
    git \
    software-properties-common

# Adicionar repo NVIDIA
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
wget -qO - https://nvidia.github.io/libnvidia-container/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    tee /etc/apt/sources.list.d/libnvidia-container.list

# Instalar driver via ubuntu-drivers
apt-get install -y ubuntu-drivers-common
ubuntu-drivers autoinstall || true

# 3. Instalar CUDA
echo "[VEREDA] Instalando CUDA 12.1..."
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i cuda-keyring_1.1-1_all.deb
apt-get update
apt-get install -y cuda-toolkit-12-1

# 4. Instalar Docker
echo "[VEREDA] Instalando Docker..."
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

# 5. Instalar NVIDIA Container Toolkit
echo "[VEREDA] Instalando NVIDIA Container Toolkit..."
apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# 6. Verificar GPU
echo "[VEREDA] Verificando GPU..."
nvidia-smi

# 7. Criar diretório do projeto
echo "[VEREDA] Configurando VEREDA..."
mkdir -p /opt/vereda-gpu
cd /opt/vereda-gpu

# 8. Clonar/configurar código (simulado - em produção usar S3 ou git)
cat > docker-compose.gpu.yml << 'COMPOSE_EOF'
version: "3.9"
services:
  vllm:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    ports:
      - "8000:8000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - vllm-models:/root/.cache/huggingface
    command: >
      --model microsoft/DialoGPT-medium
      --max-model-len 4096
      --gpu-memory-utilization 0.9
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    restart: unless-stopped

  embeddings:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    ports:
      - "8001:8001"
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - SERVICE_MODE=embeddings
    volumes:
      - vllm-models:/root/.cache/huggingface
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.gpu.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - vllm
    restart: unless-stopped

volumes:
  vllm-models:
COMPOSE_EOF

cat > nginx.gpu.conf << 'NGINX_EOF'
user nginx;
worker_processes auto;
events { worker_connections 1024; }
http {
    upstream vllm { server vllm:8000; }
    upstream embeddings { server embeddings:8001; }
    server {
        listen 80;
        location /health { return 200 '{"status":"ok"}'; add_header Content-Type application/json; }
        location /v1/chat/completions { proxy_pass http://vllm; proxy_buffering off; }
        location /v1/embeddings { proxy_pass http://embeddings; }
        location /v1/models { proxy_pass http://vllm; }
    }
}
NGINX_EOF

# 9. Subir serviços
echo "[VEREDA] Subindo GPU cluster..."
docker compose -f docker-compose.gpu.yml pull
docker compose -f docker-compose.gpu.yml up -d

# 10. Healthcheck
echo "[VEREDA] Verificando saúde..."
sleep 60
for port in 8000 8001; do
    if curl -sf "http://localhost:$port/health" > /dev/null; then
        echo "[OK] Serviço na porta $port saudável"
    else
        echo "[WARN] Porta $port ainda carregando..."
    fi
done

# 11. Cloudflare Tunnel (se token configurado)
if [ -f /opt/vereda-gpu/cloudflared-token.txt ]; then
    echo "[VEREDA] Configurando Cloudflare Tunnel..."
    docker run -d --name cloudflared \
        --restart unless-stopped \
        -v /opt/vereda-gpu/cloudflared-token.txt:/etc/cloudflared/credentials.json:ro \
        cloudflare/cloudflared:latest tunnel run --token-file /etc/cloudflared/credentials.json
fi

echo "[VEREDA] GPU Cluster Bootstrap completo em $(date)"
