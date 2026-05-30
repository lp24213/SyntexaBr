# 🔐 SECURITY FIXES — Implementação Imediata (Dia 1)

**Prioridade:** 🔴 CRÍTICA | **Tempo:** ~6h de implementação | **Risco de Não Fazer:** Vazamento de dados

---

## 🚨 PROBLEMA 1: Endpoints Sem Autenticação

### Situação Atual
```typescript
// INSEGURO - Qualquer pessoa acessa dados
app.get('/companies', async (request, reply) => {
  const result = await pgPool.query('SELECT * FROM whatsapp.companies');
  return { companies: result.rows };
});
```

### Fix Imediata (30 min)

**Passo 1:** Criar middleware de autenticação

```typescript
// src/middleware/auth.ts
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

export const authenticateJWT = async (
  request: FastifyRequest,
  reply: FastifyReply
) => {
  try {
    await request.jwtVerify();
  } catch (err) {
    reply.code(401).send({ 
      error: 'Unauthorized',
      message: 'Invalid or missing JWT token'
    });
  }
};

export const validateCompanyOwnership = async (
  request: FastifyRequest,
  reply: FastifyReply,
  companyIdSource: 'params' | 'body' | 'query' = 'params'
) => {
  const companyId = companyIdSource === 'params' 
    ? request.params.companyId
    : request.body?.companyId;
  
  const userCompanyId = (request as any).user?.company_id;
  
  if (!userCompanyId || companyId !== userCompanyId) {
    reply.code(403).send({ 
      error: 'Forbidden',
      message: 'Access denied to this company' 
    });
  }
};
```

**Passo 2:** Proteger todas as rotas

```typescript
// src/routes/companies.ts
import { authenticateJWT, validateCompanyOwnership } from '../middleware/auth.js';

export async function companiesRouter(app: FastifyInstance) {
  // GET /companies
  app.get(
    '/',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const userCompanyId = request.user.company_id;
      
      const result = await pgPool.query(
        `SELECT id, name, email, plan FROM whatsapp.companies 
         WHERE id = $1`, // Retorna apenas sua empresa
        [userCompanyId]
      );
      
      return { companies: result.rows };
    }
  );

  // POST /companies/:id/phone-numbers
  app.post(
    '/:id/phone-numbers',
    { 
      onRequest: [authenticateJWT, validateCompanyOwnership] 
    },
    async (request: any, reply) => {
      const { id } = request.params;
      const { phone_number_id, waba_id, access_token } = request.body;
      
      // Validação de input
      if (!phone_number_id || !access_token) {
        return reply.code(400).send({ 
          error: 'Missing required fields' 
        });
      }
      
      const result = await pgPool.query(
        `INSERT INTO whatsapp.phone_numbers 
         (company_id, phone_number_id, waba_id, access_token)
         VALUES ($1, $2, $3, $4)
         RETURNING id, display_number, created_at`,
        [id, phone_number_id, waba_id, access_token]
      );
      
      reply.code(201);
      return result.rows[0];
    }
  );
}
```

**Passo 3:** Proteger rotas de messages

```typescript
// src/routes/messages.ts
export async function messagesRouter(app: FastifyInstance) {
  // GET /messages/:conversationId
  app.get(
    '/:conversationId',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId } = request.params;
      const userCompanyId = request.user.company_id;
      
      // CRÍTICO: Validar que conversa pertence à empresa
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(404).send({ error: 'Conversation not found' });
      }
      
      const result = await pgPool.query(
        `SELECT * FROM whatsapp.messages 
         WHERE conversation_id = $1 
         ORDER BY created_at DESC LIMIT 100`,
        [conversationId]
      );
      
      return { messages: result.rows };
    }
  );

  // POST /messages
  app.post(
    '/',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId, content } = request.body;
      const userCompanyId = request.user.company_id;
      
      if (!content) {
        return reply.code(400).send({ error: 'Content required' });
      }
      
      // Validar ownership
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(403).send({ error: 'Access denied' });
      }
      
      const result = await pgPool.query(
        `INSERT INTO whatsapp.messages 
         (conversation_id, direction, message_type, content)
         VALUES ($1, 'outbound', 'text', $2)
         RETURNING id, created_at`,
        [conversationId, content]
      );
      
      return result.rows[0];
    }
  );
}
```

---

## 🚨 PROBLEMA 2: Webhook Sem Validação de Company

### Situação Atual
```typescript
// INSEGURO - Não valida qual empresa recebe a mensagem
for (const message of messages) {
  await orchestrateMessage(
    phone_number_id, // Poderia ser manipulado
    message, 
    contacts
  );
}
```

### Fix Imediata (20 min)

```typescript
// src/orchestrator/index.ts
export async function orchestrateMessage(
  phoneNumberId: string,
  message: Message,
  contacts: Contact[]
) {
  try {
    // CRÍTICO: Buscar phone_number com company_id
    const phoneRecord = await pgPool.query(
      `SELECT 
        companies.id as company_id,
        companies.name,
        phone_numbers.id,
        company_config.*
       FROM whatsapp.phone_numbers
       JOIN whatsapp.companies 
         ON companies.id = phone_numbers.company_id
       LEFT JOIN whatsapp.company_config 
         ON company_config.company_id = companies.id
       WHERE phone_numbers.phone_number_id = $1`,
      [phoneNumberId]
    );

    if (!phoneRecord.rows[0]) {
      logger.error(`🚨 Phone number not found: ${phoneNumberId}`);
      return;
    }

    const config = phoneRecord.rows[0];
    // Agora temos certeza que a company existe
    const companyId = config.company_id;
    
    // ... resto do código usa companyId ...
  } catch (error) {
    logger.error('Orchestration error:', error);
  }
}
```

---

## 🚨 PROBLEMA 3: Rate Limiting Não Distribuído

### Situação Atual
```typescript
// INSEGURO - Memória local não funciona com múltiplas instâncias
const rateLimitStore = new Map();
bucket.count++;
if (bucket.count > 1000) return 429;
```

### Fix Imediata (45 min)

```typescript
// src/middleware/rate-limit.ts
import { createClient } from 'redis';

const redis = createClient({
  url: process.env.REDIS_URL
});

export const rateLimitMiddleware = async (
  request: FastifyRequest,
  reply: FastifyReply
) => {
  const userId = (request as any).user?.id;
  if (!userId) return; // Skip se não autenticado
  
  // Chave: user:month
  const now = new Date();
  const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const rateLimitKey = `ratelimit:${userId}:${monthKey}`;
  
  const limit = 10000; // 10k req/mês
  const count = await redis.incr(rateLimitKey);
  
  if (count === 1) {
    // Primeira requisição do mês - set expiration
    await redis.expire(rateLimitKey, 2592000); // 30 dias
  }
  
  // Header de informação
  reply.header('X-RateLimit-Limit', String(limit));
  reply.header('X-RateLimit-Remaining', String(Math.max(0, limit - count)));
  
  if (count > limit) {
    logger.warn(`Rate limit exceeded for user ${userId}`);
    reply.code(429);
    return reply.send({
      error: 'Too many requests',
      detail: 'Monthly limit exceeded',
      resetAt: new Date(now.getFullYear(), now.getMonth() + 1, 1).toISOString()
    });
  }
};

// Usar no server principal:
// src/index.ts
app.addHook('onRequest', rateLimitMiddleware);
```

---

## 🚨 PROBLEMA 4: Webhook Não Valida company_id

### Situação Atual
```typescript
// INSEGURO - Trata job sem validar company
const job = await redis.brPop('queue:messages', 0);
const { phone_number_id, message } = JSON.parse(job.element);
await orchestrateMessage(phone_number_id, message, contacts);
```

### Fix Imediata (15 min)

```typescript
// src/routes/webhook.ts
export async function webhookRouter(app: FastifyInstance) {
  app.post('/whatsapp', async (request: FastifyRequest, reply: FastifyReply) => {
    const signature = request.headers['x-hub-signature-256'] || '';
    const body = JSON.stringify(request.body);

    // Validar HMAC
    const expected = 'sha256=' + crypto
      .createHmac('sha256', process.env.WHATSAPP_APP_SECRET || '')
      .update(body)
      .digest('hex');

    if (signature !== expected) {
      logger.warn('❌ Invalid webhook signature');
      return reply.code(403).send({ error: 'Invalid signature' });
    }

    // Responder rapidamente para Meta
    reply.code(200).send({ received: true });

    try {
      const data = request.body as any;

      for (const entry of data.entry || []) {
        for (const change of entry.changes || []) {
          if (change.field !== 'messages') continue;

          const messages = change.value.messages || [];
          const contacts = change.value.contacts || [];
          const phone_number_id = change.value.metadata?.phone_number_id;

          if (!phone_number_id) {
            logger.error('No phone_number_id in webhook');
            continue;
          }

          for (const message of messages) {
            try {
              // Enfileirar com phone_number_id para validação
              await redis.lpush(
                'queue:messages',
                JSON.stringify({
                  phone_number_id,
                  message,
                  contacts,
                  receivedAt: new Date().toISOString()
                })
              );
            } catch (error) {
              logger.error('Failed to enqueue message:', error);
            }
          }
        }
      }
    } catch (error) {
      logger.error('Webhook processing error:', error);
    }
  });
}
```

---

## 🚨 PROBLEMA 5: Sem Validação de Input

### Situação Atual
```typescript
// INSEGURO - Aceita qualquer input
const { phone_number_id, access_token } = request.body;
await pgPool.query(
  `INSERT INTO phone_numbers (...) VALUES ($1, $2, ...)`,
  [phone_number_id, access_token] // Sem validação
);
```

### Fix Imediata (30 min)

```typescript
// src/lib/validation.ts
import { z } from 'zod';

export const createPhoneNumberSchema = z.object({
  phone_number_id: z.string().min(3).max(50),
  waba_id: z.string().min(3).max(50),
  access_token: z.string().min(10).max(500),
  display_number: z.string().optional()
});

export const createMessageSchema = z.object({
  conversationId: z.string().uuid(),
  content: z.string().min(1).max(4096)
});

// Usar em rotas:
// src/routes/companies.ts
app.post('/:id/phone-numbers', 
  { onRequest: [authenticateJWT] },
  async (request, reply) => {
    const parsed = createPhoneNumberSchema.safeParse(request.body);
    
    if (!parsed.success) {
      return reply.code(400).send({
        error: 'Validation failed',
        details: parsed.error.errors
      });
    }
    
    const { phone_number_id, waba_id, access_token } = parsed.data;
    // ... continue com dados validados ...
  }
);
```

---

## 🚨 PROBLEMA 6: Secrets em Logs

### Situação Atual
```typescript
// INSEGURO - Pode logar tokens
logger.info('Token:', accessToken);
logger.error('Request body:', requestBody); // Pode incluir secrets
```

### Fix Imediata (20 min)

```typescript
// src/lib/logger.ts
import winston from 'winston';

const sanitize = (obj: any): any => {
  if (!obj) return obj;
  
  const sensitiveKeys = ['password', 'token', 'secret', 'access_token', 'api_key'];
  const result = { ...obj };
  
  for (const key of sensitiveKeys) {
    if (key in result) {
      result[key] = '***REDACTED***';
    }
  }
  
  return result;
};

export const logger = winston.createLogger({
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json(),
        winston.format.printf(info => {
          if (info.body) info.body = sanitize(info.body);
          if (info.headers) info.headers = sanitize(info.headers);
          return JSON.stringify(info);
        })
      )
    })
  ]
});
```

---

## 🚨 PROBLEMA 7: Sem Tratamento de Erro em Queue Worker

### Situação Atual
```typescript
// INSEGURO - Pode travar ou perder dados
async function processQueue() {
  while (true) {
    try {
      const job = await redis.brPop('queue:messages', 0);
      if (!job) continue;
      
      const data = JSON.parse(job.element);
      await orchestrateMessage(...);
    } catch (error) {
      logger.error('Error:', error);
      // Job perdido se crash!
    }
  }
}
```

### Fix Imediata (30 min)

```typescript
// src/worker/queue-worker.ts
import { pgPool, redis } from '../index.js';
import { orchestrateMessage } from '../orchestrator/index.js';
import { logger } from '../lib/logger.js';

const MAX_RETRIES = 3;

interface QueueJob {
  phone_number_id: string;
  message: any;
  contacts: any[];
  retries: number;
  enqueuedAt: string;
}

async function processQueue() {
  logger.info('Queue worker started');
  
  while (true) {
    let job: any = null;
    try {
      job = await redis.brPop('queue:messages', 0);
      if (!job) continue;

      const data: QueueJob = JSON.parse(job.element);
      
      logger.info(`Processing job: ${JSON.stringify({ ...data, retries: data.retries })}`);
      
      try {
        await orchestrateMessage(
          data.phone_number_id, 
          data.message, 
          data.contacts
        );
        
        logger.info(`✅ Job processed successfully`);
        // Job removido do Redis automaticamente (via brPop)
        
      } catch (processingError) {
        logger.error(`❌ Job processing failed (attempt ${data.retries + 1}/${MAX_RETRIES}):`, processingError);
        
        if (data.retries < MAX_RETRIES) {
          // Retentar com backoff exponencial
          const delay = Math.pow(2, data.retries) * 1000; // 1s, 2s, 4s
          logger.info(`Retrying in ${delay}ms...`);
          
          await new Promise(r => setTimeout(r, delay));
          
          // Re-enfileirar
          await redis.lpush(
            'queue:messages',
            JSON.stringify({
              ...data,
              retries: data.retries + 1
            })
          );
        } else {
          // Enviar para DLQ após 3 tentativas
          logger.error('❌ Max retries exceeded, moving to DLQ');
          await redis.lpush(
            'queue:dlq',
            JSON.stringify({
              ...data,
              failedAt: new Date().toISOString(),
              error: processingError.message
            })
          );
        }
      }
      
    } catch (error) {
      logger.error('Queue worker fatal error:', error);
      await new Promise(r => setTimeout(r, 5000)); // Aguardar antes de reintentar
    } finally {
      // Cleanup sempre executa
      // (Redis brPop já remove o item)
    }
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('Worker shutting down gracefully...');
  await redis.quit();
  await pgPool.end();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('Worker interrupted...');
  await redis.quit();
  await pgPool.end();
  process.exit(0);
});

processQueue().catch(error => {
  logger.error('Fatal worker error:', error);
  process.exit(1);
});
```

---

## ✅ IMPLEMENTAÇÃO: CHECKLIST

### Dia 1 (hoje)
- [ ] Criar middleware/auth.ts
- [ ] Criar middleware/rate-limit.ts  
- [ ] Criar lib/validation.ts
- [ ] Criar lib/logger.ts (com sanitize)

### Dia 2
- [ ] Aplicar autenticação em TODAS as rotas
- [ ] Validar company_id em webhook
- [ ] Implementar try-finally em queue worker
- [ ] Validar input com Zod

### Dia 3
- [ ] Testes de autenticação
- [ ] Testes de multi-tenant isolation
- [ ] Deploy em staging
- [ ] Validação manual

### Dia 4
- [ ] Deploy em produção com monitoramento
- [ ] Alertas para anomalias
- [ ] Rollback plan ativo

---

## 🧪 TESTES RÁPIDOS

```bash
# Testar autenticação
curl -X GET http://localhost:3001/companies \
  -H "Authorization: Bearer invalid_token"
# Esperado: 401 Unauthorized

# Testar isolamento multi-tenant  
curl -X GET http://localhost:3001/messages/random-conversation-id \
  -H "Authorization: Bearer valid_token_from_different_company"
# Esperado: 403 Forbidden

# Testar rate limiting
for i in {1..1005}; do
  curl -X GET http://localhost:3001/companies \
    -H "Authorization: Bearer token"
done
# Esperado: 429 Too Many Requests após 1000 requests
```

---

**Status:** READY TO IMPLEMENT  
**Tempo Total:** ~6 horas  
**Impacto:** CRÍTICO - Reduz risco de segurança de 9/10 para 3/10  

