#!/bin/bash
set -euo pipefail
# Roda na VM Azure: build da imagem API e push para ACR (identidade gerida AcrPush).
cd /opt/syntexa-build/repo
cat > Dockerfile << 'DOCKEREOF'
FROM python:3.12-slim-bookworm
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY vereda_backend ./vereda_backend
COPY vereda_ai ./vereda_ai
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "vereda_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKEREOF

systemctl start docker || service docker start

TOKEN=$(curl -sf "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://containerregistry.azure.com/" -H Metadata:true | jq -r .access_token)
echo "$TOKEN" | docker login syntexabracr891088.azurecr.io -u 00000000-0000-0000-0000-000000000000 --password-stdin

docker build -t syntexabracr891088.azurecr.io/syntexa-api:v2 -f Dockerfile .
docker push syntexabracr891088.azurecr.io/syntexa-api:v2
echo "VM_BUILD_PUSH_OK"
