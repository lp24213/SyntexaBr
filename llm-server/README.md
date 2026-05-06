# Syntexa — Motor de IA (Ollama / TGI / Azure)

Este diretório contém a configuração Docker para executar um servidor LLM local.

Opções suportadas:
- Ollama (rápido de configurar em CPU/GPU moderada; ideal para protótipos e modelos menores)
- Text Generation Inference (TGI) — recomendado para modelos 13B+ com GPU (melhor throughput e suporte a quantização)
- Azure OpenAI — serviço gerenciado (menor controle sobre custos e privacidade)

## Rápido: Ollama (ex.: Mistral / Llama)

```bash
cd /opt/syntexa/llm-server
docker compose up -d
# Exemplo: puxar modelo via Ollama
docker exec syntexa-ollama ollama pull llama-13b:latest
```

## Opcional: Text Generation Inference (TGI) para modelos 13B+

No host (Hetzner/Azure VM) com GPU NVIDIA, instale `nvidia-container-toolkit` e use a seção comentada em `docker-compose.yml`.
Coloque o modelo em `./models/llama-13b` ou monte um volume persistente. Ajuste `--max-input-length` conforme a memória da GPU.

Recomendações de máquina (Azure): NVidia A10 / A100 / 4090 dependendo do modelo e quantização. Para Llama 13B, 40–80GB VRAM (ou quantização/8-bit + técnica de offload) reduz requisitos.

## Variáveis no .env do backend

- `LOCAL_LLM_ENDPOINT` — endpoint HTTP que o backend usa (ex.: http://127.0.0.1:11434)
- `OLLAMA_ENDPOINT` — se usar Ollama no host
- `OLLAMA_MODEL` — nome exato do modelo usado pela instância Ollama
- `AZURE_TGI_ENDPOINT`, `AZURE_TGI_KEY`, `AZURE_TGI_MODEL` — se usar TGI/endpoint em Azure
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_DEPLOYMENT` — se usar Azure OpenAI
- `DEFAULT_LLM` — escolha entre `ollama|azure_tgi|azure_openai|remote|dummy`

Depois de ajustar o .env, reinicie o serviço: `systemctl restart syntexa`.
