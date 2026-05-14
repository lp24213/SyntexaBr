#!/bin/bash
set -e

echo "=========================================="
echo "SYNTEXA AI - ORACLE CLOUD DEPLOY"
echo "=========================================="

# Atualizar sistema
echo "[1/5] Atualizando sistema..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Instalar Docker
echo "[2/5] Instalando Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "Docker instalado. Relogue para usar sem sudo."
fi

# Instalar Docker Compose
echo "[3/5] Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt-get install -y docker-compose
fi

# Clonar ou copiar projeto
echo "[4/5] Preparando projeto..."
PROJECT_DIR="$HOME/syntexa-oracle"
mkdir -p "$PROJECT_DIR"

# Copiar arquivos (assumindo que estao no mesmo diretorio)
cp -r . "$PROJECT_DIR/" 2>/dev/null || true

cd "$PROJECT_DIR"

# Build e run
echo "[5/5] Build e start..."
sudo docker compose up -d --build

echo ""
echo "=========================================="
echo "DEPLOY CONCLUIDO!"
echo "=========================================="
echo "Health: http://$(curl -s ifconfig.me):8000/health"
echo "API:    http://$(curl -s ifconfig.me):8000/v1/chat/completions"
echo ""
echo "Para ver logs: sudo docker compose logs -f"
echo "Para parar:    sudo docker compose down"
echo "=========================================="
