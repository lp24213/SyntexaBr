/**
 * SYNTEXA — Next.js Middleware
 * ==============================
 * Roteamento, CORS para APIs, e headers de cache para RSC/streaming.
 */
import { NextResponse } from "next/server";

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|icon.svg|LOGOTIPO.png|manifest.webmanifest).*)",
  ],
};

const SUPPORTED_LOCALES = ["pt-BR", "en-US", "es-ES", "zh-CN"];
const DEFAULT_LOCALE = "pt-BR";
const LOCALE_COOKIE = "syntexa_locale";

function getLocaleFromCookie(request) {
  const cookie = request.cookies.get(LOCALE_COOKIE);
  if (cookie && SUPPORTED_LOCALES.includes(cookie.value)) {
    return cookie.value;
  }
  return null;
}

function getLocaleFromBrowser(request) {
  const acceptLang = request.headers.get("accept-language") || "";
  const browserLocale = acceptLang.split(",")[0].split("-")[0].toLowerCase();
  if (browserLocale === "en") return "en-US";
  if (browserLocale === "es") return "es-ES";
  if (browserLocale === "zh") return "zh-CN";
  return DEFAULT_LOCALE;
}

export function middleware(request) {
  const { pathname, search } = request.nextUrl;
  
  // ── i18n routing: /i18n/locale/page ───────────────────────
  const pathnameWithoutLocale = pathname.replace(/^\/i18n\/[^\/]+/, "") || "/";
  const localeMatch = pathname.match(/^\/i18n\/([^\/]+)/);
  const currentLocale = localeMatch ? localeMatch[1] : null;
  
  // Determinar o locale correto com PRIORIDADE:
  // 1. Cookie salvo (escolha manual do usuário)
  // 2. Locale do navegador (detecção automática)
  // 3. Padrão (pt-BR)
  const savedLocale = getLocaleFromCookie(request);
  const browserLocale = getLocaleFromBrowser(request);
  const targetLocale = savedLocale || browserLocale;
  
  // Se não tem /i18n/locale na URL, redirecionar para o locale correto
  const isStaticFile = /\.[a-zA-Z0-9]+$/.test(pathname);
  if (!currentLocale && pathname !== "/" && !pathname.startsWith("/_next") && !pathname.startsWith("/api") && !isStaticFile) {
    const newUrl = new URL(request.url);
    newUrl.pathname = `/i18n/${targetLocale}${pathname}`;
    const response = NextResponse.redirect(newUrl);
    // Setar cookie se ainda não existir
    if (!savedLocale) {
      response.cookies.set(LOCALE_COOKIE, targetLocale, { 
        maxAge: 60 * 60 * 24 * 365, // 1 ano
        path: "/",
        sameSite: "lax"
      });
    }
    return response;
  }

  // Raiz redireciona para o locale correto
  if (pathname === "/") {
    const newUrl = new URL(request.url);
    newUrl.pathname = `/i18n/${targetLocale}/`;
    const response = NextResponse.redirect(newUrl);
    if (!savedLocale) {
      response.cookies.set(LOCALE_COOKIE, targetLocale, { 
        maxAge: 60 * 60 * 24 * 365,
        path: "/",
        sameSite: "lax"
      });
    }
    return response;
  }
  
  const response = NextResponse.next();

  // ── Security headers ───────────────────────────────
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  // Allow Cloudflare Turnstile iframe communication
  response.headers.set("Referrer-Policy", "origin-when-cross-origin");
  
  // Content Security Policy for Turnstile and trusted resources
  response.headers.set(
    "Content-Security-Policy",
    "frame-src 'self' https://challenges.cloudflare.com; " +
    "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com; " +
    "connect-src 'self' https://challenges.cloudflare.com https://*.syntexabr.com.br; " +
    "default-src 'self' https:;"
  );

  // ── CORS para API routes (espelha o Worker: apenas domínios Syntexa) ──
  const isApi = pathname.startsWith("/api") || pathname.startsWith("/public-chat");
  if (isApi) {
    const allowedOrigins = [
      "https://syntexabr.com.br",
      "https://www.syntexabr.com.br",
      "https://api.syntexabr.com.br",
      "https://production.syntexa-frontend.pages.dev",
    ];
    const reqOrigin = request.headers.get("origin") || "";
    const corsOrigin = allowedOrigins.includes(reqOrigin) ? reqOrigin : allowedOrigins[0];
    response.headers.set("Access-Control-Allow-Origin", corsOrigin);
    response.headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
    response.headers.set("Access-Control-Max-Age", "86400");
  }

  // ── RSC payload preservation ───────────────────────
  // Não cachear RSC payloads — sempre fresh
  if (pathname.includes("_rsc") || pathname.includes(".rsc")) {
    response.headers.set("Cache-Control", "no-store, must-revalidate");
  }

  // ── Streaming / SSE headers ──────────────────────
  if (pathname.includes("/stream")) {
    response.headers.set("Cache-Control", "no-cache, no-transform");
    response.headers.set("X-Accel-Buffering", "no");
  }

  return response;
}
