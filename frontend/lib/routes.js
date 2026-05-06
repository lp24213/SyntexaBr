const ROUTE_MAP = {
  chat: ["/chat", "/Q7n2mLx9A4r"],
  login: ["/login", "/B_4mhVUCNloA"],
  register: ["/register", "/K9pT2vRa8mQd"],
  plans: ["/plans", "/B-I7hUkBMF0d"],
  "forgot-password": ["/forgot-password", "/W3dLp2xQn8Zk"],
  "activate-signup": ["/activate-signup", "/N8qVb4sRm2Yt"],
  "activate-reset": ["/activate-reset", "/M6cKp1uXe9Ha"],
  download: ["/download", "/D5rZw7mQx2Lc"],
  config: ["/config", "/C4hPt9nVa1Xe"],
  profile: ["/profile", "/P8yLm3qRs6Td"],
  "verify-email": ["/verify-email", "/V2nKx7pLa4Qm"],
  educacao: "/educacao",
  "educacao-aluno": "/educacao/aluno",
  "educacao-professor": "/educacao/professor",
  "educacao-governo": "/educacao/governo",
  "educacao-laboratorios": "/educacao/laboratorios",
  "educacao-ciencia": "/educacao/ciencia",
  "educacao-concursos": "/educacao/concursos",
  portal: ["/portal", "/J7pLs3mQd2Nx"],
  "admin-institucional": ["/admin/institucional", "/X8cMv2aRp9Tq"],
  "admin-ia-soberana": ["/admin/ia-soberana", "/R4nZx6qLp1Md"],
  "admin-integrations": "/admin/integrations",
  "admin-security-hub": "/admin/security-hub",
  "admin-pentest-admin": "/admin/pentest-admin",
  "admin-mobile-release": "/admin/mobile-release",
  admin: ["/admin", "/H9vKp3mLt8Qw"],
};

function toBase64Url(str) {
  if (typeof window === "undefined") {
    return Buffer.from(str, "utf-8").toString("base64url");
  }
  const b64 = btoa(unescape(encodeURIComponent(str)));
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function fromBase64Url(token) {
  const norm = String(token || "").replace(/-/g, "+").replace(/_/g, "/");
  const pad = norm.length % 4 === 0 ? "" : "=".repeat(4 - (norm.length % 4));
  if (typeof window === "undefined") {
    return Buffer.from(norm + pad, "base64").toString("utf-8");
  }
  return decodeURIComponent(escape(atob(norm + pad)));
}

function normalizeKey(path) {
  return (path || "chat").replace(/^\/+|\/+$/g, "");
}

function normalizePath(path) {
  const clean = normalizeKey(path);
  const mapped = ROUTE_MAP[clean] || ROUTE_MAP[clean.replace(/\//g, "-")] || "/" + clean;
  if (Array.isArray(mapped) && mapped.length) {
    if (mapped.length === 1) return mapped[0];
    // Alterna entre rota limpa e ofuscada para não fixar um slug único.
    const idx = Math.floor(Math.random() * mapped.length);
    return mapped[idx];
  }
  return mapped;
}

function readCookie(name) {
  if (typeof document === "undefined") return "";
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : "";
}

function visitorId() {
  if (typeof window === "undefined") return "srv";
  const cookieId = readCookie("sx_vid");
  if (cookieId) return cookieId;
  const lsKey = "syntexa_vid";
  let id = "";
  try {
    id = localStorage.getItem(lsKey) || "";
  } catch {}
  if (!id) {
    id = (window.crypto && crypto.randomUUID && crypto.randomUUID()) || String(Date.now());
    try {
      localStorage.setItem(lsKey, id);
    } catch {}
  }
  try {
    document.cookie = "sx_vid=" + encodeURIComponent(id) + "; path=/; max-age=31536000; samesite=lax";
  } catch {}
  return id;
}

function randomNonce() {
  if (typeof window !== "undefined" && window.crypto && crypto.getRandomValues) {
    const bytes = new Uint8Array(8);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function encodeToken(path, vid) {
  const p = normalizePath(path);
  const raw = JSON.stringify({
    p,
    v: String(vid || visitorId()),
    t: Math.floor(Date.now() / 1000),
    n: randomNonce(),
  });
  return toBase64Url(raw);
}

export function encryptedPath(path) {
  const p = normalizePath(path);
  const id = visitorId();
  // Usa o token inteiro (com nonce) para evitar o prefixo fixo no `k=`.
  const sig = encodeToken(p, id);
  return p + (p.includes("?") ? "&" : "?") + "k=" + sig;
}

export function encodePath(path) {
  return encryptedPath(path);
}

export function decodePath(token) {
  try {
    const decoded = fromBase64Url((token || "").replace(/^\/+|\/+$/g, ""));
    const data = JSON.parse(decoded);
    const p = String(data && data.p ? data.p : "");
    return p.startsWith("/") ? p : null;
  } catch {
    return null;
  }
}

export const ENCRYPTED_ROUTE_PATHS = Object.keys(ROUTE_MAP);

export function getEncryptedRouteTokens() {
  const id = visitorId();
  return ENCRYPTED_ROUTE_PATHS.map((k) => encodeToken(ROUTE_MAP[k], id));
}
