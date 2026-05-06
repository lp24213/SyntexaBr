import { NextResponse } from "next/server";

const PROD_API_BASE = "https://api.syntexabr.com.br";

function resolveBase() {
  const cdn = process.env.NEXT_PUBLIC_DESKTOP_CDN_BASE;
  if (cdn && String(cdn).trim()) return String(cdn).replace(/\/$/, "");

  // Em dev, permite apontar para API local/remota via env (mesma convenção do frontend/lib/api.js).
  const isDev = process.env.NODE_ENV === "development";
  if (isDev && process.env.NEXT_PUBLIC_API_BASE && String(process.env.NEXT_PUBLIC_API_BASE).trim()) {
    const raw = String(process.env.NEXT_PUBLIC_API_BASE).trim().replace(/\/$/, "");
    const withScheme = raw.startsWith("http") ? raw : `https://${raw}`;
    return withScheme.replace(/\/$/, "");
  }

  return PROD_API_BASE;
}

function sanitizeFilename(filename) {
  const f = String(filename || "").trim();
  // Evita path traversal e nomes esquisitos (só letras/números/._-).
  if (!/^[A-Za-z0-9._-]+$/.test(f)) return "";
  // Evita ".env", ".gitignore" etc.
  if (f.startsWith(".")) return "";
  return f;
}

export function GET(_req, { params }) {
  const filename = sanitizeFilename(params?.filename);
  if (!filename) {
    return NextResponse.json({ detail: "Arquivo inválido." }, { status: 400 });
  }

  const base = resolveBase();
  const target = `${base}/v1/desktop/binary/${encodeURIComponent(filename)}`;
  // 307 preserva o método (GET) e funciona bem para downloads.
  return NextResponse.redirect(target, 307);
}

