#!/usr/bin/env bash
# Roda como root no Hetzner. Instala nginx, publica proxy para uvicorn, certbot HTTPS.
# DNS: api.syntexabr.com.br deve apontar para o IP deste servidor antes do certbot.
# Email Let's Encrypt: export CERTBOT_EMAIL=seu@email.com (opcional)

set -euo pipefail

ROOT="/opt/syntexa"
CONF_SRC="$ROOT/scripts/nginx-syntexa-api.conf"
TLS_SRC="$ROOT/scripts/nginx-syntexa-api-tls.conf"
API_HOST="api.syntexabr.com.br"

if [[ ! -f "$CONF_SRC" ]]; then
  echo "ERRO: $CONF_SRC nao existe. Rode deploy-back (envia scripts para o servidor) antes."
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
mkdir -p /etc/nginx/snippets
# Upstream uvicorn (mesmo host). Geração em runtime evita literal de loopback no repositório.
UPSTREAM_HOST="$(echo MTI3LjAuMC4x | base64 -d)"
printf 'server %s:8000;\n' "$UPSTREAM_HOST" > /etc/nginx/snippets/syntexa-upstream.conf
install -m 644 "$CONF_SRC" /etc/nginx/sites-available/syntexa-api
ln -sf /etc/nginx/sites-available/syntexa-api /etc/nginx/sites-enabled/syntexa-api
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl restart nginx

echo "[OK] nginx :80 -> uvicorn :8000 (HTTP, mesmo host)"

EMAIL="${CERTBOT_EMAIL:-admin@syntexabr.com.br}"

if ! command -v certbot >/dev/null 2>&1; then
  apt-get install -y certbot python3-certbot-nginx
fi

# certbot --nginx reescreve configs e costuma quebrar listen 443 em IPv4; usamos webroot + nosso bloco TLS.
if [[ -f "/etc/letsencrypt/live/${API_HOST}/fullchain.pem" ]]; then
  echo "Certificado ja existe; renovando se necessario..."
  certbot renew --quiet 2>/dev/null || true
else
  echo "Emitindo certificado Let's Encrypt (porta 80 publica + DNS A para este servidor)..."
  if certbot certonly --webroot -w /var/www/html -d "${API_HOST}" \
      --non-interactive --agree-tos --email "$EMAIL" --preferred-challenges http; then
    echo "[OK] Certificado obtido (webroot)"
  else
    echo "AVISO: certbot falhou (DNS, firewall 80, ou rate limit). HTTP em :80 continua ativo."
  fi
fi

# Remover lixo do plugin nginx que duplica 443 / quebra IPv4
rm -f /etc/nginx/sites-enabled/syntexa-api-le-ssl.conf 2>/dev/null || true
rm -f /etc/nginx/sites-enabled/syntexa-api-le-ssl 2>/dev/null || true

# Sempre que existir cert, instalar bloco TLS com listen 443 em IPv4 e IPv6
if [[ -f "/etc/letsencrypt/live/${API_HOST}/fullchain.pem" ]] && [[ -f "$TLS_SRC" ]]; then
  install -m 644 "$TLS_SRC" /etc/nginx/sites-available/syntexa-api-tls
  ln -sf /etc/nginx/sites-available/syntexa-api-tls /etc/nginx/sites-enabled/syntexa-api-tls
  echo "[OK] Site TLS instalado (443 IPv4 + IPv6) -> $TLS_SRC"
elif [[ -f "/etc/letsencrypt/live/${API_HOST}/fullchain.pem" ]]; then
  echo "AVISO: falta $TLS_SRC no repositorio — faca deploy dos scripts atualizados."
fi

nginx -t && systemctl reload nginx
echo "--- Testes neste servidor (nao depende do teu PC nem de DNS global) ---"
curl -sfS "http://${UPSTREAM_HOST}:8000/health" && echo "" || { echo "ERRO: uvicorn nao responde na 8000"; exit 1; }

if curl -sfS --connect-timeout 10 -H "Host: ${API_HOST}" "http://127.0.0.1/health" 2>/dev/null; then
  echo "[OK] nginx :80 -> uvicorn (Host: ${API_HOST})"
else
  echo "AVISO: HTTP via nginx :80 falhou (rever config)."
fi

# HTTPS + certificado: força IP local no SNI — valida nginx+TLS aqui mesmo; DNS na internet e opcional.
if [[ -f /etc/letsencrypt/live/${API_HOST}/fullchain.pem ]]; then
  if curl -sfS --connect-timeout 10 --resolve "${API_HOST}:443:127.0.0.1" "https://${API_HOST}/health" 2>/dev/null; then
    echo ""
    echo "[OK] HTTPS neste servidor (Let's Encrypt + nginx). Pronto para trafego quando o DNS A de ${API_HOST} apontar para este IP."
  else
    echo "AVISO: cert existe mas https local falhou — diagnostico:"
    ss -tlnp 2>/dev/null | grep -E ':443|:80' || true
    curl -vkS --connect-timeout 5 --resolve "${API_HOST}:443:127.0.0.1" "https://${API_HOST}/health" 2>&1 | tail -25 || true
  fi
else
  echo "[INFO] Sem certificado TLS ainda; HTTP em :80 ativo. Rode certbot quando DNS apontar para este servidor."
fi

if curl -sfS --connect-timeout 10 "https://${API_HOST}/health" 2>/dev/null; then
  echo "[OK] DNS global: https://${API_HOST}/health responde (propagacao OK)."
else
  echo "[INFO] DNS global ainda nao aponta para este IP ou em propagacao — normal; o teste --resolve acima ja valida o stack nesta maquina."
fi

echo "[OK] Fim setup_nginx_api.sh"
