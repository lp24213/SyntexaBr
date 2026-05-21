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
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");

  // ── CORS para API routes (permite cross-origin requests) ──
  const isApi = pathname.startsWith("/api") || pathname.startsWith("/public-chat");
  if (isApi) {
    response.headers.set("Access-Control-Allow-Origin", "*");
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
