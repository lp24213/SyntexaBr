# Syntexa — Capacidades da IA

## Em produção

- **Chat com LLM real** — Ollama (llama3.2:1b ou outro modelo no servidor). Responde perguntas, explicações, fórmulas (ex.: Bhaskara), texto livre.
- **Matemática completa (Sympy)** — Contas básicas a avançadas: expressões numéricas, "quanto é 2+2", "calcule 10*5", "quanto é (1+2)*3", etc. Sempre que a mensagem for ou contiver uma expressão matemática, o resultado é calculado em tempo real.
- **Modos Syntexa** — Copiloto, Lab, Científico, Jurídico, Estratégico (detecção por palavras-chave e encaminhamento ao motor).
- **Base de conhecimento + RAG** — Busca em KnowledgeItem e vetor global para contexto.
- **Memória de conversa** — Turnos armazenados para contexto.
- **Auditoria e eventos** — Log de ações e webhooks.

## Em desenvolvimento / roadmap

- **Visão (reconhecimento de imagem)** — Análise de imagem já existe em `/v1/tools/image/analyze` e `/v1/vision`; integração com modelo de visão (multimodal) no fluxo do chat.
- **Geração de imagem** — Módulo para gerar imagens a partir de prompt (serviço externo ou modelo local).
- **Vídeo** — Análise e/ou geração de vídeo (módulo futuro).
- **Pesquisa e notícias** — Busca na web e agregação de notícias via APIs.
- **Evolução contínua** — Fine-tuning, feedback do usuário, expansão da base de conhecimento e do RAG.

## Configuração do motor no servidor

Para o backend usar o Ollama (e não o dummy), o `.env` em `/opt/syntexa` deve ter:

- `OLLAMA_ENDPOINT=http://127.0.0.1:11434`
- `OLLAMA_MODEL=llama3.2:1b` (ou o modelo que couber na RAM)
- `DEFAULT_LLM=ollama`

E o systemd deve carregar o `.env` (ver `scripts/syntexa.service.example`).
