/**
 * ============================================================
 * VEREDA / SYNTEXA — EDGE GATEWAY v3.0
 * Cloudflare Workers — Única Entrada Pública
 * ============================================================
 * Responsabilidades:
 *  • Zero Trust Edge Auth (JWT + HMAC)
 *  • WAF / Anti-DDoS / Bot Fight (via Cloudflare nativo)
 *  • Rate Limiting inteligente (KV + Durable Objects ready)
 *  • Smart Routing (AWS GPU → Local → Queue)
 *  • WebSocket Bridge
 *  • Streaming proxy (SSE)
 *  • Request Signing
 *  • Failover automático
 *  • Session Validation (KV)
 * ============================================================
 */

// ── CONFIGURAÇÃO DE ROTAS ─────────────────────────────────
const AI_PREFIXES = [
  "/v1/chat/completions",
  "/v1/embeddings",
  "/v1/vision",
  "/v1/voice/stt",
  "/v1/voice/tts",
  "/public-chat",
];

const API_PREFIXES = [
  "/v1/",
  "/health",
  "/docs",
  "/redoc",
  "/openapi.json",
  "/ws/",
];

const FRONTEND_CANONICAL_REDIRECTS = {
  "/chat": "/Q7n2mLx9A4r",
  "/login": "/B_4mhVUCNloA",
  "/cadastro": "/K9pT2vRa8mQd",
  "/register": "/K9pT2vRa8mQd",
  "/planos": "/B-I7hUkBMF0d",
  "/plans": "/B-I7hUkBMF0d",
  "/forgot-password": "/W3dLp2xQn8Zk",
  "/recuperar-senha": "/W3dLp2xQn8Zk",
  "/activate-signup": "/N8qVb4sRm2Yt",
  "/activate-reset": "/M6cKp1uXe9Ha",
  "/verify-email": "/V2nKx7pLa4Qm",
  "/config": "/C4hPt9nVa1Xe",
  "/perfil": "/P8yLm3qRs6Td",
  "/profile": "/P8yLm3qRs6Td",
  "/download": "/D5rZw7mQx2Lc",
  "/portal": "/J7pLs3mQd2Nx",
  "/admin": "/H9vKp3mLt8Qw",
  "/admin/institucional": "/X8cMv2aRp9Tq",
  "/admin/ia-soberana": "/R4nZx6qLp1Md",
};

// ── HELPERS ────────────────────────────────────────────────
function isAiRequest(pathname) {
  return AI_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

function isApiRequest(pathname) {
  return API_PREFIXES.some((p) => pathname === p || pathname.startsWith(p));
}

function isDownloadAssetPath(pathname) {
  if (!pathname.startsWith("/download/")) return false;
  const rest = pathname.slice("/download/".length);
  if (!rest || rest.includes("/")) return false;
  return /\.(exe|dmg|deb|apk|aab)$/i.test(rest) || /\.tar\.gz$/i.test(rest);
}

function isWebSocketUpgrade(request) {
  const upgrade = request.headers.get("Upgrade") || "";
  return upgrade.toLowerCase() === "websocket";
}

function corsHeaders(origin, env) {
  const allowed = env.FRONTEND_BASE_URL || "https://syntexabr.com.br";
  return {
    "Access-Control-Allow-Origin": origin && (origin === allowed || allowed === "*") ? origin : allowed,
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With, Accept, X-Vereda-Signature, X-Session-Id",
    "Access-Control-Max-Age": "86400",
  };
}

function securityHeaders() {
  return {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(self), camera=(self), payment=()",
    "X-XSS-Protection": "1; mode=block",
  };
}

// ── JWT EDGE VALIDATION (básico, sem verificação de assinatura crypto no edge)
// Para verificação completa, usar Workers Crypto API ou delegar ao Railway.
function extractBearer(request) {
  const h = request.headers.get("Authorization") || "";
  const m = h.match(/^Bearer\s+(.+)$/i);
  return m ? m[1] : null;
}

function parseJwtPayload(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch {
    return null;
  }
}

function isTokenExpired(payload) {
  if (!payload || !payload.exp) return true;
  return Math.floor(Date.now() / 1000) >= payload.exp;
}

// ── HMAC REQUEST SIGNING ───────────────────────────────────
async function verifyHmac(request, env, bodyClone) {
  const signature = request.headers.get("X-Vereda-Signature");
  if (!signature) return true; // opcional para rotas públicas
  if (!env.VEREDA_SECRET_KEY) return false;

  const method = request.method;
  const url = new URL(request.url);
  const path = url.pathname + url.search;
  const timestamp = request.headers.get("X-Vereda-Timestamp") || "";
  const toSign = `${method}:${path}:${timestamp}`;

  // Se houver body, incluir hash simplificado (em produção usar body raw)
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(env.VEREDA_SECRET_KEY), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sigBuf = await crypto.subtle.sign("HMAC", key, encoder.encode(toSign));
  const sigHex = Array.from(new Uint8Array(sigBuf)).map(b => b.toString(16).padStart(2, "0")).join("");
  return signature === sigHex;
}

// ── RATE LIMITING (KV-based simples) ───────────────────────
async function checkRateLimit(request, env) {
  if (!env.RATE_LIMIT_ENABLED) return { allowed: true };

  const clientId = request.headers.get("CF-Connecting-IP") || "unknown";
  const key = `rate:${clientId}`;
  const now = Math.floor(Date.now() / 1000);
  const window = parseInt(env.RATE_LIMIT_WINDOW || "60", 10);
  const maxReq = parseInt(env.RATE_LIMIT_MAX || "100", 10);

  // Se KV não disponível, permite passar (graceful degradation)
  if (!env.VEREDA_KV) return { allowed: true };

  try {
    const data = await env.VEREDA_KV.get(key, { type: "json" });
    const bucket = data || { count: 0, reset: now + window };

    if (now > bucket.reset) {
      bucket.count = 1;
      bucket.reset = now + window;
    } else {
      bucket.count += 1;
    }

    await env.VEREDA_KV.put(key, JSON.stringify(bucket), { expirationTtl: window });

    if (bucket.count > maxReq) {
      return { allowed: false, retryAfter: bucket.reset - now };
    }
    return { allowed: true };
  } catch {
    return { allowed: true };
  }
}

// ── SMART ROUTING ──────────────────────────────────────────
function selectBackend(pathname, env) {
  // IA pesada → AWS GPU Cluster (primário)
  if (isAiRequest(pathname)) {
    return {
      primary: env.AWS_BASE_URL,
      fallback: env.LOCAL_BASE_URL, // fallback para infra local
      type: "ai",
    };
  }
  // API geral → Railway Core
  return {
    primary: env.BACKEND_BASE_URL,
    fallback: null,
    type: "api",
  };
}

// ── PROXY REQUEST ──────────────────────────────────────────
async function proxyRequest(request, targetBase, origin, env) {
  if (!targetBase) {
    return new Response(JSON.stringify({ status: "error", detail: "backend not configured" }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...corsHeaders(origin, env), ...securityHeaders() },
    });
  }

  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(targetBase);
  targetUrl.pathname = incomingUrl.pathname;
  targetUrl.search = incomingUrl.search;

  const init = {
    method: request.method,
    headers: new Headers(request.headers),
    body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
    redirect: "manual",
  };

  // Headers de forwarding
  init.headers.delete("host");
  init.headers.delete("x-forwarded-proto");
  init.headers.set("X-Forwarded-For", request.headers.get("CF-Connecting-IP") || "unknown");
  init.headers.set("X-Vereda-Gateway", "cloudflare-edge");
  init.headers.set("X-Vereda-Request-Id", crypto.randomUUID());

  // Timeout configurável
  const timeoutMs = parseInt(env.PROXY_TIMEOUT_MS || "30000", 10);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let resp;
  try {
    resp = await fetch(targetUrl.toString(), { ...init, signal: controller.signal });
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") {
      return new Response(JSON.stringify({ status: "error", detail: "gateway timeout" }), {
        status: 504,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin, env), ...securityHeaders() },
      });
    }
    return new Response(JSON.stringify({ status: "error", detail: "backend unreachable" }), {
      status: 503,
      headers: { "Content-Type": "application/json", ...corsHeaders(origin, env), ...securityHeaders() },
    });
  }
  clearTimeout(timer);

  const respHeaders = new Headers(resp.headers);
  Object.entries(corsHeaders(origin, env)).forEach(([k, v]) => respHeaders.set(k, v));
  Object.entries(securityHeaders()).forEach(([k, v]) => respHeaders.set(k, v));

  // Cache control
  if (request.method === "GET" && incomingUrl.pathname.endsWith("/health")) {
    respHeaders.set("Cache-Control", "public, max-age=5");
  } else {
    respHeaders.set("Cache-Control", "no-store");
  }

  return new Response(resp.body, { status: resp.status, headers: respHeaders });
}

// ── MAIN HANDLER ───────────────────────────────────────────
export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const incomingUrl = new URL(request.url);
    const pathname = incomingUrl.pathname;

    // 1. CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin, env) });
    }

    // 2. Zero Trust: verificar se tráfego vem pelo Cloudflare (CF-Connecting-IP presente)
    if (env.REQUIRE_CLOUDFLARE === "true") {
      const cfIp = request.headers.get("CF-Connecting-IP");
      if (!cfIp) {
        return new Response(JSON.stringify({ detail: "Direct origin access denied." }), {
          status: 403,
          headers: { "Content-Type": "application/json", ...securityHeaders() },
        });
      }
    }

    // 3. Rate limiting
    const rate = await checkRateLimit(request, env);
    if (!rate.allowed) {
      return new Response(JSON.stringify({ detail: "Rate limit exceeded" }), {
        status: 429,
        headers: {
          "Content-Type": "application/json",
          "Retry-After": String(rate.retryAfter || 60),
          ...corsHeaders(origin, env),
          ...securityHeaders(),
        },
      });
    }

    // 4. JWT Edge Validation (para rotas protegidas)
    const isPublic = pathname.startsWith("/public-chat") || pathname.startsWith("/v1/public/");
    if (!isPublic && env.JWT_EDGE_VERIFY === "true") {
      const token = extractBearer(request);
      if (!token) {
        return new Response(JSON.stringify({ detail: "Authorization required" }), {
          status: 401,
          headers: { "Content-Type": "application/json", ...corsHeaders(origin, env), ...securityHeaders() },
        });
      }
      const payload = parseJwtPayload(token);
      if (!payload || isTokenExpired(payload)) {
        return new Response(JSON.stringify({ detail: "Invalid or expired token" }), {
          status: 401,
          headers: { "Content-Type": "application/json", ...corsHeaders(origin, env), ...securityHeaders() },
        });
      }
      // Forward user info para o backend
      request.headers.set("X-Vereda-User-Id", payload.sub || "");
      request.headers.set("X-Vereda-User-Role", payload.role || "");
    }

    // 5. HMAC verification (para webhooks / internal APIs)
    if (env.HMAC_VERIFY === "true" && pathname.startsWith("/v1/internal/")) {
      const hmacOk = await verifyHmac(request, env);
      if (!hmacOk) {
        return new Response(JSON.stringify({ detail: "Invalid signature" }), {
          status: 403,
          headers: { "Content-Type": "application/json", ...corsHeaders(origin, env), ...securityHeaders() },
        });
      }
    }

    // 6. WebSocket upgrade → Railway
    if (isWebSocketUpgrade(request) && pathname.startsWith("/ws/")) {
      const backendBase = env.BACKEND_BASE_URL;
      if (!backendBase) {
        return new Response("WS backend unavailable", { status: 502 });
      }
      const targetUrl = new URL(backendBase);
      targetUrl.pathname = pathname;
      targetUrl.search = incomingUrl.search;
      return fetch(targetUrl.toString(), request);
    }

    // 7. Download assets → servidos diretamente pelo Cloudflare Pages
    //    (ZIPs/tarballs ficam em `frontend/public/download/`). A API antiga
    //    em `api.syntexabr.com.br/v1/desktop/*` ficou indisponível, então
    //    o gateway não redireciona mais — cai direto para o block 9 (Pages).

    // 8. Public chat — PROIBIDO stub/resposta hardcoded (V38).
    // Sempre proxy para backend real; se indisponível, retorna erro técnico.
    if (pathname === "/public-chat" || pathname === "/public-chat/stream") {
      const backendBase = env.BACKEND_BASE_URL;
      if (!backendBase) {
        return new Response(JSON.stringify({
          status: "error",
          detail: "[Syntexa V38] Backend indisponível. Nenhum fallback textual permitido.",
        }), {
          status: 503,
          headers: {
            "Content-Type": "application/json",
            ...corsHeaders(origin, env),
            ...securityHeaders(),
          },
        });
      }
      return proxyRequest(request, backendBase, origin, env);
    }

    // 9. Smart Routing
    const routing = selectBackend(pathname, env);

    // 9a. API / AI requests
    if (isApiRequest(pathname) || isAiRequest(pathname)) {
      // Tenta primário
      let resp = await proxyRequest(request, routing.primary, origin, env);

      // Failover para fallback (se IA e houver fallback configurado)
      if (resp.status >= 500 && routing.type === "ai" && routing.fallback) {
        resp = await proxyRequest(request, routing.fallback, origin, env);
        resp.headers.set("X-Vereda-Failover", "local");
      }

      return resp;
    }

    // 9. Frontend → Cloudflare Pages (alias de produção)
    const frontendBase = env.FRONTEND_BASE_URL || "https://production.syntexa-frontend.pages.dev";
    const targetUrl = new URL(frontendBase);
    targetUrl.pathname = pathname;
    targetUrl.search = incomingUrl.search;

    const init = {
      method: request.method,
      headers: new Headers(request.headers),
      body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
      redirect: "manual",
      cf: { cacheTtl: 300 }, // Cache rápido para Pages (5 min)
    };
    init.headers.delete("host");
    init.headers.delete("CF-Connecting-IP"); // Remover headers que podem causar erro

    const pagesResp = await fetch(targetUrl.toString(), init);
    const pageHeaders = new Headers(pagesResp.headers);
    
    // Assets estáticos: cache longo
    if (pathname.match(/\.(js|css|mjs|woff2?|png|jpg|jpeg|webp|svg|ico|map)$/i)) {
      pageHeaders.set("Cache-Control", "public, max-age=31536000, immutable");
    } 
    // HTML + API: sem cache
    else {
      pageHeaders.set("Cache-Control", "no-store, no-cache, must-revalidate");
      pageHeaders.set("Pragma", "no-cache");
      pageHeaders.set("Expires", "0");
    }
    
    // Adicionar headers CORS
    Object.entries(corsHeaders(origin, env)).forEach(([k, v]) => pageHeaders.set(k, v));
    Object.entries(securityHeaders()).forEach(([k, v]) => pageHeaders.set(k, v));
    
    return new Response(pagesResp.body, { status: pagesResp.status, headers: pageHeaders });
  },
};
