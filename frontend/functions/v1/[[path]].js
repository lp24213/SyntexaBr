const BACKEND = "https://api.syntexabr.com.br";

// ✅ WHITELIST de domínios permitidos (HTTPS only)
const ALLOWED_ORIGINS = [
  "https://syntexabr.com.br",
  "https://www.syntexabr.com.br",
  "https://app.syntexabr.com.br",
  "https://production.syntexa-frontend.pages.dev",
];

function getCorsHeaders(requestOrigin) {
  if (!ALLOWED_ORIGINS.includes(requestOrigin)) {
    return {}; // Sem CORS headers se origem não permitida
  }
  return {
    "Access-Control-Allow-Origin": requestOrigin,
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With, Accept",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Max-Age": "86400",
  };
}

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const target = BACKEND + url.pathname + url.search;
  const req = context.request;
  const requestOrigin = req.headers.get("Origin") || req.headers.get("origin") || "";

  // CORS Preflight
  if (req.method === "OPTIONS") {
    const corsHeaders = getCorsHeaders(requestOrigin);
    if (Object.keys(corsHeaders).length === 0) {
      return new Response(null, { status: 403, headers: { "Content-Type": "text/plain" } });
    }
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  // Reject non-whitelisted origins for actual requests (except direct API calls)
  const corsHeaders = getCorsHeaders(requestOrigin);
  if (requestOrigin && !ALLOWED_ORIGINS.includes(requestOrigin)) {
    return new Response(JSON.stringify({ error: "Origin not allowed" }), {
      status: 403,
      headers: { "Content-Type": "application/json" },
    });
  }

  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("origin");

  const resp = await fetch(target, {
    method: req.method,
    headers,
    body: req.method !== "GET" && req.method !== "HEAD" ? req.body : undefined,
    redirect: "manual",
  });

  const respHeaders = new Headers(resp.headers);
  Object.entries(corsHeaders).forEach(([key, value]) => {
    respHeaders.set(key, value);
  });

  return new Response(resp.body, { status: resp.status, headers: respHeaders });
}
