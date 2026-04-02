#!/usr/bin/env bash
# Roda como root no Hetzner. Instala nginx, publica proxy para uvicorn, certbot HTTPS.
# DNS: api.syntexabr.com.br deve apontar para o IP deste servidor antes do certbot.
# Email Let's Encrypt: export CERTBOT_EMAIL=seu@email.com (opcional)

set -euo pipefail

ROOT="/opt/syntexa"
CONF_SRC="$ROOT/scripts/nginx-syntexa-api.conf"

if [[ ! -f "$CONF_SRC" ]]; then
  echo "ERRO: $CONF_SRC nao existe. Rode deploy-back no PC antes."
  exit 1
fi

# Config antiga (syntexa-backend) costuma quebrar nginx -t — tira do ar e guarda backup
if [[ -e /etc/nginx/sites-enabled/syntexa-backend ]]; then
  echo "Removendo sites-enabled/syntexa-backend (config invalida)"
  rm -f /etc/nginx/sites-enabled/syntexa-backend
fi
if [[ -f /etc/nginx/sites-available/syntexa-backend ]]; then
  mv /etc/nginx/sites-available/syntexa-backend "/etc/nginx/sites-available/syntexa-backend.bak.$(date +%s)"
fi
rm -f /etc/nginx/sites-enabled/default

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y nginx

mkdir -p /var/www/html/.well-known/acme-challenge
install -m 644 "$CONF_SRC" /etc/nginx/sites-available/syntexa-api
ln -sf /etc/nginx/sites-available/syntexa-api /etc/nginx/sites-enabled/syntexa-api
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl restart nginx

echo "[OK] nginx :80 -> 127.0.0.1:8000 (HTTP)"

EMAIL="${CERTBOT_EMAIL:-admin@syntexabr.com.br}"

if ! command -v certbot >/dev/null 2>&1; then
  apt-get install -y certbot python3-certbot-nginx
fi

if [[ -f /etc/letsencrypt/live/api.syntexabr.com.br/fullchain.pem ]]; then
  echo "Certificado ja existe; renovando se necessario..."
  certbot renew --quiet 2>/dev/null || true
else
  echo "Emitindo certificado Let's Encrypt (porta 80 deve estar acessivel publicamente)..."
  if certbot --nginx -d api.syntexabr.com.br --non-interactive --agree-tos --email "$EMAIL" --redirect; then
    echo "[OK] HTTPS configurado pelo certbot"
  else
    echo "AVISO: certbot falhou (DNS, firewall 80, ou rate limit). HTTP em :80 continua ativo."
    echo "  Corrija DNS/firewall e rode de novo: bash $ROOT/scripts/setup_nginx_api.sh"
  fi
fi

nginx -t && systemctl reload nginx

echo "--- Testes locais ---"
curl -sfS "http://127.0.0.1:8000/health" && echo "" || { echo "ERRO: uvicorn nao responde na 8000"; exit 1; }
# Apos certbot, HTTP pode redirecionar (301) para HTTPS — usar -L ou testar HTTPS
if curl -sfS "https://127.0.0.1/health" -H "Host: api.syntexabr.com.br" -k 2>/dev/null; then
  echo ""
  echo "(nginx -> API via HTTPS local OK)"
elif curl -sfSL "http://127.0.0.1/health" -H "Host: api.syntexabr.com.br" 2>/dev/null; then
  echo ""
  echo "(nginx -> API via HTTP com redirect OK)"
else
  echo "AVISO: teste proxy falhou — verifique manualmente: curl -sS https://api.syntexabr.com.br/health"
fi

echo "[OK] Fim setup_nginx_api.sh — teste de fora: curl -sS https://api.syntexabr.com.br/health"
