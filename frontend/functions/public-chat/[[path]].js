const BACKEND = "https://api.syntexabr.com.br";

// ✅ Public chat é mais permissivo (pode ser acessado de qualquer lugar)
// Mas ainda valida que é apenas para endpoints públicos
const ALLOWED_PUBLIC_ENDPOINTS = [
  "/public-chat",
  "/public-chat/stream",
  "/v1/public/chat",
  "/v1/public/models",
];

function isAllowedPublicEndpoint(pathname) {
  return ALLOWED_PUBLIC_ENDPOINTS.some(
    (p) => pathname === p || pathname.startsWith(p + "/")
  );
}

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const target = BACKEND + url.pathname + url.search;
  const req = context.request;
  const requestOrigin = req.headers.get("Origin") || "";

  // ✅ Validar que é endpoint público permitido
  if (!isAllowedPublicEndpoint(url.pathname)) {
    return new Response(JSON.stringify({ error: "Endpoint not allowed for public access" }), {
      status: 403,
      headers: { "Content-Type": "application/json" },
    });
  }

  // ✅ CORS Preflight
  if (req.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": requestOrigin || "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Accept",
        "Access-Control-Max-Age": "86400",
      },
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
  // ✅ Public endpoint: permitir CORS (mas com restrições)
  respHeaders.set("Access-Control-Allow-Origin", requestOrigin || "*");
  respHeaders.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  respHeaders.set("Cache-Control", "public, max-age=60"); // Cache para reduzir carga

  return new Response(resp.body, { status: resp.status, headers: respHeaders });
}
