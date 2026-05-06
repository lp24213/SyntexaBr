/**
 * Gateway Worker — roteia:
 *   /v1/*, /public-chat*, /health, /docs, /openapi.json → BACKEND_BASE_URL (ex.: api.syntexabr.com.br na Azure)
 *   tudo o mais → Cloudflare Pages (frontend estático)
 */

const API_PREFIXES = [
  "/v1/",
  "/public-chat",
  "/health",
  "/docs",
  "/redoc",
  "/openapi.json",
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

function isApiRequest(pathname) {
  return API_PREFIXES.some((p) => pathname === p || pathname.startsWith(p));
}

/** Ficheiros /download/*.exe (etc.) não existem no Pages — enviar para a API. */
function isDownloadAssetPath(pathname) {
  if (!pathname.startsWith("/download/")) return false;
  const rest = pathname.slice("/download/".length);
  if (!rest || rest.includes("/")) return false;
  return (
    /\.(exe|dmg|deb|apk|aab)$/i.test(rest) || /\.tar\.gz$/i.test(rest)
  );
}

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin || "https://syntexabr.com.br",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers":
      "Authorization, Content-Type, X-Requested-With, Accept",
    "Access-Control-Max-Age": "86400",
  };
}

/** Headers de segurança na borda (complementam o FastAPI). Rate limiting: use WAF / Rules no dashboard CF. */
function securityHeaders() {
  return {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
  };
}

export default {
  async fetch(request, env) {
    const backendBase = env.BACKEND_BASE_URL;
    const frontendBase =
      env.FRONTEND_BASE_URL || "https://syntexa-frontend.pages.dev";
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    const incomingUrl = new URL(request.url);
    const pathname = incomingUrl.pathname;

    // Forca rota canônica ofuscada no frontend.
    if (request.method === "GET" || request.method === "HEAD") {
      const target = FRONTEND_CANONICAL_REDIRECTS[pathname];
      if (target) {
        const to = new URL(request.url);
        to.pathname = target;
        return Response.redirect(to.toString(), 302);
      }
    }

    // Pacotes /download/* → API /v1/desktop/binary/* (FileResponse na VM).
    if (
      (request.method === "GET" || request.method === "HEAD") &&
      backendBase &&
      isDownloadAssetPath(pathname)
    ) {
      const name = pathname.slice("/download/".length);
      const base = backendBase.replace(/\/$/, "");
      const loc = `${base}/v1/desktop/binary/${encodeURIComponent(name)}`;
      return Response.redirect(loc, 302);
    }

    // Rotas de API → backend (Azure / FastAPI)
    if (isApiRequest(pathname)) {
      if (!backendBase) {
        return new Response("BACKEND_BASE_URL não configurada.", {
          status: 500,
        });
      }

      const targetUrl = new URL(backendBase);
      targetUrl.pathname = pathname;
      targetUrl.search = incomingUrl.search;

      const init = {
        method: request.method,
        headers: new Headers(request.headers),
        body:
          request.method === "GET" || request.method === "HEAD"
            ? undefined
            : request.body,
        redirect: "manual",
      };
      init.headers.delete("host");
      init.headers.delete("x-forwarded-proto");
      init.headers.delete("x-forwarded-for");

      const backendResp = await fetch(targetUrl.toString(), init);
      const respHeaders = new Headers(backendResp.headers);
      Object.entries(corsHeaders(origin)).forEach(([k, v]) =>
        respHeaders.set(k, v),
      );
      Object.entries(securityHeaders()).forEach(([k, v]) => respHeaders.set(k, v));
      // API dinâmica: não cachear no edge. Health pode cachear alguns segundos.
      if (request.method === "GET" && pathname.endsWith("/health")) {
        respHeaders.set("Cache-Control", "public, max-age=5");
      } else {
        respHeaders.set("Cache-Control", "no-store");
      }

      return new Response(backendResp.body, {
        status: backendResp.status,
        headers: respHeaders,
      });
    }

    // Todo o resto → Cloudflare Pages (frontend)
    const targetUrl = new URL(frontendBase);
    targetUrl.pathname = pathname;
    targetUrl.search = incomingUrl.search;

    const init = {
      method: request.method,
      headers: new Headers(request.headers),
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : request.body,
      redirect: "manual",
    };
    init.headers.delete("host");

    const pagesResp = await fetch(targetUrl.toString(), init);
    const pageHeaders = new Headers(pagesResp.headers);
    // Assets estáticos: cache agressivo na borda (menos carga no origin)
    if (
      request.method === "GET" &&
      pathname.match(/\.(js|css|mjs|woff2?|png|jpg|jpeg|webp|svg|ico|map)$/i)
    ) {
      pageHeaders.set("Cache-Control", "public, max-age=86400, immutable");
    }
    return new Response(pagesResp.body, {
      status: pagesResp.status,
      headers: pageHeaders,
    });
  },
};
