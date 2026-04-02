const ROUTE_MAP = {
  chat: "/chat",
  login: "/login",
  register: "/cadastro",
  plans: "/planos",
  "forgot-password": "/recuperar-senha",
  "activate-signup": "/activate-signup",
  "activate-reset": "/activate-reset",
  download: "/download",
  config: "/config",
  profile: "/perfil",
  "verify-email": "/verify-email",
  educacao: "/educacao",
  "educacao-aluno": "/educacao/aluno",
  "educacao-professor": "/educacao/professor",
  "educacao-governo": "/educacao/governo",
  "educacao-laboratorios": "/educacao/laboratorios",
  "educacao-ciencia": "/educacao/ciencia",
  "educacao-concursos": "/educacao/concursos",
  portal: "/portal",
  "admin-institucional": "/admin/institucional",
  admin: "/admin",
};

export function encryptedPath(path) {
  const clean = (path || "chat").replace(/^\/+|\/+$/g, "");
  return ROUTE_MAP[clean] || "/" + clean;
}

export function encodePath(path) {
  const clean = (path || "chat").replace(/^\/+|\/+$/g, "");
  return clean;
}

export function decodePath(token) {
  const clean = (token || "").replace(/^\/+|\/+$/g, "");
  if (!clean) return null;
  return clean;
}

export const ENCRYPTED_ROUTE_PATHS = Object.keys(ROUTE_MAP);

export function getEncryptedRouteTokens() {
  return [];
}
