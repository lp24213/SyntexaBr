/**
 * Syntexa Gateway Worker — Cloudflare Edge
 * Roteia:
 *   /v1/*, /public-chat*, /health, /docs, /openapi.json → Oracle Cloud backend
 *   tudo o mais → Cloudflare Pages (frontend estático)
 */

const API_PREFIXES = [
  "/v1/",
  "/api/",
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
    /\.(exe|msi|dmg|deb|apk|aab|AppImage)$/i.test(rest) || /\.tar\.gz$/i.test(rest)
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
    "Permissions-Policy": "microphone=(self), camera=(self), geolocation=(self), payment=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
  };
}

export default {
  async fetch(request, env) {
    // Railway = principal via Workers; AWS = fallback direto se Railway falhar
    const awsBase = env.AWS_BASE_URL || "http://98.94.86.193:8000";
    const railwayBase = env.RAILWAY_BASE_URL || "https://syntexa-backend-production.up.railway.app";
    // Cloudflare Workers bloqueia fetch a IPs públicos directos (error 1003).
    // Railway é HTTPS com domínio — sempre acessível pelo Worker.
    const backendBase = railwayBase || awsBase;
    var frontendBase = "https://syntexa-frontend.pages.dev";
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    const incomingUrl = new URL(request.url);
    const pathname = incomingUrl.pathname;

    if (
      (request.method === "GET" || request.method === "HEAD") &&
      isDownloadAssetPath(pathname)
    ) {
      const name = pathname.slice("/download/".length);
      // AWS serve o ficheiro directamente via HTTP — o Worker faz proxy HTTPS
      const awsDownloadBase = env.AWS_DOWNLOAD_URL || "http://3.90.244.89/downloads";
      const fileUrl = `${awsDownloadBase}/${encodeURIComponent(name)}`;
      let upstream;
      try {
        upstream = await fetch(fileUrl, { method: request.method });
      } catch (err) {
        return new Response("Download temporariamente indisponível.", { status: 503 });
      }
      if (!upstream.ok) {
        return new Response("Ficheiro não encontrado.", { status: 404 });
      }
      const ext = name.split(".").pop().toLowerCase();
      const mimeMap = {
        exe: "application/vnd.microsoft.portable-executable",
        msi: "application/x-msi",
        dmg: "application/x-apple-diskimage",
        apk: "application/vnd.android.package-archive",
        gz: "application/gzip",
        deb: "application/vnd.debian.binary-package",
      };
      const mime = mimeMap[ext] || "application/octet-stream";
      const headers = new Headers();
      headers.set("Content-Type", mime);
      headers.set("Content-Disposition", `attachment; filename="${name}"; filename*=UTF-8''${encodeURIComponent(name)}`);
      headers.set("X-Content-Type-Options", "nosniff");
      headers.set("Content-Transfer-Encoding", "binary");
      headers.set("Accept-Ranges", "bytes");
      headers.set("Cache-Control", "public, max-age=3600, immutable");
      if (upstream.headers.get("Content-Length")) {
        headers.set("Content-Length", upstream.headers.get("Content-Length"));
      }
      return new Response(request.method === "HEAD" ? null : upstream.body, {
        status: 200,
        headers,
      });
    }

    if (isApiRequest(pathname)) {
      if (!backendBase) {
        return new Response("BACKEND_BASE_URL não configurada.", { status: 500 });
      }

      const targetUrl = new URL(backendBase);
      targetUrl.pathname = pathname;
      targetUrl.search = incomingUrl.search;

      let body = undefined;
      if (request.method !== "GET" && request.method !== "HEAD") {
        body = await request.arrayBuffer();
      }

      const init = {
        method: request.method,
        headers: new Headers(request.headers),
        body: body,
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

      // SSE STREAMING — NÃO BUFFERIZAR
      const contentType = respHeaders.get("Content-Type") || "";
      if (contentType.includes("text/event-stream") || pathname.includes("/stream")) {
        respHeaders.set("Content-Type", "text/event-stream; charset=utf-8");
        respHeaders.set("Cache-Control", "no-cache");
        respHeaders.set("Connection", "keep-alive");
        respHeaders.set("X-Accel-Buffering", "no");
        respHeaders.delete("Content-Length");
      }

      return new Response(backendResp.body, {
        status: backendResp.status,
        headers: respHeaders,
      });
    }

    const targetUrl = new URL(frontendBase);
    targetUrl.pathname = pathname;
    targetUrl.search = incomingUrl.search;

    let pageBody = undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {
      pageBody = await request.arrayBuffer();
    }

    const init = {
      method: request.method,
      headers: new Headers(request.headers),
      body: pageBody,
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
    Object.entries(securityHeaders()).forEach(([k, v]) => pageHeaders.set(k, v));
    return new Response(pagesResp.body, {
      status: pagesResp.status,
      headers: pageHeaders,
    });
  },
};
