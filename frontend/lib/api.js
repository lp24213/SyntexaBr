import { getClientLocale } from "./i18n";
export { getClientLocale } from "./i18n";

/**
 * API pública (produção): build estático usa sempre este host (sem override acidental no Pages).
 * Dev local: opcional NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
 */
const PRODUCTION_API_BASE = "https://api.syntexabr.com.br";

/** Mensagem única e segura para o utilizador (sem detalhes técnicos). */
export const USER_FACING_TRY_AGAIN =
  "Não foi possível concluir agora. Tente novamente em alguns instantes.";

export const USER_FACING_CONNECTION =
  "Conexão instável. Verifique a internet e tente de novo.";

function isForbiddenApiHost(url) {
  try {
    const u = new URL(url);
    const h = (u.hostname || "").toLowerCase();
    return (
      h === "localhost" ||
      h === "127.0.0.1" ||
      h === "::1" ||
      h === "0.0.0.0" ||
      /^127\.\d+\.\d+\.\d+$/.test(h)
    );
  } catch {
    return true;
  }
}

export function getApiBase() {
  const isDev =
    typeof process !== "undefined" &&
    process.env &&
    process.env.NODE_ENV === "development";
  if (isDev && process.env.NEXT_PUBLIC_API_BASE) {
    const raw = String(process.env.NEXT_PUBLIC_API_BASE).trim();
    if (raw) {
      const normalized = raw.replace(/\/$/, "");
      const withScheme = normalized.startsWith("http")
        ? normalized
        : `https://${normalized}`;
      if (!isForbiddenApiHost(withScheme)) {
        return withScheme.replace(/\/$/, "");
      }
    }
  }
  // Em produção: sempre usar PRODUCTION_API_BASE (api.syntexabr.com.br)
  // Não usar window.location.origin pois frontend pode estar em .pages.dev
  return PRODUCTION_API_BASE.replace(/\/$/, "");
}

const API_BASE = getApiBase();

/** Limite de saída pedido ao backend (alinhado a respostas longas / tabelas). */
export const CHAT_MAX_TOKENS = 8192;
const STREAM_IDLE_TIMEOUT_MS = 45000;
const STREAM_TOTAL_TIMEOUT_MS = 180000;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Fetch com retry (5xx / rede) na única base de produção (API_BASE).
 */
export async function fetchWithResilience(path, options = {}) {
  const retries = typeof options.__retries === "number" ? options.__retries : 2;
  const { __retries, ...fetchOpts } = options;
  const pathStr = typeof path === "string" ? path : String(path);
  const urlPath = pathStr.startsWith("/") ? pathStr : "/" + pathStr;
  const url = API_BASE.replace(/\/$/, "") + urlPath;

  let lastErr = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const resp = await fetch(url, fetchOpts);
      if (resp.ok) return resp;
      if (resp.status >= 500 && resp.status < 600 && attempt < retries) {
        await sleep(350 * (attempt + 1));
        continue;
      }
      if (resp.status >= 400 && resp.status < 500) return resp;
      if (attempt < retries) {
        await sleep(350 * (attempt + 1));
        continue;
      }
      return resp;
    } catch (e) {
      lastErr = e;
      if (attempt < retries) {
        await sleep(350 * (attempt + 1));
        continue;
      }
    }
  }
  throw new Error(lastErr && /fetch|network|failed/i.test(String(lastErr.message || "")) ? USER_FACING_CONNECTION : USER_FACING_TRY_AGAIN);
}

/**
 * Lê erro HTTP sem expor texto bruto do servidor (exceto 403 de limite de plano).
 */
async function readErrorMessage(resp, _fallbackUnused) {
  const raw = await resp.text();
  if (resp.status === 403) {
    try {
      const data = JSON.parse(raw);
      const d = data && typeof data.detail === "string" ? data.detail.trim() : "";
      if (d && /limite|plano|upgrade|mensagens/i.test(d)) {
        return d;
      }
    } catch (_) {}
    return USER_FACING_TRY_AGAIN;
  }
  if (resp.status === 401) {
    return "Sessão expirada ou acesso não autorizado. Entre novamente.";
  }
  return USER_FACING_TRY_AGAIN;
}

async function throwIfNotOk(resp) {
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
}

function parseSSEChunkedTextIntoJsonLines(rawText, state) {
  // Junta fragmentos de rede para não perder JSON parcial.
  state.buffer += rawText;
  const lines = state.buffer.split("\n");
  state.buffer = lines.pop() || "";
  return lines;
}

function flushSseTail(state, onChunk) {
  const leftover = String(state.buffer || "").trim();
  state.buffer = "";
  if (!leftover.startsWith("data: ")) return;
  try {
    const data = JSON.parse(leftover.slice(6));
    if (data.content && onChunk) onChunk(data.content);
  } catch (_) {}
}

function createStreamGuard(externalSignal, idleMs = STREAM_IDLE_TIMEOUT_MS, totalMs = STREAM_TOTAL_TIMEOUT_MS) {
  const controller = new AbortController();
  let idleTimer = null;
  let totalTimer = null;

  const clearTimers = () => {
    if (idleTimer) clearTimeout(idleTimer);
    if (totalTimer) clearTimeout(totalTimer);
    idleTimer = null;
    totalTimer = null;
  };

  const abortNow = () => {
    clearTimers();
    if (!controller.signal.aborted) controller.abort();
  };

  const armIdle = () => {
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(abortNow, Math.max(3000, Number(idleMs) || STREAM_IDLE_TIMEOUT_MS));
  };

  totalTimer = setTimeout(abortNow, Math.max(5000, Number(totalMs) || STREAM_TOTAL_TIMEOUT_MS));
  armIdle();

  if (externalSignal) {
    if (externalSignal.aborted) abortNow();
    else externalSignal.addEventListener("abort", abortNow, { once: true });
  }

  return {
    signal: controller.signal,
    touch: armIdle,
    cleanup: clearTimers,
  };
}

export async function login(email, password, turnstileToken = "") {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  body.set("grant_type", "password");
  const headers = { "Content-Type": "application/x-www-form-urlencoded" };
  if (turnstileToken) {
    headers["X-Turnstile-Token"] = turnstileToken;
  }
  const resp = await fetchWithResilience("/v1/auth/login", {
    method: "POST",
    headers,
    body,
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  const data = await resp.json();
  return data;
}

export async function verifyTwoFactor(twoFactorToken, code) {
  const resp = await fetchWithResilience("/v1/auth/2fa/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      two_factor_token: twoFactorToken,
      code,
    }),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function setupTwoFactor(token) {
  const resp = await fetchWithResilience("/v1/auth/2fa/setup", {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function enableTwoFactor(token, code) {
  const resp = await fetchWithResilience("/v1/auth/2fa/enable", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ code }),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export function githubLoginUrl() {
  var origin =
    typeof window !== "undefined" && window.location && window.location.origin
      ? window.location.origin.replace(/\/$/, "")
      : "https://syntexabr.com.br";
  return origin + "/v1/auth/github/login";
}

export async function listIntegrationTokens(token) {
  const resp = await fetchWithResilience("/v1/integrations/tokens", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function createIntegrationToken(token, payload) {
  const resp = await fetchWithResilience("/v1/integrations/tokens", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(payload || {}),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function revokeIntegrationToken(token, tokenId) {
  const resp = await fetchWithResilience("/v1/integrations/tokens/" + tokenId, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return true;
}

export async function rotateIntegrationToken(token, tokenId) {
  const resp = await fetchWithResilience("/v1/integrations/tokens/" + tokenId + "/rotate", {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function getIntegrationConfig(token) {
  const resp = await fetchWithResilience("/v1/integrations/config", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function setIntegrationConfig(token, payload) {
  const resp = await fetchWithResilience("/v1/integrations/config", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(payload || {}),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function getMe(token) {
  const resp = await fetchWithResilience( "/v1/auth/me", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return null;
  return resp.json();
}

export async function updateMe(token, payload) {
  const resp = await fetchWithResilience("/v1/auth/me", {
    method: "PUT",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload || {}),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function chatCompletion(token, history, sessionId) {
  const locale = getClientLocale();
  const headers = { "Content-Type": "application/json", "Accept-Language": locale };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/chat/completions", {
    method: "POST",
    headers,
    body: JSON.stringify({
      model: "syntexa-large",
      messages: history,
      max_tokens: CHAT_MAX_TOKENS,
      session_id: sessionId || undefined,
      locale,
    }),
  });
  if (!resp.ok) {
    throw new Error(await readErrorMessage(resp));
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

export async function chatCompletionStream(token, history, onChunk, signal, sessionId) {
  const guard = createStreamGuard(signal);
  try {
    const locale = getClientLocale();
    const headers = { "Content-Type": "application/json", "Accept-Language": locale };
    if (token) headers.Authorization = "Bearer " + token;
    const resp = await fetchWithResilience( "/v1/chat/completions/stream", {
      method: "POST",
      headers,
      body: JSON.stringify({
        model: "syntexa-large",
        messages: history,
        max_tokens: CHAT_MAX_TOKENS,
        session_id: sessionId || undefined,
        locale,
      }),
      signal: guard.signal,
    });
    if (!resp.ok) {
      throw new Error(await readErrorMessage(resp));
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
    let full = "";
    const state = { buffer: "" };
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      guard.touch();
      const chunk = decoder.decode(value, { stream: true });
      const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              full += data.content;
              if (onChunk) onChunk(data.content);
            }
          } catch (_) {}
        }
      }
    }
    flushSseTail(state, (c) => {
      full += c;
      if (onChunk) onChunk(c);
    });
    return full || "Nenhuma resposta retornada.";
  } finally {
    guard.cleanup();
  }
}

/**
 * Se o stream falhar antes de qualquer token, obtém resposta completa sem stream.
 * Se já houver texto parcial, propaga o erro (evita duplicar conteúdo na UI).
 */
export async function chatCompletionStreamWithFallback(token, history, onChunk, signal, sessionId) {
  var received = "";
  try {
    return await chatCompletionStream(
      token,
      history,
      function (c) {
        received += c;
        if (onChunk) onChunk(c);
      },
      signal,
      sessionId
    );
  } catch (e) {
    if (!String(received || "").trim()) {
      const text = await chatCompletion(token, history, sessionId);
      if (onChunk) onChunk(text);
      return text;
    }
    throw e;
  }
}

export async function chatCompletionWithMedia(token, history, files, sessionId) {
  const locale = getClientLocale();
  const form = new FormData();
  form.append(
    "payload",
    JSON.stringify({
      model: "syntexa-large",
      messages: history,
      max_tokens: CHAT_MAX_TOKENS,
      session_id: sessionId || undefined,
      locale,
    })
  );
  for (const file of files) {
    form.append("files", file);
  }
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  headers["Accept-Language"] = locale;
  const resp = await fetchWithResilience( "/v1/chat/completions", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readErrorMessage(resp));
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

export async function publicChat(history) {
  const locale = getClientLocale();
  const resp = await fetchWithResilience( "/v1/public-chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept-Language": locale },
    body: JSON.stringify({
      model: "syntexa-large",
      messages: history,
      max_tokens: CHAT_MAX_TOKENS,
      locale,
    }),
  });
  if (!resp.ok) {
    throw new Error(await readErrorMessage(resp));
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

/**
 * Chat público em streaming: resposta imediata, texto aparece aos poucos.
 * onChunk(content) é chamado a cada pedaço; retorna o texto completo ao terminar.
 */
export async function publicChatStream(history, onChunk, signal) {
  const guard = createStreamGuard(signal);
  try {
    const locale = getClientLocale();
    const resp = await fetchWithResilience( "/v1/public-chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept-Language": locale },
      body: JSON.stringify({
        model: "syntexa-large",
        messages: history,
        max_tokens: CHAT_MAX_TOKENS,
        locale,
      }),
      signal: guard.signal,
    });
    if (!resp.ok) {
      throw new Error(await readErrorMessage(resp));
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
    let full = "";
    const state = { buffer: "" };
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      guard.touch();
      const chunk = decoder.decode(value, { stream: true });
      const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              full += data.content;
              if (onChunk) onChunk(data.content);
            }
          } catch (_) {}
        }
      }
    }
    flushSseTail(state, (c) => {
      full += c;
      if (onChunk) onChunk(c);
    });
    return full || "Nenhuma resposta retornada.";
  } finally {
    guard.cleanup();
  }
}

export async function publicChatStreamWithFallback(history, onChunk, signal) {
  var received = "";
  try {
    return await publicChatStream(
      history,
      function (c) {
        received += c;
        if (onChunk) onChunk(c);
      },
      signal
    );
  } catch (e) {
    if (!String(received || "").trim()) {
      const text = await publicChat(history);
      if (onChunk) onChunk(text);
      return text;
    }
    throw e;
  }
}

export async function publicChatWithMedia(history, files) {
  const locale = getClientLocale();
  const form = new FormData();
  form.append(
    "payload",
    JSON.stringify({
      model: "vereda-small-echo",
      messages: history,
      max_tokens: CHAT_MAX_TOKENS,
      locale,
    })
  );
  for (const file of files) {
    form.append("files", file);
  }
  const resp = await fetchWithResilience( "/v1/public-chat", {
    method: "POST",
    headers: { "Accept-Language": locale },
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readErrorMessage(resp));
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

/**
 * Retorna o perfil do usuário logado (inclui subscription_plan para limites da IA).
 */
export async function getProfile(token) {
  if (!token) return null;
  const resp = await fetchWithResilience( "/v1/auth/me", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return null;
  return resp.json();
}

/** Lista de IPs cadastrados pelo admin (referência para rede institucional). */
export async function getAdminAllowedIps(token) {
  const resp = await fetchWithResilience( "/v1/admin/network/allowed-ips", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error("Não foi possível carregar IPs.");
  return resp.json();
}

export async function putAdminAllowedIps(token, ips) {
  const resp = await fetchWithResilience( "/v1/admin/network/allowed-ips", {
    method: "PUT",
    headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
    body: JSON.stringify({ ips: Array.isArray(ips) ? ips : [] }),
  });
  if (!resp.ok) throw new Error("Não foi possível salvar IPs.");
  return resp.json();
}

export async function getAdminMe(token) {
  const resp = await fetchWithResilience("/v1/admin/me", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return null;
  return resp.json();
}

export async function getAdminSystemStatus(token) {
  const resp = await fetchWithResilience("/v1/admin/system/status", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error(USER_FACING_TRY_AGAIN);
  return resp.json();
}

export async function pentestAdminPreflight(token, payload) {
  const resp = await fetchWithResilience("/v1/chat/pentest-admin/preflight", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload || {}),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function pentestAdminRun(token, payload) {
  const resp = await fetchWithResilience("/v1/chat/pentest-admin", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload || {}),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function pentestAdminSuite(token, payload) {
  const resp = await fetchWithResilience("/v1/chat/pentest-admin/suite", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload || {}),
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function getPentestAdminHistory(token, limit = 50) {
  const cap = Math.min(Math.max(Number(limit) || 50, 1), 200);
  const resp = await fetchWithResilience("/v1/chat/pentest-admin/history?limit=" + cap, {
    headers: {
      Authorization: "Bearer " + token,
    },
  });
  if (!resp.ok) throw new Error(await readErrorMessage(resp));
  return resp.json();
}

export async function listChatSessions(token) {
  if (!token) return [];
  const resp = await fetchWithResilience( "/v1/chat/sessions", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return [];
  return resp.json();
}

export async function getChatSessionMessages(sessionId, token) {
  if (!token) return [];
  const resp = await fetchWithResilience( "/v1/chat/sessions/" + sessionId + "/messages", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return [];
  return resp.json();
}

async function mergeImageBase64FromWhitelistedUrl(data, token) {
  if (!data || data.image_base64) return data;
  const rawUrl = data.url || data.image_url;
  if (!rawUrl || typeof rawUrl !== "string") return data;
  const fd = new FormData();
  fd.append("url", rawUrl);
  const h = {};
  if (token) h.Authorization = "Bearer " + token;
  try {
    const r2 = await fetchWithResilience( "/v1/media/images/fetch-url", {
      method: "POST",
      headers: h,
      body: fd,
    });
    if (!r2.ok) return data;
    const j = await r2.json();
    if (j && j.image_base64) {
      data.image_base64 = j.image_base64;
      data.mime = j.mime || data.mime || "image/jpeg";
    }
  } catch (_) {}
  return data;
}

export async function generateImage(prompt, token) {
  /** Por defeito: API no backend (Pollinations/Azure/local) — sem login Puter. Puter só com NEXT_PUBLIC_USE_PUTER_IMAGES=1 */
  const puterExplicit =
    typeof window !== "undefined" &&
    typeof process !== "undefined" &&
    process.env &&
    process.env.NEXT_PUBLIC_USE_PUTER_IMAGES === "1";

  const form = new FormData();
  form.append("prompt", prompt);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;

  if (!puterExplicit) {
    try {
      const resp = await fetchWithResilience("/v1/media/images/generate", {
        method: "POST",
        headers,
        body: form,
      });
      if (resp.ok) {
        const data = await resp.json();
        return mergeImageBase64FromWhitelistedUrl(data, token);
      }
    } catch (_e) {
      /* tenta Puter só se explícito abaixo */
    }
  }

  if (puterExplicit) {
    try {
      const { generateImageWithPuter } = await import("./puter-image.js");
      const data = await generateImageWithPuter(prompt);
      return mergeImageBase64FromWhitelistedUrl(data, token);
    } catch (_e) {
      /* fallback servidor */
    }
  }

  const resp = await fetchWithResilience("/v1/media/images/generate", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readErrorMessage(resp));
  }
  const data = await resp.json();
  return mergeImageBase64FromWhitelistedUrl(data, token);
}

export async function generateVideo(prompt, token) {
  const form = new FormData();
  form.append("prompt", prompt);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/media/videos/generate", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readErrorMessage(resp));
  }
  return resp.json();
}

export async function generateMusic(prompt, token) {
  const form = new FormData();
  form.append("prompt", prompt);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/media/music/generate", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readErrorMessage(resp));
  }
  return resp.json();
}

// ---------------------------------------------------------------------------
// Educação & Pesquisa
// ---------------------------------------------------------------------------

/** Tutor de IA para alunos — público. Suporta discipline, level, language, mode. */
export async function educationTutor(discipline, question, mode, history, level, language, feedback) {
  const resp = await fetchWithResilience( "/v1/education/tutor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      discipline, question,
      mode: mode || "chat",
      history: history || [],
      level: level || "intermediario",
      language: language || "pt",
      feedback: feedback || null,
    }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Tutor streaming para alunos — onChunk(text) chamado a cada fragmento. */
export async function educationTutorStream(discipline, question, mode, history, onChunk, signal, level, language, feedback) {
  const resp = await fetchWithResilience( "/v1/education/tutor/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      discipline, question,
      mode: mode || "chat",
      history: history || [],
      level: level || "intermediario",
      language: language || "pt",
      feedback: feedback || null,
    }),
    signal,
  });
  await throwIfNotOk(resp);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
  let full = "";
  const state = { buffer: "" };
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content) { full += data.content; if (onChunk) onChunk(data.content); }
        } catch (_) {}
      }
    }
  }
  return full || "Sem resposta.";
}

/** Ferramentas para professor/pesquisador — requer token. */
export async function teacherChat(token, task, content, context, level, language) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/education/teacher/chat", {
    method: "POST",
    headers,
    body: JSON.stringify({ task, content, context: context || null, level: level || "avancado", language: language || "pt" }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Ferramentas do professor em streaming. */
export async function teacherChatStream(token, task, content, context, level, language, onChunk, signal) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/education/teacher/chat/stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ task, content, context: context || null, level: level || "avancado", language: language || "pt" }),
    signal,
  });
  await throwIfNotOk(resp);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
  let full = "";
  const state = { buffer: "" };
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content) { full += data.content; if (onChunk) onChunk(data.content); }
        } catch (_) {}
      }
    }
  }
  return full || "Sem resposta.";
}

/** Motor de cálculo simbólico/numérico — público. */
export async function educationCompute(expression, computeType, variable) {
  const resp = await fetchWithResilience( "/v1/education/compute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ expression, compute_type: computeType || "auto", variable: variable || "x" }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Sandbox de código Python/JS — público. */
export async function educationCodeSandbox(code, language, timeout) {
  const resp = await fetchWithResilience( "/v1/education/compute/code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language: language || "python", timeout: timeout || 10 }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Ferramenta de pesquisa científica para professores — requer token. */
export async function teacherResearch(token, task, content, extra, language) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/education/teacher/research", {
    method: "POST",
    headers,
    body: JSON.stringify({ task: task || "analisar", content, extra: extra || null, language: language || "pt" }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Ferramenta de pesquisa em streaming — requer token. */
export async function teacherResearchStream(token, task, content, extra, language, onChunk, signal) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/education/teacher/research/stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ task: task || "analisar", content, extra: extra || null, language: language || "pt" }),
    signal,
  });
  await throwIfNotOk(resp);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
  let full = "";
  const state = { buffer: "" };
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content) { full += data.content; if (onChunk) onChunk(data.content); }
        } catch (_) {}
      }
    }
  }
  return full || "Sem resposta.";
}

/** Estatísticas para o painel governamental — requer token de admin. */
export async function govStats(token) {
  const resp = await fetchWithResilience( "/v1/education/gov/stats", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error(USER_FACING_TRY_AGAIN);
  return resp.json();
}

/** Gera relatório educacional via IA — requer token de admin. */
export async function govGenerateReport(token, type, period, region) {
  const resp = await fetchWithResilience( "/v1/education/gov/report", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
    body: JSON.stringify({ type: type || "geral", period: period || "mensal", region: region || "nacional" }),
  });
  if (!resp.ok) throw new Error(USER_FACING_TRY_AGAIN);
  return resp.json();
}

/** Previsão educacional com IA — requer token de admin. */
export async function govPredict(token, scenario, context) {
  const resp = await fetchWithResilience( "/v1/education/gov/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
    body: JSON.stringify({ scenario, context: context || null }),
  });
  if (!resp.ok) throw new Error(USER_FACING_TRY_AGAIN);
  return resp.json();
}

/** Geração de política pública — requer token de admin. */
export async function govPolicy(token, challenge, region, budget) {
  const resp = await fetchWithResilience( "/v1/education/gov/policy", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
    body: JSON.stringify({ challenge, region: region || null, budget: budget || null }),
  });
  if (!resp.ok) throw new Error(USER_FACING_TRY_AGAIN);
  return resp.json();
}

/** Corrige redação no formato ENEM (5 competências, 0-1000) — anônimo. */
export async function gradeEnemEssay(essay, theme, language) {
  const resp = await fetchWithResilience( "/v1/education/essay/grade", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ essay, theme: theme || null, language: language || "pt" }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Correção de redação ENEM em streaming — anônimo. */
export async function gradeEnemEssayStream(essay, theme, language, onChunk, signal) {
  const resp = await fetchWithResilience( "/v1/education/essay/grade/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ essay, theme: theme || null, language: language || "pt" }),
    signal,
  });
  await throwIfNotOk(resp);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
  let full = "";
  const state = { buffer: "" };
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content) { full += data.content; if (onChunk) onChunk(data.content); }
        } catch (_) {}
      }
    }
  }
  return full || "Sem resposta.";
}

/** Tutor de concursos públicos e vestibulares — anônimo. */
export async function concursosTutor(exam, subject, question, level, language, history) {
  const resp = await fetchWithResilience( "/v1/education/concursos/tutor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exam: exam || "enem", subject: subject || "geral", question, level: level || "avancado", language: language || "pt", history: history || [] }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Tutor de concursos em streaming — anônimo. */
export async function concursosTutorStream(exam, subject, question, level, language, history, onChunk, signal) {
  const resp = await fetchWithResilience( "/v1/education/concursos/tutor/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exam: exam || "enem", subject: subject || "geral", question, level: level || "avancado", language: language || "pt", history: history || [] }),
    signal,
  });
  await throwIfNotOk(resp);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
  let full = "";
  const state = { buffer: "" };
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content) { full += data.content; if (onChunk) onChunk(data.content); }
        } catch (_) {}
      }
    }
  }
  return full || "Sem resposta.";
}

/** Política de privacidade do módulo educacional — confirma anonimato. */
export async function educationPrivacy() {
  const resp = await fetchWithResilience( "/v1/education/privacy");
  if (!resp.ok) return null;
  return resp.json();
}

/** Tutor científico especializado — público, anônimo. */
export async function educationScience(area, question, level, language, history) {
  const resp = await fetchWithResilience( "/v1/education/science", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      area: area || "geral",
      question,
      level: level || "avancado",
      language: language || "pt",
      history: history || [],
    }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Tutor científico em streaming — público, anônimo. */
export async function educationScienceStream(area, question, level, language, history, onChunk, signal) {
  const resp = await fetchWithResilience( "/v1/education/science/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      area: area || "geral",
      question,
      level: level || "avancado",
      language: language || "pt",
      history: history || [],
    }),
    signal,
  });
  await throwIfNotOk(resp);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: false, ignoreBOM: true });
  let full = "";
  const state = { buffer: "" };
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = parseSSEChunkedTextIntoJsonLines(chunk, state);
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content) { full += data.content; if (onChunk) onChunk(data.content); }
        } catch (_) {}
      }
    }
  }
  return full || "Sem resposta.";
}

// ─── Multimodal (análise, exportação, STT/TTS unificados) ─────────────────

export async function multimodalCapabilities() {
  const resp = await fetchWithResilience("/v1/multimodal/capabilities");
  await throwIfNotOk(resp);
  return resp.json();
}

/** INTENÇÃO -> xlsx/pdf/docx/csv/txt + resumo + TTS (Azure quando configurado). */
export async function multimodalSmartExport(
  userMessage,
  token,
  generateAudio,
  assistantReply
) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const ar =
    assistantReply != null && String(assistantReply).trim()
      ? String(assistantReply).slice(0, 500000)
      : undefined;
  const resp = await fetchWithResilience("/v1/multimodal/smart-export", {
    method: "POST",
    headers,
    body: JSON.stringify({
      user_message: userMessage,
      generate_audio: generateAudio !== false,
      ...(ar ? { assistant_reply: ar } : {}),
    }),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

export async function multimodalAnalyze(file, { deep = false, token = null } = {}) {
  const form = new FormData();
  form.append("file", file);
  form.append("deep", deep ? "true" : "false");
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/multimodal/analyze", {
    method: "POST",
    headers,
    body: form,
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Evita guardar JSON como “.pdf” quando o origin devolve erro em 200 (raro). */
async function _blobFromExportResponse(resp, label) {
  if (!resp.ok) {
    await throwIfNotOk(resp);
  }
  const buf = await resp.arrayBuffer();
  if (buf.byteLength >= 1) {
    const first = new Uint8Array(buf.slice(0, 1))[0];
    if (first === 0x7b) {
      try {
        const j = JSON.parse(new TextDecoder().decode(buf));
        throw new Error(
          (j && j.detail) || label + ": o servidor devolveu JSON em vez do ficheiro."
        );
      } catch (e) {
        if (e instanceof Error && /JSON|servidor/i.test(e.message)) throw e;
      }
    }
  }
  return new Blob([buf]);
}

export async function multimodalExportPdf(body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/multimodal/export/pdf", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  return _blobFromExportResponse(resp, "PDF");
}

export async function multimodalExportXlsx(body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/multimodal/export/xlsx", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  return _blobFromExportResponse(resp, "Excel");
}

export async function multimodalExportDocx(body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/multimodal/export/docx", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  return _blobFromExportResponse(resp, "Word");
}

export async function multimodalExportTxt(body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/multimodal/export/txt", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  return _blobFromExportResponse(resp, "TXT");
}

/** Áudio → STT → chat → TTS (resposta com audio_url base64). */
export async function multimodalVoiceConversation(file, token, maxTokens) {
  const form = new FormData();
  form.append("file", file);
  if (maxTokens) form.append("max_tokens", String(maxTokens));
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/multimodal/voice/conversation", {
    method: "POST",
    headers,
    body: form,
  });
  await throwIfNotOk(resp);
  return resp.json();
}

export async function multimodalTranscribe(file, token) {
  const form = new FormData();
  form.append("file", file);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/multimodal/transcribe", {
    method: "POST",
    headers,
    body: form,
  });
  const raw = await resp.text();
  let data = null;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch {
    data = null;
  }
  if (!resp.ok) {
    const detail =
      (data && (data.detail || data.message)) ||
      raw ||
      (await readErrorMessage(resp).catch(() => USER_FACING_TRY_AGAIN));
    throw new Error(String(detail || USER_FACING_TRY_AGAIN));
  }
  return data && typeof data === "object" ? data : { ok: false, text: "", detail: USER_FACING_TRY_AGAIN };
}

/** STT no servidor via LOCAL_STT_ENDPOINT (Whisper HTTP próprio) — legado; chat usa Xenova no browser. */
export async function transcribeAudioBlob(blob, token, filename) {
  if (!blob || blob.size < 256) {
    throw new Error("Gravação muito curta. Fale por mais tempo e tente de novo.");
  }
  const name = filename || "gravacao.webm";
  const type = blob.type || "audio/webm";
  const file = new File([blob], name, { type });
  const data = await multimodalTranscribe(file, token);
  const text = String((data && data.text) || "").trim();
  if (!text) {
    throw new Error(
      String((data && data.detail) || "Transcrição vazia. Verifique AZURE_SPEECH_KEY no servidor.")
    );
  }
  return text;
}

/** Voz (TTS) em PT-BR via backend (edge-tts). Requer login. */
export async function generateSpeech(text, token, voice) {
  const form = new FormData();
  form.append("text", text);
  if (voice) form.append("voice", voice);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience( "/v1/media/tts/generate", {
    method: "POST",
    headers,
    body: form,
  });
  await throwIfNotOk(resp);
  return resp.json();
}

// ─── Gestão Institucional (Admin) ───────────────────────────────────────────

function _adminHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("syntexa_token") : null;
  const h = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = "Bearer " + token;
  return h;
}

export async function institutionalListClients({ activeOnly = false } = {}) {
  const qs = activeOnly ? "?active_only=true" : "";
  const resp = await fetchWithResilience( "/v1/institutional/clients" + qs, { headers: _adminHeaders() });
  await throwIfNotOk(resp);
  return resp.json();
}

export async function institutionalCreateClient(data) {
  const resp = await fetchWithResilience( "/v1/institutional/clients", {
    method: "POST",
    headers: _adminHeaders(),
    body: JSON.stringify(data),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

export async function institutionalUpdateClient(id, data) {
  const resp = await fetchWithResilience( "/v1/institutional/clients/" + id, {
    method: "PATCH",
    headers: _adminHeaders(),
    body: JSON.stringify(data),
  });
  await throwIfNotOk(resp);
  return resp.json();
}

export async function institutionalDeactivateClient(id) {
  const resp = await fetchWithResilience( "/v1/institutional/clients/" + id, {
    method: "DELETE",
    headers: _adminHeaders(),
  });
  await throwIfNotOk(resp);
  return { ok: true };
}

export async function institutionalRenewClient(id, expiresDays = 365) {
  const resp = await fetchWithResilience(
    "/v1/institutional/clients/" + id + "/renew?expires_days=" + expiresDays,
    { method: "POST", headers: _adminHeaders() }
  );
  await throwIfNotOk(resp);
  return resp.json();
}

export async function institutionalRegenerateKey(id) {
  const resp = await fetchWithResilience(
    "/v1/institutional/clients/" + id + "/regenerate-key",
    { method: "POST", headers: _adminHeaders() }
  );
  await throwIfNotOk(resp);
  return resp.json();
}

// ─── Subscription API ───────────────────────────────────────────

/** Busca status da subscription do usuario */
export async function getSubscriptionStatus(token) {
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/subscription/status", {
    headers,
  });
  await throwIfNotOk(resp);
  return resp.json();
}

/** Cria checkout Stripe para um plano */
export async function createStripeCheckout(plan, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetchWithResilience("/v1/payments/stripe/checkout", {
    method: "POST",
    headers,
    body: JSON.stringify({ plan }),
  });
  await throwIfNotOk(resp);
  const data = await resp.json();
  return data.url;
}
