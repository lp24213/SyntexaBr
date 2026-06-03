# ✅ SYNTEXA SECURITY FIXES — VALIDATION CHECKLIST

**Executar após todos os deploys. Confirma que correções estão funcionando.**

---

## 1️⃣ CORS VALIDATION (Máxima Prioridade)

### Teste 1.1: Origin Whitelistado (✅ Deve funcionar)
```bash
curl -i -H "Origin: https://syntexabr.com.br" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -X OPTIONS \
  https://api.syntexabr.com.br/v1/auth/login

# Esperado:
# HTTP/1.1 204 No Content
# Access-Control-Allow-Origin: https://syntexabr.com.br
# Access-Control-Allow-Credentials: true
```

### Teste 1.2: Origin NÃO Whitelistado (❌ Deve rejeitar)
```bash
curl -i -H "Origin: https://attacker.com" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  https://api.syntexabr.com.br/v1/auth/login

# Esperado:
# HTTP/1.1 403 Forbidden
# OU sem header Access-Control-Allow-Origin
```

### Teste 1.3: Frontend Proxy CORS
```bash
curl -i -H "Origin: https://evilsite.com" \
  https://syntexabr.com.br/v1/auth/login

# Esperado: 403 ou sem CORS header
```

---

## 2️⃣ FILE UPLOAD VALIDATION (Máxima Prioridade)

### Teste 2.1: Upload .webm (✅ Deve aceitar)
```bash
# Criar arquivo de teste
echo "PK" > test.webm  # Simulação rápida

curl -F "audio=@test.webm" \
  -H "Content-Type: multipart/form-data" \
  https://api.syntexabr.com.br/api/stt/enqueue

# Esperado:
# { "ok": true, "jobId": "...", "status": "queued" }
```

### Teste 2.2: Upload .exe (❌ Deve rejeitar)
```bash
# Criar fake exe
echo "MZ" > malware.exe

curl -i -F "audio=@malware.exe" \
  https://api.syntexabr.com.br/api/stt/enqueue

# Esperado:
# HTTP/1.1 400 Bad Request
# { "error": "Extension not allowed: .exe" }
```

### Teste 2.3: MIME Type Spoofing (❌ Deve validar)
```bash
# Renomear um .txt como .mp3
echo "<?php system(\$_GET['c']); ?>" > shell.php
mv shell.php shell.mp3

# Server MIME type detection
curl -i -F "audio=@shell.mp3" \
  https://api.syntexabr.com.br/api/stt/enqueue

# Esperado:
# HTTP/1.1 400 Bad Request
# { "error": "MIME type not allowed: text/plain" }
```

### Teste 2.4: Path Traversal (❌ Deve blocar)
```bash
# Tentar traversal via filename
curl -i -F "audio=@../../../etc/passwd" \
  https://api.syntexabr.com.br/api/stt/enqueue

# Esperado:
# HTTP/1.1 400 Bad Request
# { "error": "Path traversal attempt detected" }
```

---

## 3️⃣ RATE LIMITING (Alto Risco)

### Teste 3.1: Rate Limit Ativado (✅ Deve bloquear)
```bash
#!/bin/bash
# Fazer 150+ requisições em 60 segundos
for i in {1..200}; do
  curl -s https://api.syntexabr.com.br/health | head -c 10 &
done
wait

# Esperado após ~120 requisições:
# { "error": "too_many_requests", "detail": "Muitas requisições..." }
# HTTP Status: 429 Too Many Requests
```

### Teste 3.2: Redis Persistence (✅ Contador deve manter)
```bash
# Requisição 1
curl -s https://api.syntexabr.com.br/health
# Esperado: { "ok": true, "service": "syntexa-api", "redis": "up" }

# Restart container/servidor (simular)
# docker restart syntexa-api

# Requisição 2 (depois do restart)
curl -s https://api.syntexabr.com.br/health
# Esperado: Contador NÃO reset (via Redis)
```

### Teste 3.3: Health Check Exempt (✅ Sem limite)
```bash
# /health deve não contar contra rate limit
for i in {1..300}; do
  curl -s https://api.syntexabr.com.br/health &
done
wait

# Esperado: Todas retornam 200 OK (não bloqueadas)
```

---

## 4️⃣ MICROPHONE / AUDIO (Alto Risco)

### Teste 4.1: Xenova Init Feedback
```
1. Abrir: https://syntexabr.com.br/i18n/pt-BR/chat/
2. Clicar no botão de microfone 🎤
3. ESPERADO: Mensagem "Carregando modelo de áudio..." (ou similar)
4. NÃO esperado: UI travada silenciosamente
5. Aguardar ~5-30s até o modelo carregar
6. Falar: "Olá, teste de áudio"
7. ESPERADO: Transcrição em português
```

### Teste 4.2: Timeout Behavior
```
1. Iniciar gravação
2. Deixar gravando por >60 segundos
3. Parar gravação
4. ESPERADO: Erro "Transcrição expirou (timeout 60s)" após 60s
5. NÃO esperado: App trava indefinidamente
```

### Teste 4.3: Fallback Web Speech
```
1. Forçar falha de Xenova (editar DevTools Console):
   global.transcriber = null
2. Iniciar gravação
3. Falar: "Teste fallback"
4. ESPERADO: Funciona com Web Speech API (menos preciso)
```

---

## 5️⃣ SERVICE WORKER VALIDATION

### Teste 5.1: SW Registrado
```javascript
// No console do navegador:
navigator.serviceWorker.getRegistrations().then(regs => {
  console.log("SW registrado:", regs.length > 0 ? "✅ SIM" : "❌ NÃO");
});
```

### Teste 5.2: Cache Funcionando
```
1. Abrir DevTools → Application → Service Workers
2. Recarregar página (F5)
3. Desconectar internet (DevTools → Network → Offline)
4. Navegação deve funcionar (cached)
5. ESPERADO: ✅ Offline mode funcional
```

### Teste 5.3: HEAD Request Sem Erro
```javascript
// No console:
fetch("https://production.syntexa-frontend.pages.dev/", { method: "HEAD" })
  .then(r => console.log("✅ HEAD OK:", r.status))
  .catch(e => console.error("❌ Erro:", e.message));

// ESPERADO: ✅ HEAD OK: 200 (ou 204)
```

---

## 6️⃣ I18N MANDARIM VALIDATION

### Teste 6.1: Cookie Reset
```javascript
// Console do navegador:
document.cookie = "syntexa_locale=; max-age=0; path=/";
localStorage.clear();
location.reload();
```

### Teste 6.2: Mandarim Load
```
1. Adicionar header Accept-Language: zh-CN
   (pode usar DevTools ou curl)
2. Navegar para: https://syntexabr.com.br/i18n/zh-CN/chat/
3. ESPERADO: Interface em MANDARIM (中文)
4. NÃO esperado: Português ou inglês
```

### Teste 6.3: Pages Dev Direct
```bash
# Testar deployment direct (sem gateway)
curl -H "Accept-Language: zh-CN" \
  https://production.syntexa-frontend.pages.dev/i18n/zh-CN/chat/ \
  | grep -i "中文|mandarim"

# ESPERADO: Conteúdo em mandarim presente
```

---

## 7️⃣ FULL-STACK INTEGRATION TEST

### Teste 7.1: Login Flow
```
1. Abrir: https://syntexabr.com.br/i18n/pt-BR/
2. Clicar em "Login"
3. Entrar com credenciais válidas
4. ESPERADO: ✅ Acesso liberado
5. DevTools Console → verificar token guardado (localStorage)
```

### Teste 7.2: Chat Streaming
```
1. Após login, ir para Chat
2. Escrever mensagem: "Olá, como vai?"
3. Enviar
4. ESPERADO: ✅ Resposta com streaming em tempo real
5. Verificar DevTools → Network → stream endpoint
   - Status: 200
   - Headers: Transfer-Encoding: chunked
   - Body: SSE format (data: {...})
```

### Teste 7.3: File Upload
```
1. No chat, clicar em ➕ Anexo
2. Selecionar arquivo: documento.pdf ou imagem.jpg
3. Enviar
4. ESPERADO: ✅ Upload bem-sucedido
5. DevTools → Network → /api/upload
   - Status: 202 Accepted
   - Response: { "ok": true, "jobId": "..." }
```

---

## 🎯 SCORING FINAL

**Marcar como ✅ após cada teste passar:**

- [ ] 1.1: CORS Whitelistado funciona
- [ ] 1.2: CORS rejeta origem inválida
- [ ] 1.3: Frontend CORS protegido
- [ ] 2.1: File .webm aceito
- [ ] 2.2: File .exe rejeitado
- [ ] 2.3: MIME spoofing detectado
- [ ] 2.4: Path traversal bloqueado
- [ ] 3.1: Rate limiting ativado (429)
- [ ] 3.2: Redis persiste após restart
- [ ] 3.3: /health não é limitado
- [ ] 4.1: Xenova feedback "loading"
- [ ] 4.2: Timeout 60s funciona
- [ ] 4.3: Fallback Web Speech funciona
- [ ] 5.1: Service Worker registrado
- [ ] 5.2: Offline mode funciona
- [ ] 5.3: HEAD request sem erro
- [ ] 6.1: Cookie mandarim reset funciona
- [ ] 6.2: Mandarim exibe corretamente
- [ ] 6.3: Pages dev mandarim funciona
- [ ] 7.1: Login flow funciona
- [ ] 7.2: Chat streaming funciona
- [ ] 7.3: File upload funciona

**Total: 22 testes**  
**Sucesso: Todos os 22 com ✅**

---

**Status Final:**
- 🟢 PRODUÇÃO SEGURA if todos os testes passarem
- 🟡 REVISÃO NECESSÁRIA se algum teste falhar
- 🔴 ROLLBACK RECOMENDADO se > 5 testes falharem

