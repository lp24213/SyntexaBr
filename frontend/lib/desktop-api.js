/**
 * SYNTEXA DESKTOP LOCAL API CLIENT
 * =================================
 * Comunicação com o backend Python local do app desktop Electron.
 * Fallback automático para API online quando o desktop não está disponível.
 *
 * Detecção de modo:
 * - window.__DESKTOP_MODE__ = true  → Backend local ativo
 * - window.__DESKTOP_MODE__ = false → Modo web/API online
 */

const DESKTOP_HOST = "http://127.0.0.1";
const DESKTOP_DEFAULT_PORT = 34560;

/** Só o app Syntexa Desktop (preload) — não Cursor/VS Code/outros Electron. */
function isDesktopMode() {
  if (typeof window === "undefined") return false;
  return window.__DESKTOP_MODE__ === true;
}

/** Obtém a porta do backend local (descoberta dinâmica via IPC) */
function getDesktopPort() {
  if (typeof window !== "undefined" && window.__DESKTOP_PORT__) {
    return window.__DESKTOP_PORT__;
  }
  return DESKTOP_DEFAULT_PORT;
}

/** Base URL do backend local */
function desktopBaseUrl() {
  return `${DESKTOP_HOST}:${getDesktopPort()}`;
}

/** Health check do backend local */
export async function desktopHealthCheck() {
  try {
    const res = await fetch(`${desktopBaseUrl()}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return { ok: false, status: res.status };
    const data = await res.json();
    return { ok: true, ...data };
  } catch (err) {
    return { ok: false, error: String(err) };
  }
}

/** Chat completion via backend local (não-streaming) */
export async function desktopChatCompletion(messages, options = {}) {
  const body = {
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
    max_new_tokens: options.max_tokens || 1024,
    temperature: options.temperature ?? 0.7,
    top_p: options.top_p ?? 0.9,
    stream: false,
  };

  const res = await fetch(`${desktopBaseUrl()}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "Unknown error");
    throw new Error(`Desktop backend error ${res.status}: ${err}`);
  }

  const data = await res.json();
  return data.response || "";
}

/** Chat completion streaming via backend local */
export async function desktopChatStream(messages, onChunk, options = {}) {
  const body = {
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
    max_new_tokens: options.max_tokens || 1024,
    temperature: options.temperature ?? 0.7,
    top_p: options.top_p ?? 0.9,
    stream: true,
  };

  const controller = new AbortController();
  if (options.signal) {
    options.signal.addEventListener("abort", () => controller.abort());
  }

  const res = await fetch(`${desktopBaseUrl()}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: controller.signal,
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "Unknown error");
    throw new Error(`Desktop backend error ${res.status}: ${err}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;
        const payload = trimmed.slice(6);
        if (payload === "[DONE]") continue;

        try {
          const json = JSON.parse(payload);
          if (json.chunk) {
            onChunk(json.chunk);
          }
          if (json.done) {
            return;
          }
          if (json.error) {
            throw new Error(json.error);
          }
        } catch (e) {
          // ignora linhas malformadas do stream
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/** Processa upload multimodal no backend local */
export async function desktopProcessMultimodal(base64Data, mimeType, kind) {
  const res = await fetch(`${desktopBaseUrl()}/multimodal/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      base64_data: base64Data,
      mime_type: mimeType,
      kind: kind, // "image", "audio", "pdf"
    }),
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "Unknown error");
    throw new Error(`Multimodal error ${res.status}: ${err}`);
  }

  return res.json();
}

/** TTS via backend local */
export async function desktopTTS(text) {
  const res = await fetch(`${desktopBaseUrl()}/tts/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "Unknown error");
    throw new Error(`TTS error ${res.status}: ${err}`);
  }

  const data = await res.json();
  if (data.audio_base64) {
    return `data:${data.mime || "audio/wav"};base64,${data.audio_base64}`;
  }
  throw new Error(data.error || "TTS retornou áudio vazio");
}

/** Diagnóstico técnico real do boot validator */
export async function desktopBootDiagnostic() {
  try {
    const res = await fetch(`${desktopBaseUrl()}/boot/diagnostic`, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    });
    const data = await res.json();
    return { ok: res.ok, status: res.status, ...data };
  } catch (err) {
    return { ok: false, error: String(err) };
  }
}

/** Exporta conversa via backend local */
export async function desktopExportConversation(messages, format) {
  const res = await fetch(`${desktopBaseUrl()}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, format }),
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "Unknown error");
    throw new Error(`Export error ${res.status}: ${err}`);
  }

  return res.json();
}

/** Obtém status do backend */
export async function desktopBackendStatus() {
  if (typeof window !== "undefined" && window.desktopAPI && window.desktopAPI.backendStatus) {
    return window.desktopAPI.backendStatus();
  }
  return desktopHealthCheck();
}

// ── EXPORT UNIFICADO ──────────────────────────────────────
export { isDesktopMode, getDesktopPort, desktopBaseUrl };
