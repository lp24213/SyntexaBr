#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Script de instalação e deploy orquestrado (Terraform + Ansible + Azure CLI)"

read -p "Este script instalará ferramentas no host e executará o deploy. Continuar? [y/N] " CONF
if [[ "$CONF" != "y" ]]; then
  echo "Abortando."
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  SUDO=sudo
else
  SUDO=
fi

echo "Atualizando apt e instalando dependências básicas..."
$SUDO apt-get update
$SUDO apt-get install -y curl unzip gnupg software-properties-common ca-certificates apt-transport-https lsb-release

echo "Instalando Azure CLI..."
if ! command -v az >/dev/null 2>&1; then
  curl -sL https://aka.ms/InstallAzureCLIDeb | $SUDO bash
else
  echo "az já instalado"
fi

echo "Instalando Terraform..."
if ! command -v terraform >/dev/null 2>&1; then
  TF_VER="1.6.8"
  ARCH=$(uname -m)
  if [ "$ARCH" = "x86_64" ]; then TF_ARCH=amd64; else TF_ARCH=$ARCH; fi
  TMPDIR=$(mktemp -d)
  curl -sSL "https://releases.hashicorp.com/terraform/${TF_VER}/terraform_${TF_VER}_linux_${TF_ARCH}.zip" -o "$TMPDIR/terraform.zip"
  $SUDO unzip -o "$TMPDIR/terraform.zip" -d /usr/local/bin
  rm -rf "$TMPDIR"
else
  echo "terraform já instalado"
fi

echo "Instalando Ansible..."
if ! command -v ansible >/dev/null 2>&1; then
  $SUDO apt-get install -y ansible
else
  echo "ansible já instalado"
fi

echo "Pronto. Agora vou executar o orquestrador: terraform -> gerar inventory -> ansible"
read -p "Confirmar execução do orquestrador agora? [y/N] " CONF2
if [[ "$CONF2" != "y" ]]; then
  echo "Abortando antes do deploy.";
  exit 0
fi

pushd "$SCRIPT_DIR/.." >/dev/null
bash scripts/run_full_deploy.sh
popd >/dev/null

echo "Script concluído." 
