const DEFAULT_LOCALE = "pt-BR";

const DICT = {
  "pt-BR": {
    chat: "Chat",
    plans: "Planos",
    portal: "Portal",
    profile: "Perfil",
    settings: "Configurações",
    logout: "Sair",
    login: "Login",
    conversations: "Conversas",
    new: "Nova",
    general: "Geral",
    specializations: "Especializações",
    tools: "Ferramentas",
    account: "Conta",
    authenticatedAccount: "Conta autenticada na Syntexa",
    publicMode: "Modo público gratuito",
    historyHint: "Histórico aparecerá aqui após você usar o chat autenticado.",
    newConversation: "Nova conversa",
    rightsReserved: "Todos os direitos reservados.",
    educationResearch: "Educação & Pesquisa",
    labs: "Laboratórios",
    scienceTech: "Ciência & Tecnologia",
    competitions: "Concursos",
    teacherArea: "Área do Professor",
    fullAi: "IA Completa",
    bankFinance: "Banco & Finanças",
    agro: "Agro",
    taxes: "Impostos / Receita",
    whatsappSales: "Vendas WhatsApp",
    offlineSystem: "Sistema Offline",
    apiTokens: "API Tokens",
  },
  "en-US": {
    chat: "Chat",
    plans: "Plans",
    portal: "Portal",
    profile: "Profile",
    settings: "Settings",
    logout: "Log out",
    login: "Login",
    conversations: "Conversations",
    new: "New",
    general: "General",
    specializations: "Specializations",
    tools: "Tools",
    account: "Account",
    authenticatedAccount: "Authenticated Syntexa account",
    publicMode: "Free public mode",
    historyHint: "History will appear here after you use authenticated chat.",
    newConversation: "New conversation",
    rightsReserved: "All rights reserved.",
    educationResearch: "Education & Research",
    labs: "Labs",
    scienceTech: "Science & Technology",
    competitions: "Competitions",
    teacherArea: "Teacher Area",
    fullAi: "Full AI",
    bankFinance: "Banking & Finance",
    agro: "Agro",
    taxes: "Taxes / Revenue",
    whatsappSales: "WhatsApp Sales",
    offlineSystem: "Offline System",
    apiTokens: "API Tokens",
  },
};

export function getClientLocale() {
  try {
    if (typeof navigator !== "undefined" && navigator.language) {
      return String(navigator.language);
    }
  } catch {}
  return DEFAULT_LOCALE;
}

export function normalizeLocale(locale) {
  var raw = String(locale || "").toLowerCase();
  if (raw.startsWith("en")) return "en-US";
  return "pt-BR";
}

export function t(key, locale) {
  var loc = normalizeLocale(locale || getClientLocale());
  var table = DICT[loc] || DICT[DEFAULT_LOCALE];
  return table[key] || DICT[DEFAULT_LOCALE][key] || key;
}

export function formatDateTime(value, locale, options) {
  var loc = normalizeLocale(locale || getClientLocale());
  try {
    return new Date(value).toLocaleString(loc, options || {});
  } catch {
    return "";
  }
}

export function formatNumber(value, locale) {
  var loc = normalizeLocale(locale || getClientLocale());
  try {
    return new Intl.NumberFormat(loc).format(Number(value || 0));
  } catch {
    return String(value || 0);
  }
}
