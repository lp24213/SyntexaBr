#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Orchestrator Bootstrap
# Executado na t3.micro existente
# ============================================================
set -euo pipefail

exec > >(tee /var/log/vereda-orch-bootstrap.log) 2>&1

echo "[VEREDA] Orchestrator Bootstrap iniciado em $(date)"

# 1. Atualizar
apt-get update && apt-get upgrade -y

# 2. Instalar dependências
apt-get install -y \
    docker.io docker-compose-plugin \
    redis-server \
    nginx \
    curl wget git \
    python3 python3-pip \
    nodejs npm \
    prometheus-node-exporter

# 3. Configurar Docker
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

# 4. Configurar Redis
cat >> /etc/redis/redis.conf << 'EOF'
maxmemory 512mb
maxmemory-policy allkeys-lru
appendonly yes
bind 0.0.0.0
protected-mode no
EOF
systemctl enable redis-server
systemctl restart redis-server

# 5. Instalar Cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared.deb || apt-get install -f -y

# 6. Criar diretório VEREDA
mkdir -p /opt/vereda
cd /opt/vereda

# 7. Configurar como orchestrator
cat > docker-compose.orch.yml << 'EOF'
version: "3.9"
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.orch.conf:/etc/nginx/nginx.conf:ro
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=vereda-admin
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    restart: unless-stopped
EOF

# 8. Subir
docker compose -f docker-compose.orch.yml up -d

echo "[VEREDA] Orchestrator Bootstrap completo em $(date)"
