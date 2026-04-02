# Arquitetura de IA modular — SyntexaBR

Sistema de IA baseado em **agentes**, **ferramentas (tools)**, **memória** e **roteamento**, sem depender de provedor externo de LLM. Otimizado para servidor pequeno (2 CPU, ~4 GB RAM, sem GPU).

## Visão geral do fluxo

```
User Prompt
    ↓
PromptRouter (heurística leve)
    ↓
Agente especializado (math | code | knowledge | vision | crypto | general)
    ↓
Tools (opcional)
    ↓
ModularReasoningEngine
    ↓
Cache (TTL) → Resposta final
```

## Estrutura de diretórios

```
vereda_ai/
    router/           # Roteamento de prompts
        prompt_router.py   # Classificação: math, code, knowledge, vision, web, crypto, general
    agents/           # Agentes especializados
        base_agent.py
        math_agent.py
        code_agent.py
        knowledge_agent.py
        vision_agent.py
        crypto_agent.py
        general_agent.py
    tools/            # Ferramentas reutilizáveis
        base_tool.py
        math_tool.py      # Sympy
        crypto_tool.py    # Preço cripto (API pública, opcional)
        web_tool.py       # HTTP (opcional)
        image_tool.py     # Análise básica (PIL)
        code_tool.py      # Execução segura de Python
    reasoning/        # Engine de raciocínio
        engine.py         # ModularReasoningEngine
    memory/           # Memória
        chat_history_db.py # SQLite: chat_history (user_id, message, role, timestamp)
    cache/            # Cache de respostas
        response_cache.py # TTL em memória (Redis opcional)
    plugins/          # Descoberta de plugins
        loader.py         # discover_agents(), discover_tools()

vereda_backend/
    api/v1/endpoints/
        modular_chat.py   # POST /v1/chat
```

## 1) Router de prompts (PromptRouter)

- **Arquivo:** `vereda_ai/router/prompt_router.py`
- **Função:** Classifica a pergunta do usuário por **palavras-chave** (sem LLM).
- **Categorias:** `math`, `code`, `knowledge`, `vision`, `web`, `crypto`, `general`.
- **Uso:** `router.route(prompt)` → `RouteCategory`.

## 2) Sistema de agentes

Cada agente implementa `handle(prompt: str, context: dict) -> str`.

| Agente        | Arquivo          | Responsabilidade                    |
|---------------|------------------|-------------------------------------|
| MathAgent     | math_agent.py    | Expressões matemáticas (Sympy)      |
| CodeAgent     | code_agent.py    | Código e programação                |
| KnowledgeAgent| knowledge_agent.py | Conhecimento + RAG/contexto      |
| VisionAgent   | vision_agent.py  | Análise de imagem (metadados)       |
| CryptoAgent   | crypto_agent.py  | Preço de criptomoedas               |
| GeneralAgent  | general_agent.py | Resposta geral                      |

## 3) Sistema de tools

Cada tool estende `BaseTool` e implementa `run(**kwargs) -> dict` com `ok`, `result` ou `error`.

- **MathTool:** Sympy (offline).
- **CryptoTool:** API CoinGecko (opcional; offline retorna erro).
- **WebTool:** HTTP GET/POST (opcional).
- **ImageTool:** Dimensões e cor média (PIL, offline).
- **CodeTool:** Execução de snippet Python com timeout (offline).

## 4) Engine de raciocínio (ModularReasoningEngine)

- **Arquivo:** `vereda_ai/reasoning/engine.py`
- **Fluxo:** Obtém categoria do router → escolhe agente → chama `agent.handle(prompt, context)` → opcionalmente usa cache.
- **Contexto:** `history`, `knowledge_snippets`, `memory_snippets`, `image_data`/`image_path`.

## 5) Memória de conversa (SQLite)

- **Tabela:** `chat_history` (id, user_id, message, role, timestamp).
- **Arquivo:** `vereda_ai/memory/chat_history_db.py`
- **Métodos:** `add(user_id, message, role)`, `get_recent(user_id, limit)`.

## 6) Cache inteligente

- **Arquivo:** `vereda_ai/cache/response_cache.py`
- **Comportamento:** TTL em memória (padrão 300 s). Chave: hash(prompt + user_id).
- **Redis:** Opcional via `redis_url` no construtor.

## 7) Sistema de plugins

- **Arquivo:** `vereda_ai/plugins/loader.py`
- **Funções:** `discover_agents(agents_dir)`, `discover_tools(tools_dir)`.
- **Regra:** Novos arquivos em `agents/` ou `tools/` que herdam `BaseAgent`/`BaseTool` são descobertos automaticamente.

## 8) Modo offline

- Tools que dependem de rede (crypto, web) retornam erro amigável quando offline.
- Math, code e image funcionam sem internet.

## 9) Otimização para servidor pequeno

- Router heurístico (sem chamada a LLM para rotear).
- Cache em memória para evitar reprocessamento.
- Sem modelo pesado extra; usa o LLM já configurado (ex.: Ollama 1B).
- Execução síncrona; para alto throughput, usar workers/async na API.

## 10) Rota FastAPI

**POST /v1/chat**

- **Body:** `{ "message": "..." }` ou `{ "messages": [{ "role": "user", "content": "..." }] }`, opcional `user_id`, `use_cache`.
- **Resposta:** `{ "response": "...", "category": "math" }`.
- **Auth:** Opcional (Bearer); se não enviar token, usa `user_id` ou `anon`.

## Uso programático

```python
from vereda_ai.reasoning import ModularReasoningEngine
from vereda_ai.cache import ResponseCache

cache = ResponseCache(ttl_seconds=300)
engine = ModularReasoningEngine(llm=llm_engine, rag=rag_engine, cache=cache)
response = engine.process("Quanto é raiz de 64?", user_id="user1")
```

## Resumo

A SyntexaBR passa a contar com uma IA modular: roteamento por categoria, agentes especializados, tools reutilizáveis, memória em SQLite, cache com TTL e rota `/v1/chat` integrada ao backend existente, pronta para produção em ambiente com poucos recursos.
