# Syntexa AI - Oracle Cloud Deploy

## O que e
Backend + IA em uma unica instancia Oracle Cloud.

- **Always Free**: CPU ARM + 24GB RAM (roda LLM ate 7B em CPU)
- **Trial GPU**: A10/V100 com $300-400 creditos (30 dias, depois paga)

## Passo 1: Criar Instancia Oracle Cloud

1. Va em https://cloud.oracle.com e crie conta
2. Va em **Compute** → **Instances** → **Create Instance**
3. Configuracao:
   - **Name**: syntexa-ai
   - **Image**: Ubuntu 22.04 (ou Oracle Linux 8)
   - **Shape**: VM.Standard.A1.Flex (ARM, Always Free)
   - **OCPUs**: 4
   - **Memory**: 24 GB
   - **Boot Volume**: 200 GB
   - **Add SSH Keys**: Gere ou cole sua chave publica
   - **Public Subnet**: Marque "Assign a public IPv4 address"
4. Clique **Create**

## Passo 2: Abrir Porta 8000

1. Na pagina da instancia, clique na **Subnet**
2. Va em **Security Lists** → **Default Security List**
3. **Add Ingress Rules**:
   - **Source Type**: CIDR
   - **Source CIDR**: 0.0.0.0/0
   - **IP Protocol**: TCP
   - **Destination Port Range**: 8000
   - **Description**: Syntexa AI API
4. Salve

## Passo 3: Conectar e Deploy

```bash
# Conectar via SSH (substitua IP)
ssh -i sua-chave.pem ubuntu@IP_DA_INSTANCIA

# No servidor, clone o repo ou copie os arquivos
git clone SEU_REPO.git syntexa-oracle
cd syntexa-oracle/oracle-cloud

# Ou copie manualmente os arquivos: Dockerfile, app.py, requirements.txt, docker-compose.yml

# Rodar deploy
chmod +x deploy.sh
./deploy.sh
```

## Passo 4: Verificar

```bash
# Healthcheck
curl http://IP_DA_INSTANCIA:8000/health

# Chat teste
curl -X POST http://IP_DA_INSTANCIA:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Ola"}]}'
```

## Para GPU (com creditos trial)

Se voce tem creditos GPU:

1. Crie instancia com shape **VM.GPU.A10.1**
2. No `docker-compose.yml`, descomente a secao `deploy.resources`
3. Rode `docker compose up -d --build`

## Variaveis de Ambiente

| Variavel | Padrao | Descricao |
|----------|--------|-----------|
| `PORT` | 8000 | Porta do servidor |
| `LOCAL_LLM_MODEL` | microsoft/DialoGPT-medium | Modelo HuggingFace |
| `AI_DEVICE` | auto | cpu, cuda, ou auto |

## Para usar sua LLM propria

1. Suba o modelo para a instancia (SCP ou download)
2. Defina `LOCAL_LLM_MODEL` como o path local ou repo HuggingFace

## URLs

- Health: `http://IP:8000/health`
- Chat: `http://IP:8000/v1/chat/completions`
- Embeddings: `http://IP:8000/v1/embeddings`
