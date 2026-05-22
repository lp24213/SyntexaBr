# Alterações — commit `e761d2b`

**Data:** 22/05/2026  
**Repositório:** [lp24213/SyntexaBr](https://github.com/lp24213/SyntexaBr)  
**Mensagem:** `fix: chat API real, microfone e texto sem modo desktop falso`  
**Resumo:** 10 arquivos, +242 / −143 linhas (sem build, sem npm)

---

## Objetivo geral

Corrigir o chat que não enviava mensagens (falso modo desktop no Electron/Cursor), microfone, texto colado/quebrado e endpoint de API incorreto — tudo em fluxo **real**, sem fallback degradado.

---

## Arquivos modificados

### Frontend

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/app/chat/page.js` | Chat usa API online quando não é app Desktop real; stream com `sanitizeStreamChunk` + polish final; microfone com `SpeechRecognition` estável (`recognitionRef`, erros visíveis); botão de microfone sempre visível; botão “Fala” (TTS) com ícone de áudio, não microfone; sessão expirada sem cair para chat anônimo |
| `frontend/lib/desktop-api.js` | `isDesktopMode()` só retorna `true` com `window.__DESKTOP_MODE__` (preload do app Desktop) — removida detecção por `userAgent` Electron |
| `frontend/lib/api.js` | `publicChatWithMedia` corrigido de `/public-chat` para `/v1/public-chat` |
| `frontend/lib/sanitizeOutput.js` | `sanitizeStreamChunk` (leve, para SSE); `fixMojibakeEncoding` e `normalizeBrokenPortuguese`; espaço após pontuação colada |
| `frontend/components/AudioRecorder.js` | Label padrão alterado de “Perguntar em voz (IA)” para “Microfone” |

### Gateway / infraestrutura

| Arquivo | O que mudou |
|---------|-------------|
| `gateway_worker.js` | `Permissions-Policy`: `microphone=(self)` e `camera=(self)` (antes bloqueava microfone) |
| `cloudflare-workers/src/index.js` | Mesma correção de `Permissions-Policy` |
| `infrastructure/gateway-api/main.py` | Mesma correção de `Permissions-Policy` |

### Backend (Python)

| Arquivo | O que mudou |
|---------|-------------|
| `vereda_backend/main.py` | `Permissions-Policy`: `microphone=(self)` e `camera=(self)` |
| `vereda_backend/core/text_polish.py` | Espaço após `. , ! ?` e `; :` quando colados na palavra seguinte (ex.: `Olá.Como` → `Olá. Como`) |

---

## Lista rápida (caminhos)

```
cloudflare-workers/src/index.js
frontend/app/chat/page.js
frontend/components/AudioRecorder.js
frontend/lib/api.js
frontend/lib/desktop-api.js
frontend/lib/sanitizeOutput.js
gateway_worker.js
infrastructure/gateway-api/main.py
vereda_backend/core/text_polish.py
vereda_backend/main.py
```

---

## Como ver o diff completo

```bash
git show e761d2b
```

Ou no GitHub:  
https://github.com/lp24213/SyntexaBr/commit/e761d2b
