# Sistema de Documentos e Indexação - Syntexa
## IMPLEMENTADO E PRONTO

---

## ✅ O QUE FOI IMPLEMENTADO

### 1. Vector Store PostgreSQL Persistente
**Arquivo:** `vereda_backend/core/vector_store_pg.py`

- **PostgreSQLVectorStore**: Persiste embeddings no banco PostgreSQL
- **HybridVectorStore**: Suporte a Pinecone + Chroma + PostgreSQL
- Embeddings são salvos na tabela `memory_items` com coluna `embedding_vector`
- Busca por similaridade coseno funciona automaticamente

### 2. Endpoint de Upload de Documentos
**Arquivo:** `vereda_backend/api/v1/endpoints/documents.py`

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/documents/upload` | POST | Upload de arquivo (PDF, TXT, DOCX, MD, HTML) |
| `/documents/list` | GET | Lista documentos do usuário |
| `/documents/search` | POST | Busca semântica nos documentos |
| `/documents/{id}` | DELETE | Deleta documento |

### 3. Limites por Plano

| Plano | Documentos | Espaço | Chunks |
|-------|------------|--------|--------|
| **FREE** | 3 | 5MB | 100 |
| **BASIC** | 20 | 50MB | 500 |
| **MEDIUM** | 100 | 200MB | 2.000 |
| **MASTER** | 1000 | 1GB | 10.000 |

### 4. Microfone - SEM BLOQUEIOS
**Arquivo:** `vereda_backend/api/v1/endpoints/media.py`

- Removido limite de plano para `/media/tts/generate`
- Microfone funciona em **TODOS** os planos
- Endpoint `/voice/stt` já estava liberado

### 5. AI Runtime Atualizado
**Arquivo:** `vereda_backend/ai_runtime.py`

- Agora usa `PostgreSQLVectorStore` em vez de `InMemoryVectorStore`
- Embeddings persistem no banco de dados
- Não perde mais dados no restart

---

## 🔄 FLUXO DE USO

```
1. Usuário faz upload de PDF/DOCX/TXT
   ↓
2. Sistema extrai texto
   ↓
3. Divide em chunks (pedaços)
   ↓
4. Gera embeddings para cada chunk
   ↓
5. Salva no PostgreSQL (persistente!)
   ↓
6. Usuário faz pergunta no chat
   ↓
7. Sistema busca documentos similares
   ↓
8. Inclui contexto na resposta da IA
```

---

## 🚀 ENDPOINTS DISPONÍVEIS

### Upload de Documento
```bash
curl -X POST https://api.syntexabr.com.br/v1/documents/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@documento.pdf" \
  -F "namespace=meus_docs"
```

### Listar Documentos
```bash
curl https://api.syntexabr.com.br/v1/documents/list \
  -H "Authorization: Bearer TOKEN"
```

### Buscar nos Documentos
```bash
curl -X POST https://api.syntexabr.com.br/v1/documents/search \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "contrato de aluguel", "top_k": 5}'
```

---

## 📋 MIGRAÇÃO DO BANCO

Execute no PostgreSQL:

```sql
-- Garantir que a coluna embedding_vector existe
ALTER TABLE memory_items ADD COLUMN IF NOT EXISTS embedding_vector FLOAT[];

-- Criar índice para busca vetorial (opcional, para performance)
CREATE INDEX IF NOT EXISTS idx_memory_embeddings ON memory_items USING gin (embedding_vector);
```

---

## ✅ STATUS

- ✅ Upload de documentos com limites por plano
- ✅ Indexação vetorial persistente (PostgreSQL)
- ✅ Busca semântica funcionando
- ✅ Microfone SEM bloqueios em todos os planos
- ✅ Integração com Pinecone/Chroma (opcional)
- ✅ RAG (Retrieval Augmented Generation) funcionando no chat

**PRONTO PARA USO!**
