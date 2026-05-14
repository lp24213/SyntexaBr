#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Remote Setup Script (runs on AWS instance)
# ============================================================
set -euo pipefail

VEREDA_DIR="/home/ubuntu/vereda"
LOG="/home/ubuntu/vereda-setup.log"
exec > >(tee "$LOG") 2>&1

echo "[VEREDA] Setup iniciado em $(date)"
echo "[VEREDA] Host: $(hostname) | IP: $(curl -s ifconfig.me)"

# 1. Update system
echo "[VEREDA] Atualizando sistema..."
sudo apt-get update -y

# 2. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[VEREDA] Instalando Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker ubuntu
    sudo systemctl enable docker
    sudo systemctl start docker
    echo "[VEREDA] Docker instalado"
else
    echo "[VEREDA] Docker já instalado: $(docker --version)"
fi

# 3. Install docker-compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[VEREDA] Instalando docker-compose..."
    sudo apt-get install -y docker-compose-plugin
fi

# 4. Install NVIDIA drivers (if GPU present)
if lspci | grep -i nvidia &> /dev/null; then
    echo "[VEREDA] GPU NVIDIA detectada"
    if ! command -v nvidia-smi &> /dev/null; then
        echo "[VEREDA] Instalando drivers NVIDIA..."
        sudo apt-get install -y --no-install-recommends linux-headers-$(uname -r) build-essential
        sudo ubuntu-drivers autoinstall
    fi
    # Install NVIDIA Container Toolkit
    if [ ! -f /etc/apt/sources.list.d/nvidia-container-toolkit.list ]; then
        distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
        curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
        curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
        sudo apt-get update
        sudo apt-get install -y nvidia-container-toolkit
        sudo nvidia-ctk runtime configure --runtime=docker
        sudo systemctl restart docker
    fi
    nvidia-smi || echo "[WARN] nvidia-smi não disponível ainda"
else
    echo "[VEREDA] Sem GPU NVIDIA detectada — modo CPU/Orchestrator"
fi

# 5. Create nginx config
echo "[VEREDA] Criando nginx config..."
cat > "$VEREDA_DIR/nginx.gpu.conf" << 'EOF'
user nginx;
worker_processes auto;
events { worker_connections 1024; }
http {
    upstream vllm { server vllm:8000; }
    upstream embeddings { server embeddings:8001; }
    server {
        listen 80;
        location /health { return 200 '{"status":"ok","mode":"vereda-aws"}'; add_header Content-Type application/json; }
        location /v1/chat/completions { proxy_pass http://vllm; proxy_buffering off; proxy_read_timeout 300s; }
        location /v1/embeddings { proxy_pass http://embeddings; }
        location /v1/models { proxy_pass http://vllm; }
    }
}
EOF

# 6. Pull and start services
echo "[VEREDA] Subindo serviços..."
cd "$VEREDA_DIR"

if lspci | grep -i nvidia &> /dev/null; then
    # GPU mode
    echo "[VEREDA] Modo GPU — subindo vLLM + embeddings"
    docker compose -f docker-compose.gpu.yml pull
    docker compose -f docker-compose.gpu.yml up -d
else
    # CPU/Orchestrator mode
    echo "[VEREDA] Modo CPU — subindo nginx + redis + monitor"
    cat > "$VEREDA_DIR/docker-compose.orch.yml" << 'ORCH'
version: "3.9"
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.gpu.conf:/etc/nginx/nginx.conf:ro
    restart: unless-stopped
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    restart: unless-stopped
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    restart: unless-stopped
ORCH
    docker compose -f docker-compose.orch.yml up -d
fi

# 7. Health check
echo "[VEREDA] Health check..."
sleep 10
for port in 80 8000 8001; do
    if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "[OK] Porta $port: SAUDÁVEL"
    else
        echo "[WARN] Porta $port: não respondeu ainda"
    fi
done

# 8. Create systemd service for auto-restart
echo "[VEREDA] Criando systemd service..."
sudo tee /etc/systemd/system/vereda.service > /dev/null << EOF
[Unit]
Description=VEREDA AI Worker
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=ubuntu
WorkingDirectory=$VEREDA_DIR
ExecStart=/usr/bin/docker compose -f docker-compose.gpu.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.gpu.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.gpu.yml restart

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vereda.service

echo "[VEREDA] Setup completo em $(date)"
echo "[VEREDA] Logs: $LOG"
