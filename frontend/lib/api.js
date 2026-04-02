export function getApiBase() {
  if (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }
  // Producao: API dedicada (sem localhost / same-origin).
  return "https://api.syntexabr.com.br";
}
const API_BASE = getApiBase();

async function readErrorMessage(resp, fallbackMessage) {
  try {
    const data = await resp.json();
    if (data && typeof data.detail === "string" && data.detail.trim()) {
      return data.detail;
    }
    return fallbackMessage;
  } catch (_) {
    try {
      const txt = await resp.text();
      return txt || fallbackMessage;
    } catch (_) {
      return fallbackMessage;
    }
  }
}

function parseSSEChunkedTextIntoJsonLines(rawText, state) {
  // Junta fragmentos de rede para não perder JSON parcial.
  state.buffer += rawText;
  const lines = state.buffer.split("\n");
  state.buffer = lines.pop() || "";
  return lines;
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  body.set("grant_type", "password");
  const resp = await fetch(API_BASE + "/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!resp.ok) throw new Error("Credenciais inválidas");
  const data = await resp.json();
  return data.access_token;
}

export async function getMe(token) {
  const resp = await fetch(API_BASE + "/v1/auth/me", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return null;
  return resp.json();
}

export async function chatCompletion(token, history) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/chat/completions", {
    method: "POST",
    headers,
    body: JSON.stringify({ model: "syntexa-large", messages: history, max_tokens: 1024 }),
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro ao chamar IA: " + txt);
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

export async function chatCompletionStream(token, history, onChunk, signal) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/chat/completions/stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ model: "syntexa-large", messages: history, max_tokens: 1024 }),
    signal,
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro ao chamar IA: " + txt);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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
          if (data.content) {
            full += data.content;
            if (onChunk) onChunk(data.content);
          }
        } catch (_) {}
      }
    }
  }
  return full || "Nenhuma resposta retornada.";
}

export async function chatCompletionWithMedia(token, history, files) {
  const form = new FormData();
  form.append(
    "payload",
    JSON.stringify({
      model: "syntexa-large",
      messages: history,
      max_tokens: 1024,
    })
  );
  for (const file of files) {
    form.append("files", file);
  }
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/chat/completions", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro ao chamar IA com mídia: " + txt);
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

export async function publicChat(history) {
  const resp = await fetch(API_BASE + "/public-chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "syntexa-large",
      messages: history,
      max_tokens: 1024,
    }),
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro no modo gratuito: " + txt);
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

/**
 * Chat público em streaming: resposta imediata, texto aparece aos poucos.
 * onChunk(content) é chamado a cada pedaço; retorna o texto completo ao terminar.
 */
export async function publicChatStream(history, onChunk, signal) {
  const resp = await fetch(API_BASE + "/public-chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "syntexa-large",
      messages: history,
      max_tokens: 1024,
    }),
    signal,
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro no modo gratuito: " + txt);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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
          if (data.content) {
            full += data.content;
            if (onChunk) onChunk(data.content);
          }
        } catch (_) {}
      }
    }
  }
  return full || "Nenhuma resposta retornada.";
}

export async function publicChatWithMedia(history, files) {
  const form = new FormData();
  form.append(
    "payload",
    JSON.stringify({
      model: "vereda-small-echo",
      messages: history,
      max_tokens: 1024,
    })
  );
  for (const file of files) {
    form.append("files", file);
  }
  const resp = await fetch(API_BASE + "/public-chat", {
    method: "POST",
    body: form,
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro no modo gratuito com mídia: " + txt);
  }
  const data = await resp.json();
  return data?.choices?.[0]?.message?.content ?? "Nenhuma resposta retornada pelo backend.";
}

/**
 * Retorna o perfil do usuário logado (inclui subscription_plan para limites da IA).
 */
export async function getProfile(token) {
  if (!token) return null;
  const resp = await fetch(API_BASE + "/v1/auth/me", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return null;
  return resp.json();
}

export async function listChatSessions(token) {
  if (!token) return [];
  const resp = await fetch(API_BASE + "/v1/chat/sessions", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return [];
  return resp.json();
}

export async function getChatSessionMessages(sessionId, token) {
  if (!token) return [];
  const resp = await fetch(API_BASE + "/v1/chat/sessions/" + sessionId + "/messages", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) return [];
  return resp.json();
}

export async function createStripeCheckout(plan, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/payments/stripe/checkout", {
    method: "POST",
    headers,
    body: JSON.stringify({ plan }),
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro ao iniciar checkout: " + txt);
  }
  const data = await resp.json();
  return data?.url;
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
    const r2 = await fetch(API_BASE + "/v1/media/images/fetch-url", {
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
  const form = new FormData();
  form.append("prompt", prompt);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/media/images/generate", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    const msg = await readErrorMessage(resp, "Falha ao gerar imagem no provedor real.");
    throw new Error(msg);
  }
  const data = await resp.json();
  return mergeImageBase64FromWhitelistedUrl(data, token);
}

export async function generateVideo(prompt, token) {
  const form = new FormData();
  form.append("prompt", prompt);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/media/videos/generate", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    const msg = await readErrorMessage(resp, "Falha ao gerar video no provedor real.");
    throw new Error(msg);
  }
  return resp.json();
}

export async function generateMusic(prompt, token) {
  const form = new FormData();
  form.append("prompt", prompt);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/media/music/generate", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    const msg = await readErrorMessage(resp, "Falha ao gerar audio no provedor real.");
    throw new Error(msg);
  }
  return resp.json();
}

// ---------------------------------------------------------------------------
// Educação & Pesquisa
// ---------------------------------------------------------------------------

/** Tutor de IA para alunos — público. Suporta discipline, level, language, mode. */
export async function educationTutor(discipline, question, mode, history, level, language, feedback) {
  const resp = await fetch(API_BASE + "/v1/education/tutor", {
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
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro no tutor: " + txt); }
  return resp.json();
}

/** Tutor streaming para alunos — onChunk(text) chamado a cada fragmento. */
export async function educationTutorStream(discipline, question, mode, history, onChunk, signal, level, language, feedback) {
  const resp = await fetch(API_BASE + "/v1/education/tutor/stream", {
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
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro no tutor: " + txt);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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
  const resp = await fetch(API_BASE + "/v1/education/teacher/chat", {
    method: "POST",
    headers,
    body: JSON.stringify({ task, content, context: context || null, level: level || "avancado", language: language || "pt" }),
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro na ferramenta: " + txt); }
  return resp.json();
}

/** Ferramentas do professor em streaming. */
export async function teacherChatStream(token, task, content, context, level, language, onChunk, signal) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/education/teacher/chat/stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ task, content, context: context || null, level: level || "avancado", language: language || "pt" }),
    signal,
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error("Erro na ferramenta: " + txt);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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
  const resp = await fetch(API_BASE + "/v1/education/compute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ expression, compute_type: computeType || "auto", variable: variable || "x" }),
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro no cálculo: " + txt); }
  return resp.json();
}

/** Sandbox de código Python/JS — público. */
export async function educationCodeSandbox(code, language, timeout) {
  const resp = await fetch(API_BASE + "/v1/education/compute/code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language: language || "python", timeout: timeout || 10 }),
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro no sandbox: " + txt); }
  return resp.json();
}

/** Ferramenta de pesquisa científica para professores — requer token. */
export async function teacherResearch(token, task, content, extra, language) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/education/teacher/research", {
    method: "POST",
    headers,
    body: JSON.stringify({ task: task || "analisar", content, extra: extra || null, language: language || "pt" }),
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro na pesquisa: " + txt); }
  return resp.json();
}

/** Ferramenta de pesquisa em streaming — requer token. */
export async function teacherResearchStream(token, task, content, extra, language, onChunk, signal) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/education/teacher/research/stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ task: task || "analisar", content, extra: extra || null, language: language || "pt" }),
    signal,
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro na pesquisa: " + txt); }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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
  const resp = await fetch(API_BASE + "/v1/education/gov/stats", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!resp.ok) throw new Error("Acesso negado ou erro ao buscar estatísticas");
  return resp.json();
}

/** Gera relatório educacional via IA — requer token de admin. */
export async function govGenerateReport(token, type, period, region) {
  const resp = await fetch(API_BASE + "/v1/education/gov/report", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
    body: JSON.stringify({ type: type || "geral", period: period || "mensal", region: region || "nacional" }),
  });
  if (!resp.ok) throw new Error("Erro ao gerar relatório");
  return resp.json();
}

/** Previsão educacional com IA — requer token de admin. */
export async function govPredict(token, scenario, context) {
  const resp = await fetch(API_BASE + "/v1/education/gov/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
    body: JSON.stringify({ scenario, context: context || null }),
  });
  if (!resp.ok) throw new Error("Erro na previsão");
  return resp.json();
}

/** Geração de política pública — requer token de admin. */
export async function govPolicy(token, challenge, region, budget) {
  const resp = await fetch(API_BASE + "/v1/education/gov/policy", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
    body: JSON.stringify({ challenge, region: region || null, budget: budget || null }),
  });
  if (!resp.ok) throw new Error("Erro ao gerar política");
  return resp.json();
}

/** Corrige redação no formato ENEM (5 competências, 0-1000) — anônimo. */
export async function gradeEnemEssay(essay, theme, language) {
  const resp = await fetch(API_BASE + "/v1/education/essay/grade", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ essay, theme: theme || null, language: language || "pt" }),
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro na correção: " + txt); }
  return resp.json();
}

/** Correção de redação ENEM em streaming — anônimo. */
export async function gradeEnemEssayStream(essay, theme, language, onChunk, signal) {
  const resp = await fetch(API_BASE + "/v1/education/essay/grade/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ essay, theme: theme || null, language: language || "pt" }),
    signal,
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro na correção: " + txt); }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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
  const resp = await fetch(API_BASE + "/v1/education/concursos/tutor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exam: exam || "enem", subject: subject || "geral", question, level: level || "avancado", language: language || "pt", history: history || [] }),
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro no tutor: " + txt); }
  return resp.json();
}

/** Tutor de concursos em streaming — anônimo. */
export async function concursosTutorStream(exam, subject, question, level, language, history, onChunk, signal) {
  const resp = await fetch(API_BASE + "/v1/education/concursos/tutor/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exam: exam || "enem", subject: subject || "geral", question, level: level || "avancado", language: language || "pt", history: history || [] }),
    signal,
  });
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro no tutor: " + txt); }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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
  const resp = await fetch(API_BASE + "/v1/education/privacy");
  if (!resp.ok) return null;
  return resp.json();
}

/** Tutor científico especializado — público, anônimo. */
export async function educationScience(area, question, level, language, history) {
  const resp = await fetch(API_BASE + "/v1/education/science", {
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
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro na consulta científica: " + txt); }
  return resp.json();
}

/** Tutor científico em streaming — público, anônimo. */
export async function educationScienceStream(area, question, level, language, history, onChunk, signal) {
  const resp = await fetch(API_BASE + "/v1/education/science/stream", {
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
  if (!resp.ok) { const txt = await resp.text(); throw new Error("Erro na consulta: " + txt); }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
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

/** Voz (TTS) em PT-BR via backend (edge-tts). Requer login. */
export async function generateSpeech(text, token, voice) {
  const form = new FormData();
  form.append("text", text);
  if (voice) form.append("voice", voice);
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  const resp = await fetch(API_BASE + "/v1/media/tts/generate", {
    method: "POST",
    headers,
    body: form,
  });
  if (!resp.ok) {
    const msg = await readErrorMessage(resp, "Falha ao sintetizar voz.");
    throw new Error(msg);
  }
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
  const resp = await fetch(API_BASE + "/v1/institutional/clients" + qs, { headers: _adminHeaders() });
  if (!resp.ok) { const msg = await readErrorMessage(resp, "Erro ao listar clientes."); throw new Error(msg); }
  return resp.json();
}

export async function institutionalCreateClient(data) {
  const resp = await fetch(API_BASE + "/v1/institutional/clients", {
    method: "POST",
    headers: _adminHeaders(),
    body: JSON.stringify(data),
  });
  if (!resp.ok) { const msg = await readErrorMessage(resp, "Erro ao criar cliente."); throw new Error(msg); }
  return resp.json();
}

export async function institutionalUpdateClient(id, data) {
  const resp = await fetch(API_BASE + "/v1/institutional/clients/" + id, {
    method: "PATCH",
    headers: _adminHeaders(),
    body: JSON.stringify(data),
  });
  if (!resp.ok) { const msg = await readErrorMessage(resp, "Erro ao atualizar cliente."); throw new Error(msg); }
  return resp.json();
}

export async function institutionalDeactivateClient(id) {
  const resp = await fetch(API_BASE + "/v1/institutional/clients/" + id, {
    method: "DELETE",
    headers: _adminHeaders(),
  });
  if (!resp.ok) { const msg = await readErrorMessage(resp, "Erro ao desativar cliente."); throw new Error(msg); }
  return { ok: true };
}

export async function institutionalRenewClient(id, expiresDays = 365) {
  const resp = await fetch(
    API_BASE + "/v1/institutional/clients/" + id + "/renew?expires_days=" + expiresDays,
    { method: "POST", headers: _adminHeaders() }
  );
  if (!resp.ok) { const msg = await readErrorMessage(resp, "Erro ao renovar licença."); throw new Error(msg); }
  return resp.json();
}

export async function institutionalRegenerateKey(id) {
  const resp = await fetch(
    API_BASE + "/v1/institutional/clients/" + id + "/regenerate-key",
    { method: "POST", headers: _adminHeaders() }
  );
  if (!resp.ok) { const msg = await readErrorMessage(resp, "Erro ao regenerar chave."); throw new Error(msg); }
  return resp.json();
}
