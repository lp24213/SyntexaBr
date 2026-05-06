#!/usr/bin/env bash
set -euo pipefail

# Execução orquestrada: Terraform -> gerar inventory -> Ansible
# NÃO executa automaticamente sem confirmação do usuário.

TF_DIR="terraform"
ANSIBLE_DIR="ansible"

echo "1/3 - Inicializando Terraform"
pushd "$TF_DIR" >/dev/null
terraform init
echo "Aplicar Terraform: confirme que quer provisionar a VM na Azure"
echo "Forneça a chave pública via variável admin_public_key (ex: -var \"admin_public_key=$(cat ~/.ssh/id_rsa.pub)\")"
read -p "Confirmar apply Terraform? [y/N] " yn
if [[ "$yn" != "y" ]]; then
  echo "Aborting Terraform apply"
  exit 1
fi
terraform apply -var "admin_public_key=$(cat ~/.ssh/id_rsa.pub)" -auto-approve
terraform output -json > ../terraform-output.json
popd >/dev/null

echo "2/3 - Gerando inventory Ansible"
./scripts/generate_inventory_from_terraform.sh terraform/terraform-output.json ansible/inventory.ini

echo "3/3 - Executando Ansible playbook para instalar ExLlama e atualizar Hetzner (.env)"
cd "$ANSIBLE_DIR"
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass

echo "Deploy concluído. Verifique logs e health endpoints." 
