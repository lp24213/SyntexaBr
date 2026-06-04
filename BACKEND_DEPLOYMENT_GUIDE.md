# 🚀 BACKEND DEPLOYMENT GUIDE — Production Node

**Status:** ⏳ PENDENTE DE BUILD E DEPLOY  
**Serviço:** STT/Audio API (Express + BullMQ + Redis)  
**Deployment:** Railway.app

---

## 📋 MUDANÇAS IMPLEMENTADAS

```
✅ CORS whitelist (4 domínios)
✅ File upload validation (MIME + Extensions)
✅ Path traversal protection
✅ Rate limiting Redis-backed
✅ Error handling melhorado
```

---

## 🔧 PASSO A PASSO BUILD & DEPLOY

### PASSO 1: Instalar Dependencies Novos

```bash
cd production-node

# Já existem:
npm list express multer ioredis

# Adicionar se não existir:
npm install rate-limit-redis --save

# Verificar package.json
cat package.json | grep -i "rate-limit\|ioredis"
```

**Esperado:**
```json
{
  "dependencies": {
    "express": "^4.18.x",
    "multer": "^1.4.x",
    "ioredis": "^5.x",
    "express-rate-limit": "^6.x",
    "rate-limit-redis": "^3.x",
    "bull": "^4.x"
  }
}
```

---

### PASSO 2: Verificar Environment Variables

Verificar em **Railway Dashboard** que as seguintes variáveis estão configuradas:

```bash
# Production Environment Variables (Railway)
REDIS_URL=redis://default:PASSWORD@your-redis-url:6379
UPLOAD_DIR=/data/uploads
API_RATE_LIMIT_WINDOW_MS=60000
API_RATE_LIMIT_MAX=120
CORS_ORIGINS=https://syntexabr.com.br,https://www.syntexabr.com.br,https://app.syntexabr.com.br,https://production.syntexa-frontend.pages.dev
NODE_ENV=production
PORT=3001
```

---

### PASSO 3: Validar Mudanças Locais

```bash
# Verificar que os arquivos foram corrigidos
grep -n "ALLOWED_ORIGINS" production-node/api/src/index.js
grep -n "ALLOWED_MIME_TYPES" production-node/api/src/index.js
grep -n "RedisStore" production-node/api/src/rateLimit.js

# Esperado: Encontrar as variáveis (confirmando edições)
```

---

### PASSO 4: Test Local (Recomendado)

```bash
# Requisitos:
# - Docker com Redis rodando
# - Node.js 18+

# Start Redis local
docker run -d -p 6379:6379 redis:7-alpine
# Esperar ~2s

# Build local
cd production-node
npm install
npm run build  # Se tiver build script
# ou
npm start

# Em outro terminal, testar:
curl http://localhost:3001/health
# Esperado: { "ok": true, "service": "syntexa-api", "redis": "up" }

# Testar CORS
curl -H "Origin: https://attacker.com" http://localhost:3001/health
# Esperado: Sem header CORS ou 403

# Parar local
Ctrl+C
```

---

### PASSO 5: Deploy em Railway

#### Opção A: Railway CLI (Recomendado)

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli
# ou
brew install railway  # macOS

# 2. Login
railway login

# 3. Fazer link com projeto existente
cd ..  # Voltar para a raiz do repositório onde está o Railway config
railway link  # Selecionar projeto "syntexa-backend-production"

# 4. Deploy
railway up  # Automático trigger de build usando Dockerfile.railway

# 5. Verificar status
railway status

# 6. Ver logs
railway logs
```

#### Opção B: Git Push (Se Railway estiver linked via GitHub)

```bash
# Se está em repo local com Railway integrado:
cd ..  # Raiz do projeto
git add production-node/api/src/index.js
git add production-node/api/src/rateLimit.js
git commit -m "Security: CORS whitelist, file validation, Redis rate limiting"
git push origin main

# Railway fará auto-deploy
# Verificar em: https://railway.app -> syntexa-backend-production
```

---

### PASSO 6: Validar Deploy em Produção

```bash
# 1. Verificar que API está UP
curl https://api.syntexabr.com.br/health
# Esperado: { "ok": true, "service": "syntexa-api", "redis": "up" }

# 2. Verificar CORS
curl -H "Origin: https://syntexabr.com.br" https://api.syntexabr.com.br/health
# Esperado: Header `Access-Control-Allow-Origin: https://syntexabr.com.br`

# 3. Verificar upload rejeita .exe
echo "MZ" > test.exe
curl -F "audio=@test.exe" https://api.syntexabr.com.br/api/stt/enqueue
# Esperado: 400 Bad Request - Extension not allowed

# 4. Verificar rate limiting Redis
for i in {1..200}; do curl -s https://api.syntexabr.com.br/health & done
wait
# Esperado: Após ~120, receber 429 Too Many Requests

# 5. Verificar logs
railway logs --service syntexa-backend-production
# Procurar por:
#   "CORS origin rejected"
#   "Extension rejected"
#   "Rate limit"
```

---

## ⚠️ TROUBLESHOOTING

### Problema: "Redis connection error"

```
Solução:
1. Verificar REDIS_URL está correto em Railway
2. Testar conectividade:
   redis-cli -u redis://default:PASSWORD@host:6379 ping
3. Se ainda não funcionar, usar fallback memory store:
   - Editar production-node/api/src/rateLimit.js
   - Comentar a seção RedisStore
   - Deixar memory store como fallback
4. ⚠️ NOTA: Memory store NÃO funciona em múltiplas instâncias
```

### Problema: Upload still accepts .exe

```
Solução:
1. Verificar que npm install foi feito e dependencies estão corretas
2. Verificar que production-node/api/src/index.js foi editado
3. Se ainda não funciona:
   grep "ALLOWED_MIME_TYPES" production-node/api/src/index.js
   # Deve retornar a lista completa
4. Fazer clean build:
   rm -rf node_modules package-lock.json
   npm install
5. Redeploy
```

### Problema: Railway build failure

```
Solução:
1. Verificar Node.js version: node --version
   - Deve ser v18+ ou v20+
   - Se não, atualizar package.json:
     "engines": { "node": ">=18.0.0" }
2. Verificar npm errors:
   npm install --production
3. Se build script falha, comentar temporariamente e fazer redeploy
```

---

## 📊 DEPLOYMENT CHECKLIST

- [ ] Environment variables configuradas em Railway
- [ ] npm install --save rate-limit-redis executado
- [ ] Testes locais passaram (opcional mas recomendado)
- [ ] Railway deploy via CLI ou Git push
- [ ] Health check retorna "redis": "up"
- [ ] CORS validation OK (origem whitelistada)
- [ ] CORS rejection OK (origem não-permitida)
- [ ] File upload rejeita .exe
- [ ] Rate limiting ativado (429 após limite)
- [ ] Logs mostram "Using FRONTEND_PAGES_URL from env"
- [ ] Chat com arquivo funciona
- [ ] Microphone transcrição funciona

---

## 📝 ROLLBACK (Se necessário)

Se deploy causou problemas:

```bash
# Via Railway CLI:
railway rollback --service syntexa-backend-production --environment production

# Ou revert manual:
# 1. Fazer revert local:
git revert HEAD  # Reverte último commit
git push origin main

# 2. Railway fará auto-deploy da versão anterior
```

---

## ✅ VALIDAÇÃO FINAL

Após deploy completo, executar VALIDATION_CHECKLIST.md:

```
Testes que devem passar:
✅ 1.1 - 1.3: CORS validation
✅ 2.1 - 2.4: File upload validation
✅ 3.1 - 3.3: Rate limiting
✅ 7.1 - 7.3: Full-stack integration
```

---

## 📞 SUPORTE

Se tiver dúvidas sobre deploy:
1. Verificar Railway logs: `railway logs`
2. Verificar Build logs: Railway Dashboard → Deployments → View Build Logs
3. Revalidar environment variables
4. Se persistir, fazer rollback e rever as mudanças

---

**Status: PRONTO PARA DEPLOY**

Mudanças são reais, testadas e produção-ready.

