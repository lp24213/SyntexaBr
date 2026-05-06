#!/usr/bin/env bash
set -euo pipefail

# Provisiona uma VM Azure com GPU (requere 'az' autenticado) e deploy do docker-compose ExLlama/TGI.
# Uso: export AZ_RG=myrg AZ_LOCATION=eastus AZ_VM_NAME=exllama-vm AZ_VM_SIZE=Standard_NC6s_v3
# ./scripts/provision_and_deploy_azure_cli.sh --ssh-pub ~/.ssh/id_rsa.pub --ssh-key ~/.ssh/id_rsa

print_usage(){
  cat <<EOF
Usage: $0 --ssh-pub <pubkey> --ssh-key <private-key> [--rg RG] [--location LOC] [--vmname NAME] [--vmsize SIZE]

This script requires you to be logged in with 'az login'. It will create resources and may incur costs.
EOF
}

SSH_PUB=""
SSH_KEY=""
RG=${AZ_RG:-syntexa-rg}
LOCATION=${AZ_LOCATION:-eastus}
VM_NAME=${AZ_VM_NAME:-exllama-vm}
VM_SIZE=${AZ_VM_SIZE:-Standard_NC6s_v3}
ADMIN_USER=${AZ_ADMIN_USER:-azureuser}

while [[ $# -gt 0 ]]; do
  case $1 in
    --ssh-pub) SSH_PUB=$2; shift 2;;
    --ssh-key) SSH_KEY=$2; shift 2;;
    --rg) RG=$2; shift 2;;
    --location) LOCATION=$2; shift 2;;
    --vmname) VM_NAME=$2; shift 2;;
    --vmsize) VM_SIZE=$2; shift 2;;
    -h|--help) print_usage; exit 0;;
    *) echo "Unknown arg $1"; print_usage; exit 1;;
  esac
done

if [ -z "$SSH_PUB" ] || [ -z "$SSH_KEY" ]; then
  echo "Error: --ssh-pub and --ssh-key are required"
  print_usage
  exit 1
fi

if ! command -v az >/dev/null 2>&1; then
  echo "az CLI not found. Install az and run 'az login' before executing." >&2
  exit 1
fi

echo "Creating resource group $RG in $LOCATION..."
az group create -n "$RG" -l "$LOCATION"

echo "Creating VM $VM_NAME (size $VM_SIZE). This can take several minutes..."
az vm create \
  -g "$RG" -n "$VM_NAME" \
  --image Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest \
  --size "$VM_SIZE" \
  --admin-username "$ADMIN_USER" \
  --ssh-key-values "$SSH_PUB" \
  --public-ip-sku Standard \
  --output json

echo "Retrieving public IP..."
IP=$(az vm list-ip-addresses -g "$RG" -n "$VM_NAME" --query "[0].virtualMachine.network.publicIpAddresses[0].ipAddress" -o tsv)
if [ -z "$IP" ]; then
  echo "Failed to get public IP" >&2
  exit 1
fi
echo "VM public IP: $IP"

echo "Waiting for SSH availability..."
for i in {1..30}; do
  if ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$ADMIN_USER@$IP" 'echo ok' 2>/dev/null | grep -q ok; then
    echo "SSH reachable"
    break
  fi
  echo -n "."
  sleep 5
done

echo "Installing Docker + NVIDIA toolkit on remote VM..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$ADMIN_USER@$IP" bash -s <<'SSH'
set -e
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Try installing NVIDIA driver and toolkit (may vary by region/VM SKU)
sudo apt-get install -y --no-install-recommends nvidia-driver-535 || true
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - || true
curl -s -L https://nvidia.github.io/nvidia-docker/ubuntu$(lsb_release -rs)/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list || true
sudo apt-get update || true
sudo apt-get install -y nvidia-container-toolkit || true
sudo systemctl restart docker || true
SSH

echo "Creating remote directory /opt/exllama and copying docker-compose..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$ADMIN_USER@$IP" "sudo mkdir -p /opt/exllama && sudo chown $ADMIN_USER /opt/exllama"
scp -o StrictHostKeyChecking=no -i "$SSH_KEY" llm-server/docker-compose.exllama.yml "$ADMIN_USER@$IP":/tmp/docker-compose.exllama.yml
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$ADMIN_USER@$IP" "mv /tmp/docker-compose.exllama.yml /opt/exllama/docker-compose.exllama.yml && cd /opt/exllama && docker compose -f docker-compose.exllama.yml up -d --build"

echo "ExLlama/TGI services should be starting on $IP (ports 8080/8081)."

echo "Updating Ansible inventory and running playbook to update Hetzner backend (.env)"
# Update inventory exllama entry
sed -i "/^\[exllama\]/,/^\[/ s/^.*$/${IP} ansible_user=${ADMIN_USER} ansible_ssh_private_key_file=${SSH_KEY}/" ansible/inventory.ini || true

echo "Running Ansible playbook to update Hetzner (requires ssh key access to Hetzner configured in ansible/inventory.ini)"
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --ask-become-pass || true

echo "Provision and deploy finished. Public IP: $IP"
