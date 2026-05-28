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

export function middleware(request) {
  const { pathname, search } = request.nextUrl;
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
