/**
 * sanitizeOutput — normalização global de texto vindo da IA ou de APIs.
 * Durante SSE use sanitizeStreamChunk (não colapsa espaços nem mojibake por chunk).
 */

function badEncodingScore(text) {
  var t = String(text || "");
  var bad = (t.match(/Ã|Â|â\uFFFD|Ð|þ/g) || []).length;
  var weird = 0;
  for (var i = 0; i < t.length; i++) {
    var o = t.charCodeAt(i);
    if (o < 9 || (o > 13 && o < 32)) weird++;
  }
  return bad * 4 + weird;
}

function latin1ToUtf8(raw) {
  if (!raw || /[^\u0000-\u00ff]/.test(raw)) return raw;
  try {
    var bytes = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i) & 0xff;
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
  } catch {
    return raw;
  }
}

export function fixMojibakeEncoding(text) {
  var raw = String(text || "");
  if (!raw) return raw;
  var candidates = [raw, latin1ToUtf8(raw), latin1ToUtf8(latin1ToUtf8(raw))];
  var best = raw;
  var bestScore = badEncodingScore(raw);
  for (var i = 0; i < candidates.length; i++) {
    var c = candidates[i];
    var score = badEncodingScore(c);
    if (score < bestScore) {
      best = c;
      bestScore = score;
    }
  }
  return best;
}

function normalizeBrokenPortuguese(text) {
  var out = String(text || "");
  var replacements = [
    [/\bN\uFFFDo\b/g, "Não"],
    [/\bn\uFFFDo\b/g, "não"],
    [/\bposs\uFFFDvel\b/gi, "possível"],
    [/\bh\uFFFD\b/g, "há"],
    [/\bH\uFFFD\b/g, "Há"],
    [/\bgal\uFFFDxia\b/gi, "galáxia"],
    [/\bL\uFFFDctea\b/g, "Láctea"],
    [/\bn\uFFFDmero\b/gi, "número"],
    [/\bbilh\uFFFDes\b/gi, "bilhões"],
    [/\bmilh\uFFFDes\b/gi, "milhões"],
    [/\best\uFFFD\b/gi, "está"],
    [/\bnÃ£o\b/g, "não"],
    [/\bNÃ£o\b/g, "Não"],
  ];
  for (var i = 0; i < replacements.length; i++) {
    out = out.replace(replacements[i][0], replacements[i][1]);
  }
  return out;
}

/** Só durante streaming SSE — não altera espaçamento nem encoding agressivo. */
export function sanitizeStreamChunk(chunk) {
  if (!chunk) return "";
  var s = String(chunk);
  s = s.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/g, "");
  s = s.replace(/[\u200b-\u200f\u2060\ufeff]/g, "");
  return s;
}

export function sanitizeOutput(text) {
  if (!text) return "";
  let s = fixMojibakeEncoding(String(text));
  s = normalizeBrokenPortuguese(s);

  s = s.normalize("NFC");
  s = s.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/g, "");
  s = s.replace(/[\u200b-\u200f\u2060\ufeff]/g, "");
  s = s.replace(/\u202f/g, " ");
  s = s.replace(/\xa0/g, " ");
  s = s.replace(/\\{2,}\s*$/gm, "");         // \\ at end of line (LaTeX row terminator) → nothing
  s = s.replace(/\\{2,}/g, "\n");             // remaining \\ → newline (LaTeX line-break)
  s = s.replace(/^\|{1,}\s*/gm, "");           // || or | at start of line (broken table row prefix)
  s = s.replace(/\|{2,}/g, "|");               // remaining multiple pipes → single
  s = s.replace(/~~([^~]*)~~/g, "$1");         // ~~strikethrough~~ → text
  s = s.replace(/~~+/g, "");                   // lone ~~ artifacts → nothing
  s = s.replace(/\*{3,}/g, "**");
  s = s.replace(/#{4,}/g, "###");
  s = s.replace(/&{2,}/g, "&");
  s = s.replace(/`{3,}(?!`)/g, "``");

  // Espaço após pontuação quando colado (ex.: "Olá.Como" → "Olá. Como")
  s = s.replace(/([.!?])([A-Za-zÀ-ÿ])/g, "$1 $2");
  s = s.replace(/([,;:])([A-Za-zÀ-ÿ])/g, "$1 $2");

  s = s.replace(/[ \t]+/g, " ");
  s = s.replace(/\n{3,}/g, "\n\n");
  s = s.replace(/^[\s]*[-=\*#_~`|]{5,}[\s]*$/gm, "");
  s = s.replace(/\s+([,;.!?])/g, "$1");
  s = s.replace(/([,;.!?])\s+/g, "$1 ");

  return s.trim();
}

/**
 * escapeHTML — escapa caracteres HTML perigosos.
 */
export function escapeHTML(text) {
  if (!text) return "";
  return sanitizeOutput(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function validateContent(content, options) {
  const opts = options || {};
  const minLen = typeof opts.minLength === "number" ? opts.minLength : 1;
  const maxLen = typeof opts.maxLength === "number" ? opts.maxLength : 500000;

  if (!content || String(content).length < minLen) {
    throw new Error("Conteúdo inválido ou vazio");
  }
  if (String(content).length > maxLen) {
    throw new Error("Conteúdo excede limite máximo");
  }
  return sanitizeOutput(content);
}

export function sanitizeForMarkdown(text) {
  let s = sanitizeOutput(text);
  if (!s) return "";

  s = s.replace(/```[a-zA-Z0-9_-]*\n?([\s\S]*?)```/g, function (_m, body) {
    return String(body || "").trim();
  });
  s = s.replace(/`([^`]+)`/g, "$1");
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, "$1 ($2)");
  s = s.replace(/!\[([^\]]*)\]\([^)\s]+\)/g, "$1");
  s = s.replace(/\*\*\*([^*]+)\*\*\*/g, "$1");
  s = s.replace(/\*\*([^*]+)\*\*/g, "$1");
  s = s.replace(/(^|[\s(])\*([^\s*][^*]*?)\*(?=[\s)\.,;:!?]|$)/g, "$1$2");
  s = s.replace(/__([^_]+)__/g, "$1");
  s = s.replace(/~~([^~]+?)~~/g, "$1");
  s = s.replace(/^[ \t]{0,3}#{1,6}[ \t]+/gm, "");
  s = s.replace(/^[ \t]{0,3}>\s?/gm, "");
  s = s.replace(/^[ \t]{0,6}[*\-+][ \t]+/gm, "• ");

  return s.trim();
}

export function sanitizeForExport(text) {
  if (!text) return "";
  // Para export, NÃO passar pelo sanitizeOutput genÃ©rico que destrÃ³i pipes de tabelas.
  // Fazer limpeza cirurÃºrgica preservando linhas com | (tabelas Markdown).
  let s = String(text);

  // Encoding e caracteres invÃ¡lidos (sem mexer em pipes)
  s = fixMojibakeEncoding(s);
  s = normalizeBrokenPortuguese(s);
  s = s.normalize("NFC");
  s = s.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/g, "");
  s = s.replace(/[\u200b-\u200f\u2060\ufeff]/g, "");
  s = s.replace(/\u202f/g, " ");
  s = s.replace(/\xa0/g, " ");

  // Artefactos LaTeX/math
  s = s.replace(/\$\$[\s\S]*?\$\$/g, " ");
  s = s.replace(/(^|\s)\$[^\$\n]+\$(\s|$)/g, " ");
  s = s.replace(/\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}/g, " ");
  s = s.replace(/\\{2,}\s*$/gm, "");
  s = s.replace(/\\{2,}/g, "\n");
  s = s.replace(/\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?/g, " ");
  s = s.replace(/\\[a-zA-Z]+/g, " ");

  // HTML tags
  s = s.replace(/<[^>]{1,200}>/g, " ");

  // Markdown inline (mantÃ©m | intacto)
  s = s.replace(/^\s*#+\s*/gm, "");
  s = s.replace(/\*\*\*([^*]+)\*\*\*/g, "$1");
  s = s.replace(/\*\*([^*]+)\*\*/g, "$1");
  s = s.replace(/\*([^*]+)\*/g, "$1");
  s = s.replace(/~~([^~]*)~~/g, "$1");
  s = s.replace(/~~+/g, "");

  // EspaÃ§o por linha, SEM remover | das tabelas
  s = s
    .split("\n")
    .map(function (line) {
      // Linhas de tabela (contÃªm |): preservar espaÃ§amento interno, apenas trim leve
      if (line.indexOf("|") !== -1) return line.replace(/^[ \t]+|[ \t]+$/g, "");
      return line.replace(/[ \t]+/g, " ").trim();
    })
    .join("\n");
  s = s.replace(/\n{3,}/g, "\n\n");

  return s.trim();
}

export default {
  sanitizeOutput,
  sanitizeStreamChunk,
  fixMojibakeEncoding,
  escapeHTML,
  validateContent,
  sanitizeForMarkdown,
  sanitizeForExport,
};
