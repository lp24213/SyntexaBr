# 📱 Como Usar WhatsApp SaaS - Guia Prático

## 🚀 Início Rápido

### 1. Configurar Credenciais Meta

Obter em: https://developers.facebook.com/apps

```bash
# .env (whatsapp-saas)
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_ACCESS_TOKEN=EAAB...
WHATSAPP_APP_SECRET=app-secret-xxx
WHATSAPP_VERIFY_TOKEN=verify-token-xxx
```

### 2. Configurar Webhook em Meta

1. Ir para app settings
2. Webhook URL: `https://whatsapp.syntexabr.com.br/webhook/whatsapp`
3. Verify Token: (mesmo do .env)
4. Webhook Fields: `messages`, `message_template_status_update`

### 3. Iniciar Backend

```bash
cd whatsapp-saas
npm install
npm run build
npm start
```

Ou com worker:
```bash
npm run worker
```

---

## 💬 Exemplo Real: Cliente Pede Planilha

### Cliente envia no WhatsApp:
```
"Monta uma planilha de fluxo de caixa para meu negócio 
com receita, custo e lucro dos últimos 3 meses. 
Quero exportar pro Excel."
```

### O que acontece nos bastidores:

#### 1️⃣ Webhook recebe (< 100ms)
```
POST /webhook/whatsapp
Headers: X-Hub-Signature-256: sha256=HMAC_SHA256(body, APP_SECRET)
Body: { entry: [{ changes: [{ field: "messages", value: {...} }] }] }
Response: 200 OK
```

#### 2️⃣ Redis enfileira (< 50ms)
```
redis.lPush('queue:messages', JSON.stringify({
  phone_number_id: "1234567890",
  message: { from: "5511999999999", text: "Monta uma planilha..." },
  contacts: [{ profile: { name: "Cliente" }, wa_id: "5511999999999" }],
  receivedAt: "2026-05-31T12:32:00Z"
}))
```

#### 3️⃣ Worker processa (< 500ms)
```
- Desserializa JSON
- Busca histórico da conversa
- Busca memória vetorizada (pgvector)
- Monta prompt com contexto
```

#### 4️⃣ LLM Syntexa responde (2-5s)
```
POST https://api.syntexabr.com.br/v1/chat/completions
{
  "model": "syntexa-llm",
  "messages": [
    { "role": "system", "content": "Você é um assistente de negócios..." },
    { "role": "user", "content": "Monta uma planilha..." }
  ]
}

Response:
{
  "choices": [{
    "message": {
      "content": "Aqui está sua planilha...",
      "tool_call": {
        "type": "xlsx",
        "data": {
          "sheet_title": "Fluxo de Caixa",
          "rows": [
            ["Mês", "Receita", "Custo", "Lucro"],
            ["Janeiro", "R$ 15.000", "R$ 8.000", "R$ 7.000"],
            ["Fevereiro", "R$ 18.500", "R$ 10.200", "R$ 8.300"],
            ["Março", "R$ 22.000", "R$ 11.800", "R$ 10.200"]
          ]
        }
      }
    }
  }]
}
```

#### 5️⃣ Gera Excel (< 1s)
```
POST https://api.syntexabr.com.br/v1/multimodal/export/xlsx
Body: { sheet_title: "Fluxo de Caixa", rows: [...] }
Response: <binary data> (4.96 KB)
```

#### 6️⃣ Upload para Meta (< 2s)
```
POST https://graph.instagram.com/v18.0/{phoneNumberId}/media
Headers: Authorization: Bearer {accessToken}
Body: multipart/form-data (arquivo Excel)
Response: { "id": "123456789" }
```

#### 7️⃣ Envia resposta (< 500ms)
```
POST https://graph.instagram.com/v18.0/{phoneNumberId}/messages
{
  "messaging_product": "whatsapp",
  "to": "5511999999999",
  "type": "document",
  "document": {
    "id": "123456789",
    "caption": "Aqui está sua planilha de fluxo de caixa. 
                Receita total: R$ 55.500 | 
                Custo total: R$ 30.000 | 
                Lucro total: R$ 25.500"
  }
}
Response: { "messages": [{ "id": "wamid.xxx.yyy" }] }
```

### Cliente recebe:
```
Assistente: "Aqui está sua planilha de fluxo de caixa. 
             Receita total: R$ 55.500 | 
             Custo total: R$ 30.000 | 
             Lucro total: R$ 25.500"

[Arquivo anexado: fluxo_caixa.xlsx]
```

**Tempo total**: 4-10 segundos ✅

---

## 🔧 Configurações Avançadas

### Aumentar Timeout do LLM
```typescript
// src/worker/queue-worker-new.ts
const llmResponse = await axios.post(
  'https://api.syntexabr.com.br/v1/chat/completions',
  payload,
  { timeout: 60000 }  // 60 segundos
);
```

### Aumentar Retry
```typescript
// src/worker/queue-worker-new.ts
const maxRetries = 5;  // até 5 tentativas
```

### Aumentar Pool PostgreSQL
```typescript
// src/index.ts
const pgPool = new Pool({
  max: 50  // aumentado de 20
});
```

### Aumentar Redis Queue
```bash
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## 📊 Monitoramento

### Ver Fila Redis
```bash
redis-cli LLEN queue:messages      # Mensagens pendentes
redis-cli LLEN queue:dlq           # Mensagens com erro
redis-cli LRANGE queue:messages 0 -1  # Ver conteúdo
```

### Ver Logs
```bash
tail -f logs/combined.log | grep -E "Message|LLM|Excel|PDF"
```

### Health Check
```bash
curl https://api.syntexabr.com.br/health
# Response: {"status":"ok"}
```

---

## 🐛 Troubleshooting

### Problema: Webhook não recebe eventos

**Solução**:
1. Verificar VERIFY_TOKEN em Meta app settings
2. Verificar URL do webhook (deve ser HTTPS)
3. Validar HMAC SHA256:
```bash
echo -n "body" | openssl dgst -sha256 -hmac "APP_SECRET"
```

### Problema: LLM não responde

**Solução**:
1. Verificar SYNTEXA_API_TOKEN
2. Verificar conectividade:
```bash
curl https://api.syntexabr.com.br/health
```
3. Aumentar timeout para 60s

### Problema: Arquivo não é enviado

**Solução**:
1. Verificar WHATSAPP_ACCESS_TOKEN
2. Verificar WHATSAPP_PHONE_NUMBER_ID
3. Verificar se número está verificado em Meta
4. Verificar logs:
```bash
tail -f logs/combined.log | grep "Media upload"
```

### Problema: Fila Redis crescendo

**Solução**:
1. Verificar se worker está rodando:
```bash
ps aux | grep queue-worker
```
2. Verificar tamanho da fila:
```bash
redis-cli LLEN queue:messages
```
3. Reiniciar worker:
```bash
npm run worker
```

---

## 📈 Escalabilidade

### Para 1000 mensagens/dia
- ✅ Configuração atual é suficiente
- Pool PostgreSQL: 20 conexões
- Redis: 1GB RAM

### Para 10.000 mensagens/dia
- Aumentar pool PostgreSQL: 50 conexões
- Aumentar Redis: 2GB RAM
- Adicionar cache de respostas

### Para 100.000 mensagens/dia
- Usar Kubernetes
- Múltiplas replicas do worker
- Redis Cluster
- PostgreSQL com read replicas

---

## 🔒 Segurança

### Validação HMAC
```typescript
const signature = crypto
  .createHmac('sha256', APP_SECRET)
  .update(body)
  .digest('hex');

if (signature !== headerSignature) {
  return 401; // Unauthorized
}
```

### Rate Limiting
```
1000 requisições/minuto/IP
```

### JWT Authentication
```bash
Authorization: Bearer <JWT_TOKEN>
```

### Secrets
```bash
# Nunca comitar .env
# Usar variáveis de ambiente
export WHATSAPP_ACCESS_TOKEN=...
```

---

## 📚 Recursos Úteis

- [Meta WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)
- [Fastify Docs](https://www.fastify.io/)
- [pgvector Docs](https://github.com/pgvector/pgvector)
- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)

---

## ✅ Checklist de Deploy

- [ ] Credenciais Meta configuradas
- [ ] Webhook URL configurada em Meta
- [ ] Verify Token configurado
- [ ] .env com todas as variáveis
- [ ] PostgreSQL rodando
- [ ] Redis rodando
- [ ] Backend compilado
- [ ] Worker iniciado
- [ ] Health check retorna OK
- [ ] Teste com mensagem real

---

## 🎯 Próximos Passos

1. **Configurar**: Adicionar credenciais Meta
2. **Testar**: Enviar mensagem de teste
3. **Monitorar**: Acompanhar logs
4. **Escalar**: Aumentar recursos conforme necessário

---

**Status**: 🟢 Pronto para usar
**Última atualização**: 31/05/2026
