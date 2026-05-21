#!/bin/bash
# Syntexa Native Worker — bootstrap em Ubuntu 22.04
# Instala Python + cloudflared. O código + checkpoint sao enviados via scp depois.
set -e
exec > >(tee /var/log/syntexa-userdata.log) 2>&1
echo "[Syntexa] userdata start $(date -u)"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3-pip build-essential git curl wget unzip jq

# Cria diretorio da app
mkdir -p /opt/syntexa-worker
chown -R ubuntu:ubuntu /opt/syntexa-worker

# Instala cloudflared
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cf.deb
dpkg -i /tmp/cf.deb || apt-get install -f -y

echo "[Syntexa] base ready $(date -u)"
