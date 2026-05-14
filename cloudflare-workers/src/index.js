/**
 * Syntexa Gateway Worker — Cloudflare Edge
 * Roteia:
 *   /v1/*, /public-chat*, /health, /docs, /openapi.json → Oracle Cloud backend
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
    // AWS EC2 = principal, Railway = fallback
    const awsBase = env.AWS_BASE_URL || "http://98.94.86.193:8000";
    const railwayBase = env.RAILWAY_BASE_URL || "https://syntexa-backend-production.up.railway.app";
    const backendBase = awsBase || railwayBase;
    var frontendBase = "https://production.syntexa-frontend.pages.dev";
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    const incomingUrl = new URL(request.url);
    const pathname = incomingUrl.pathname;

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

    if (isApiRequest(pathname)) {
      if (!backendBase) {
        return new Response("BACKEND_BASE_URL não configurada.", { status: 500 });
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

      let backendResp;
      try {
        backendResp = await fetch(targetUrl.toString(), init);
      } catch (err) {
        return new Response(JSON.stringify({status:"error",detail:"backend unreachable"}), {
          status: 503,
          headers: {"Content-Type":"application/json", ...corsHeaders(origin), ...securityHeaders()},
        });
      }
      const respHeaders = new Headers(backendResp.headers);
      Object.entries(corsHeaders(origin)).forEach(([k, v]) =>
        respHeaders.set(k, v),
      );
      Object.entries(securityHeaders()).forEach(([k, v]) => respHeaders.set(k, v));
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
      cf: { cacheTtl: 0 },
    };
    init.headers.delete("host");
    init.headers.set("Cache-Control", "no-cache");

    const pagesResp = await fetch(targetUrl.toString(), init);
    const pageHeaders = new Headers(pagesResp.headers);
    if (!pathname.match(/\.(js|css|mjs|woff2?|png|jpg|jpeg|webp|svg|ico|map)$/i)) {
      pageHeaders.set("Cache-Control", "no-store, no-cache, must-revalidate");
      pageHeaders.set("Pragma", "no-cache");
      pageHeaders.set("Expires", "0");
    } else {
      pageHeaders.set("Cache-Control", "public, max-age=86400, immutable");
    }
    return new Response(pagesResp.body, {
      status: pagesResp.status,
      headers: pageHeaders,
    });
  },
};
