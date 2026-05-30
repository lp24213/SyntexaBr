# 📋 CHECKLIST IMPLEMENTAÇÃO — WhatsApp SaaS Production-Ready

**Data:** 29 MAI 2026 | **Prioridade:** CRÍTICA | **Prazo:** 6-8 semanas

---

## ⚡ FASE 1: SEGURANÇA CRÍTICA (SEMANA 1)

### [ ] 1.1 Autenticação JWT em Todas as Rotas

#### Código a Implementar:

```typescript
// src/middleware/auth.ts
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

export async function authenticateJWT(
  request: FastifyRequest,
  reply: FastifyReply
) {
  try {
    await request.jwtVerify();
  } catch (err) {
    reply.code(401).send({ error: 'Unauthorized' });
  }
}

// Uso em rotas:
app.get('/messages/:conversationId', 
  { onRequest: [authenticateJWT] }, 
  async (request, reply) => {
    const userId = request.user.sub;
    const companyId = request.user.company_id;
    // ...
  }
);
```

#### Routes a Proteger:
- [ ] GET /companies
- [ ] POST /companies
- [ ] GET /messages/:conversationId
- [ ] POST /messages
- [ ] GET /memory/:conversationId
- [ ] POST /memory/:conversationId
- [ ] GET /config/:companyId
- [ ] PUT /config/:companyId
- [ ] GET /tools/:conversationId
- [ ] POST /tools/pdf
- [ ] POST /tools/xlsx

#### Estimativa: **8h**

---

### [ ] 1.2 Validação de Ownership (Multi-Tenant Isolation)

```typescript
// src/middleware/validate-company.ts
export async function validateCompanyOwnership(
  request: FastifyRequest,
  reply: FastifyReply
) {
  const companyId = request.params.companyId || request.body?.companyId;
  const userCompanyId = request.user.company_id;
  
  if (companyId !== userCompanyId) {
    return reply.code(403).send({ error: 'Forbidden' });
  }
}

// Em TODA query, adicionar:
const result = await pgPool.query(
  `SELECT * FROM whatsapp.conversations 
   WHERE id = $1 AND company_id = $2`, // ← ADD THIS
  [conversationId, companyId]
);
```

#### Queries a Corrigir:
- [ ] /messages/:conversationId
- [ ] /memory/:conversationId
- [ ] /config/:companyId
- [ ] /tools/:conversationId
- [ ] Webhook processing (validar company)

#### Estimativa: **12h**

---

### [ ] 1.3 Rate Limiting Distribuído em Redis

```typescript
// src/middleware/rate-limit.ts
import { createClient } from 'redis';

const redis = createClient();

export async function rateLimitMiddleware(
  request: FastifyRequest,
  reply: FastifyReply
) {
  const key = `ratelimit:${request.user.id}:${new Date().toISOString().slice(0, 7)}`;
  const limit = 10000; // Por mês
  
  const count = await redis.incr(key);
  if (count === 1) {
    await redis.expire(key, 2592000); // 30 dias
  }
  
  if (count > limit) {
    return reply.code(429).send({
      error: 'Rate limit exceeded',
      remaining: Math.max(0, limit - count)
    });
  }
}
```

#### Estimativa: **6h**

---

### [ ] 1.4 Row-Level Security em PostgreSQL

```sql
-- Enable RLS
ALTER TABLE whatsapp.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp.memory_vectors ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can only see their company's data"
  ON whatsapp.conversations
  USING (company_id = current_setting('app.current_company_id')::uuid);

CREATE POLICY "Users can only see their company's messages"
  ON whatsapp.messages
  USING (
    conversation_id IN (
      SELECT id FROM whatsapp.conversations 
      WHERE company_id = current_setting('app.current_company_id')::uuid
    )
  );
```

#### Estimativa: **4h**

---

### [ ] 1.5 Secrets Management

- [ ] Remover secrets de .env.example
- [ ] Usar Railway/Vercel Secrets
- [ ] Implementar secret rotation
- [ ] Adicionar secret versioning

#### Estimativa: **3h**

---

## ⚙️ FASE 2: CONFIABILIDADE (SEMANA 2-3)

### [ ] 2.1 Retry Logic com Exponential Backoff

```typescript
// src/lib/retry.ts
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: any;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      const delay = initialDelay * Math.pow(2, attempt);
      logger.warn(`Attempt ${attempt + 1} failed, retrying in ${delay}ms`, error);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}

// Uso:
const response = await retryWithBackoff(
  () => callSyntexaLLM(messages, options),
  3,
  1000
);
```

#### Onde Aplicar:
- [ ] LLM calls
- [ ] WhatsApp API calls
- [ ] S3 uploads
- [ ] Database operations

#### Estimativa: **10h**

---

### [ ] 2.2 Dead-Letter Queue (DLQ)

```typescript
// src/lib/queue.ts
export async function enqueueMessage(data: any, retries = 0) {
  if (retries > 3) {
    // Enviar para DLQ
    await redis.lpush('queue:dlq', JSON.stringify({
      data,
      failedAt: new Date(),
      reason: 'Max retries exceeded'
    }));
    return;
  }
  
  await redis.lpush('queue:messages', JSON.stringify({
    ...data,
    retries,
    enqueuedAt: new Date()
  }));
}

// Worker processa DLQ
export async function processDLQ() {
  const job = await redis.brPop('queue:dlq', 1);
  if (!job) return;
  
  const data = JSON.parse(job.element);
  logger.error('DLQ Job:', data);
  // Alertar admin, gerar ticket, etc
}
```

#### Estimativa: **8h**

---

### [ ] 2.3 Circuit Breaker

```typescript
// src/lib/circuit-breaker.ts
export class CircuitBreaker {
  private failureCount = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  
  private threshold = 5;
  private timeout = 60000;
  
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }
    
    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private onSuccess() {
    this.failureCount = 0;
    this.state = 'closed';
  }
  
  private onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.failureCount >= this.threshold) {
      this.state = 'open';
    }
  }
}

// Uso:
const llmBreaker = new CircuitBreaker();
const response = await llmBreaker.execute(
  () => callSyntexaLLM(messages, options)
);
```

#### Estimativa: **6h**

---

### [ ] 2.4 Try-Finally para Cleanup

```typescript
// src/worker/queue-worker.ts
async function processQueue() {
  while (true) {
    let job: any = null;
    try {
      job = await redis.brPop('queue:messages', 0);
      if (!job) continue;
      
      const data = JSON.parse(job.element);
      await orchestrateMessage(data.phone_number_id, data.message, data.contacts);
      
    } catch (error) {
      logger.error('Queue processing error:', error);
      if (job) {
        await handleFailedJob(job);
      }
    } finally {
      // Cleanup sempre executa
      // Remove from processing, update metrics, etc
    }
  }
}
```

#### Estimativa: **4h**

---

### [ ] 2.5 Graceful Shutdown

```typescript
// src/index.ts
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  
  // Stop accepting new requests
  app.server.close();
  
  // Wait for in-flight requests (timeout 30s)
  await new Promise(resolve => setTimeout(resolve, 30000));
  
  // Close connections
  await pgPool.end();
  await redis.quit();
  
  logger.info('Shutdown complete');
  process.exit(0);
});
```

#### Estimativa: **3h**

---

## 📈 FASE 3: ESCALABILIDADE (SEMANA 4)

### [ ] 3.1 Vector Search (pgvector/RAG)

```sql
-- Adicionar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Nova tabela
CREATE TABLE whatsapp.embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES whatsapp.conversations(id),
  content TEXT NOT NULL,
  embedding vector(1536), -- OpenAI embedding size
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index para similaridade
CREATE INDEX idx_embeddings_vector 
  ON whatsapp.embeddings 
  USING ivfflat (embedding vector_cosine_ops);
```

```typescript
// src/lib/embeddings.ts
export async function similaritySearch(
  query: string,
  conversationId: string,
  topK: number = 5
) {
  const queryEmbedding = await getEmbedding(query);
  
  const result = await pgPool.query(
    `SELECT content, 1 - (embedding <=> $1) as similarity
     FROM whatsapp.embeddings
     WHERE conversation_id = $2
     ORDER BY similarity DESC
     LIMIT $3`,
    [queryEmbedding, conversationId, topK]
  );
  
  return result.rows;
}
```

#### Estimativa: **15h**

---

### [ ] 3.2 Múltiplos Workers (Kubernetes)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatsapp-worker
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: worker
        image: whatsapp-worker:latest
        env:
        - name: WORKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
```

#### Estimativa: **10h**

---

### [ ] 3.3 PostgreSQL Replication

```sql
-- Primary
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 3;
CREATE USER replicator WITH REPLICATION;

-- Replica
pg_basebackup -h primary -U replicator -v -P -W -D /var/lib/postgresql/data
standby_mode = 'on'
primary_conninfo = 'host=primary port=5432 user=replicator'
```

#### Estimativa: **8h**

---

### [ ] 3.4 Redis Sentinel

```conf
# redis-sentinel.conf
port 26379
sentinel monitor whatsapp-redis 127.0.0.1 6379 1
sentinel down-after-milliseconds whatsapp-redis 5000
sentinel failover-timeout whatsapp-redis 10000
```

#### Estimativa: **6h**

---

## 🎯 FASE 4: QUALIDADE (SEMANA 5+)

### [ ] 4.1 Engine de Documentos Profissional

- [ ] PDF com pdfkit (templates, styling)
- [ ] Excel com openpyxl (formulas, charts)
- [ ] DOCX com python-docx
- [ ] CSV com proper encoding

#### Estimativa: **40h**

---

### [ ] 4.2 Dashboard Avançado

- [ ] Analytics de conversas
- [ ] Relatórios de atendimento
- [ ] Métricas de resposta
- [ ] Gráficos em tempo real

#### Estimativa: **30h**

---

### [ ] 4.3 WebSocket Real-Time

```typescript
// src/websocket/handler.ts
import { Server } from 'socket.io';

const io = new Server(app.server, {
  cors: { origin: process.env.ALLOWED_ORIGINS.split(',') }
});

io.on('connection', (socket) => {
  socket.on('join-conversation', (conversationId, companyId) => {
    // Validate ownership
    socket.join(`conversation:${conversationId}`);
  });
  
  socket.on('disconnect', () => {
    // Cleanup
  });
});

// Emitir quando mensagem chega:
io.to(`conversation:${conversationId}`).emit('new-message', message);
```

#### Estimativa: **20h**

---

### [ ] 4.4 Marketing Pages

- [ ] Home page
- [ ] Pricing page
- [ ] Feature showcase
- [ ] Documentation
- [ ] Blog

#### Estimativa: **30h**

---

## 🧪 TESTES

### [ ] Unit Tests
- [ ] Middleware de autenticação
- [ ] Rate limiting
- [ ] Retry logic
- [ ] Circuit breaker

### [ ] Integration Tests
- [ ] Webhook processing
- [ ] Multi-tenant isolation
- [ ] Queue processing
- [ ] LLM integration

### [ ] E2E Tests
- [ ] Complete message flow
- [ ] Error scenarios
- [ ] Failover scenarios

#### Estimativa: **40h**

---

## 📊 RESUMO

| Fase | Horas | Prazo |
|------|-------|-------|
| **1. Segurança** | 33h | 1 semana |
| **2. Confiabilidade** | 31h | 1-2 semanas |
| **3. Escalabilidade** | 39h | 1 semana |
| **4. Qualidade** | 120h | 2-3 semanas |
| **Testes** | 40h | Paralelo |
| **TOTAL** | **263h** | **6-8 semanas** |

---

## 🚀 PARALLELIZAÇÃO

Tarefas que podem ser feitas em paralelo:

**Semana 1:**
- 2 devs: Segurança
- 1 dev: Testes unitários

**Semana 2:**
- 2 devs: Confiabilidade
- 1 dev: Testes de integração

**Semana 3:**
- 2 devs: Escalabilidade
- 1 dev: Infraestrutura K8s

**Semana 4-5:**
- 3 devs: Dashboard + Docs + Marketing
- 1 dev: E2E tests

**Equipe:** 2-3 desenvolvedores full-time

---

## ✅ DEFINIÇÃO DE "PRONTO"

Sistema está pronto para produção quando:

- [ ] Todos os endpoints têm autenticação JWT
- [ ] Isolamento multi-tenant testado e validado
- [ ] Rate limiting funciona com múltiplas instâncias
- [ ] Retry logic implementada e testada
- [ ] DLQ funcional para jobs falhados
- [ ] Circuit breaker está em produção
- [ ] Health checks passando
- [ ] Logs estruturados em JSON
- [ ] Métricas sendo coletadas
- [ ] Alertas configurados
- [ ] Backup automático ativo
- [ ] Disaster recovery testado
- [ ] SLA de 99.5% uptime
- [ ] <100ms latência P95
- [ ] Suporta 10k msg/hora

---

**Status:** READY FOR IMPLEMENTATION  
**Próximo Passo:** Iniciar Fase 1

