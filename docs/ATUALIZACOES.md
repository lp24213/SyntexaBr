# Atualizações — Chat, microfone e STT Xenova

Documento vivo das mudanças recentes no **SyntexaBr**. Sem Azure no microfone do chat. Sem placeholder.

---

## Microfone do chat (como funciona de verdade)

| Etapa | O quê |
|-------|--------|
| 1 | Utilizador clica no **microfone** → `getUserMedia` + `MediaRecorder` grava WebM/Opus |
| 2 | Segundo clique **para** a gravação |
| 3 | **`@xenova/transformers`** carrega `Xenova/whisper-small` (ONNX, Hugging Face CDN na 1ª vez) |
| 4 | Transcrição **no navegador** — áudio não vai para Azure nem API de terceiros |
| 5 | Texto entra na caixa e a mensagem é **enviada** ao chat (API Syntexa normal) |

**Ficheiros principais**

- `frontend/lib/xenova-stt.js` — pipeline Whisper Xenova
- `frontend/app/chat/page.js` — botão microfone + gravação
- `frontend/components/AudioRecorder.js` — export/menu de voz também usa Xenova
- `frontend/package.json` — dependência `@xenova/transformers`

**Requisitos no browser**

- Chrome ou Edge (recomendado)
- HTTPS (ou localhost)
- Permitir microfone
- 1ª utilização: download do modelo (~dezenas de MB) — barra de estado em baixo do input

**Não usa**

- Azure Speech
- `/v1/multimodal/transcribe` no fluxo do microfone do chat
- `SpeechRecognition` do Google no browser

---

## Chat (envio de mensagens)

| Problema | Correção |
|----------|----------|
| Cursor/Electron detectado como “Desktop” | `isDesktopMode()` só com `window.__DESKTOP_MODE__` |
| Texto colado / encoding | `sanitizeStreamChunk` + `sanitizeOutput` |
| Anexos chat público | `publicChatWithMedia` → `/v1/public-chat` |

Ver também: [ALTERACOES-e761d2b-chat-microfone.md](./ALTERACOES-e761d2b-chat-microfone.md)

---

## Backend `/v1/multimodal/transcribe` (opcional)

Só para quem chama o endpoint à parte (não é o microfone do chat):

- **Whisper HTTP** via `LOCAL_STT_ENDPOINT` (ex. `production-node/worker-stt`)
- **ffmpeg** no servidor para WebM → WAV
- **Azure removido** do fluxo de `vereda_backend/audio/stt.py`

---

## Commits de referência

| Commit | Descrição |
|--------|-----------|
| `e761d2b` | Chat API real, desktop falso, sanitização |
| `0388e26` | Microfone WebM + transcribe API (substituído por Xenova) |
| *(atual)* | Xenova Whisper no browser, sem Azure |

---

## Deploy do frontend (sem surpresas)

1. `cd frontend`
2. `npm install` — instala `@xenova/transformers` (obrigatório no CI/Pages)
3. `npm run build` — gera `out/` estático

O modelo Xenova é baixado **no cliente** na 1ª gravação; não precisa commitar pesos no Git.

---

## Testar o microfone

1. Abrir `/chat/`
2. Clicar microfone → permitir
3. Falar 3–5 segundos → clicar de novo (parar)
4. Aguardar “Carregando Whisper (Xenova)…” na 1ª vez
5. Texto deve aparecer e a IA responder

Se falhar: consola do browser (F12) → erros de WASM/WebGPU; testar Chrome atualizado.

---

## Variáveis de ambiente (servidor — opcional)

```env
# Só se usar STT HTTP no backend (não no microfone do chat)
LOCAL_STT_ENDPOINT=http://127.0.0.1:PORT/transcribe
```

Não é necessário `AZURE_SPEECH_KEY` para o microfone do chat.
