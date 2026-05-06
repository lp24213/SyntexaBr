# Syntexa IA Própria - Arquitetura

## Objetivo
- manter `Ollama` como engine temporária
- tornar o backend agnóstico de provedor (substituível via env)
- acumular inteligência proprietária da Syntexa via memória, dados e telemetria

## Estrutura
- `vereda_ai/ai/llm_engine.py`
  - `LLMProvider` (contrato)
  - `OllamaLLMProvider`
  - `OpenAIProvider`
  - `FutureSyntexaProvider`
- `vereda_backend/services/conversation_store.py`
  - persistência estruturada de sessões/conversas/mensagens/model_runs
- `vereda_backend/core/syntexa_intel.py`
  - idioma, assunto, sentimento, embeddings, memória semântica
- `vereda_backend/api/v1/endpoints/intel.py`
  - endpoint de busca semântica de memória
- `vereda_backend/api/v1/endpoints/admin.py`
  - dashboard de métricas e export de dataset
- `migrations/sql/20260420_syntexa_intelligence_core.sql`
  - schema PostgreSQL + pgvector

## Variáveis principais
- `DEFAULT_LLM=ollama|openai|future_syntexa|syntexa_native`
- `OLLAMA_ENDPOINT`, `OLLAMA_MODEL`, `OLLAMA_API_KEY`
- `OPENAI_ENDPOINT`, `OPENAI_API_KEY`, `OPENAI_MODEL`
- `DATABASE_URL=postgresql+psycopg2://...`

## Endpoints novos
- `POST /v1/intel/memory/search`
- `GET /v1/admin/dashboard/metrics`
- `GET /v1/admin/dataset/export`

## Pipeline de dataset
- `python scripts/export_training_dataset.py --output training/datasets/syntexa_dialogs.jsonl`

## Próximos passos
- vetor nativo em coluna `VECTOR` com índice ivfflat
- rank semântico no banco (`ORDER BY embedding <=> query_embedding`)
- avaliação offline + fine-tuning com dataset proprietário
