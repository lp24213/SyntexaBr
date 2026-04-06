# Syntexa — Motor de IA (Ollama + Mistral 7B)

O stack usa **Ollama** com **Mistral 7B**. Roda em VPS com 8GB+ RAM.

## No servidor (primeira vez)

```bash
cd /opt/syntexa/llm-server
docker compose up -d
docker exec syntexa-ollama ollama pull mistral
```

## Variáveis no .env do backend

- `OLLAMA_ENDPOINT=http://172.17.0.1:11434` (host → container Ollama; ver `.env.example`)
- `OLLAMA_MODEL=mistral`
- `DEFAULT_LLM=ollama`

Depois: `systemctl restart syntexa`.
