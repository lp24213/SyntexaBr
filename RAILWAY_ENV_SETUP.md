# 🔧 RAILWAY BACKEND CONFIGURATION GUIDE

## ✅ CHECKLIST FINAL - CONFIGURAR DO ZERO

### PASSO 1: Acessar Railway Dashboard
- URL: https://railway.app/
- Acesse seu projeto: `syntexa-api` (ou crie um novo)

### PASSO 2: Configurar Redis (Dependency)
1. No dashboard do Railway, clique em **"+ Add"** → **"Redis"**
2. Aguarde o Redis ficar **"UP"** (status verde)
3. Copie a **REDIS_URL** completa:
   - Deve ter este formato: `redis://:PASSWORD@container.railway.app:PORT`
   - Salve em local seguro (você vai precisar!)

### PASSO 3: Configurar PostgreSQL (Optional - se usar DB)
1. No dashboard, clique em **"+ Add"** → **"PostgreSQL"**
2. Aguarde ficar **"UP"**
3. Copie a **DATABASE_URL** completa:
   - Formato: `postgresql://user:password@host:port/database`

### PASSO 4: Configurar Variáveis de Ambiente (.env)
1. No dashboard do seu serviço `syntexa-api`, clique em **"Variables"**
2. Adicione CADA variável abaixo (copie exatamente):

```
PORT=3001
NODE_ENV=production
REDIS_URL=redis://:SEU_PASSWORD@container.railway.app:SEU_PORT
DATABASE_URL=postgresql://user:pass@host:port/database (OPCIONAL)
QUEUE_NAME=stt_jobs
QUEUE_EVENTS_CHANNEL=stt_events
MAX_JOB_ATTEMPTS=3
JOB_BACKOFF_MS=5000
API_RATE_LIMIT_WINDOW_MS=60000
API_RATE_LIMIT_MAX=120
UPLOAD_DIR=/data/uploads
MAX_FILE_SIZE_MB=40
ALLOWED_ORIGINS=https://syntexabr.com.br,https://www.syntexabr.com.br,https://app.syntexabr.com.br
LOG_LEVEL=info
```

### PASSO 5: Configurar Build & Deploy
1. Clique em **"Settings"** no serviço `syntexa-api`
2. **Build Command**: `npm install`
3. **Start Command**: `npm start`
4. **Root Directory**: `production-node/api`

### PASSO 6: Fazer Deploy
```bash
# Do seu computador, na pasta do projeto
cd production-node/api
railway up
```

### ⚠️ PROBLEMAS COMUNS

**Erro: "NOAUTH Authentication required"**
- ❌ REDIS_URL está incorreta ou vazia
- ✅ Verifique a URL no dashboard do Railway Redis
- ✅ Certifique-se de copiar EXATAMENTE o valor completo

**Erro: "Connection refused"**
- ❌ Redis não está "UP" (status vermelho)
- ✅ Aguarde o Redis ficar verde no dashboard

**Container keeps restarting**
- ❌ Falta de variáveis de ambiente críticas
- ✅ Verifique se REDIS_URL está setado
- ✅ Confirme que PORT=3001 está definido

### ✅ VALIDAÇÃO FINAL
Após deploy:
1. Acesse: `https://syntexa-backend-production.up.railway.app/health`
2. Deve retornar: `{"status":"ok"}`
3. Se retornar erro, check dos logs no Railway dashboard

---

## 🚀 PRÓXIMO PASSO
Após tudo funcionando, o gateway será capaz de fazer requests para:
- `GET /health`
- `POST /api/chat`
- `POST /api/stt`
- `POST /api/tts`
- WebSocket connections

Sucesso! 🎉
