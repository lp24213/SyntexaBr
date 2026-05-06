#!/usr/bin/env bash
# Provisiona uma VM Azure para rodar Text Generation Inference (TGI) ou Ollama com GPU.
# Uso local: configure AZURE_SUBSCRIPTION_ID, RESOURCE_GROUP, VM_NAME, VM_SIZE, LOCATION, SSH_PUBLIC_KEY
# Requer: `az cli` autenticado (`az login`) e `jq` instalado.
set -euo pipefail

SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
RESOURCE_GROUP="${RESOURCE_GROUP:-syntexa-rg}"
LOCATION="${LOCATION:-eastus}"
VM_NAME="${VM_NAME:-syntexa-llm-01}"
VM_SIZE="${VM_SIZE:-Standard_NC6s_v3}"
SSH_USER="${SSH_USER:-azureuser}"
SSH_PUBLIC_KEY_PATH="${SSH_PUBLIC_KEY_PATH:-$HOME/.ssh/id_rsa.pub}"
IMAGE="UbuntuLTS"

if [ -z "$SUBSCRIPTION_ID" ]; then
  echo "ERRO: defina AZURE_SUBSCRIPTION_ID no ambiente." >&2
  exit 1
fi
if [ ! -f "$SSH_PUBLIC_KEY_PATH" ]; then
  echo "ERRO: chave pública SSH não encontrada: $SSH_PUBLIC_KEY_PATH" >&2
  exit 1
fi

echo "[Azure] Selecionando subscription $SUBSCRIPTION_ID"
az account set --subscription "$SUBSCRIPTION_ID"

echo "[Azure] Criando resource group $RESOURCE_GROUP ($LOCATION)"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" >/dev/null

CLOUD_INIT=$(mktemp)
cat > "$CLOUD_INIT" <<'CLOUD'
#cloud-config
package_upgrade: true
packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - gnupg
  - lsb-release
runcmd:
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmour -o /usr/share/keyrings/docker-archive-keyring.gpg
  - echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  - apt-get update
  - apt-get install -y docker-ce docker-ce-cli containerd.io nvidia-container-toolkit nvidia-utils-470
  - systemctl enable docker
  - systemctl start docker
CLOUD

echo "[Azure] Criando VM $VM_NAME (tamanho $VM_SIZE) — isso pode levar alguns minutos"
az vm create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VM_NAME" \
  --image "$IMAGE" \
  --size "$VM_SIZE" \
  --generate-ssh-keys \
  --custom-data "$CLOUD_INIT" \
  --admin-username "$SSH_USER" \
  --output json >/tmp/az_vm_create.json

VM_PUBLIC_IP=$(jq -r '.publicIpAddress' /tmp/az_vm_create.json)
if [ -z "$VM_PUBLIC_IP" ] || [ "$VM_PUBLIC_IP" = "null" ]; then
  echo "ERRO: nao foi possivel obter IP da VM. Verifique no portal Azure." >&2
  exit 1
fi

echo "[Azure] VM criada: $VM_NAME @ $VM_PUBLIC_IP"

echo "Ações manuais recomendadas no VM (executar via SSH):"
echo "  1) Instalar nvidia drivers oficiais se necessario"
echo "  2) Instalar text-generation-inference ou Ollama via docker-compose"
echo "  3) Ajustar /etc/docker/daemon.json para usar nvidia runtime se precisar"

echo "Exemplo de deploy TGI (após SSH no VM):"
echo "  sudo apt-get update && sudo apt-get install -y docker-compose"
echo "  mkdir -p ~/tgi && cat > ~/tgi/docker-compose.yml <<'YML'"
echo "  version: '3.8'"
echo "  services:" \
     && echo "    tgi:" \
     && echo "      image: ghcr.io/huggingface/text-generation-inference:latest" \
     && echo "      runtime: nvidia" \
     && echo "      environment:" \
     && echo "        - CUDA_VISIBLE_DEVICES=0" \
     && echo "      ports:" \
     && echo "        - '8080:8080'" \
     && echo "      volumes:" \
     && echo "        - ./models:/models" \
     && echo "  YML"

echo "Depois, faça ssh $SSH_USER@$VM_PUBLIC_IP e inicie:"
echo "  cd ~/tgi && docker compose up -d"

echo "Após a VM TGI subir, configure no backend (Hetzner) a variável AZURE_TGI_ENDPOINT=http://$VM_PUBLIC_IP:8080 e DEFAULT_LLM=azure_tgi no .env do servidor Hetzner."

echo "Script concluído."

rm -f "$CLOUD_INIT" /tmp/az_vm_create.json
