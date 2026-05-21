/**
 * sanitizeOutput — normalização global de texto vindo da IA ou de APIs.
 * Preserva conteúdo legível, remove artefatos quebrados e estabiliza encoding.
 */

export function sanitizeOutput(text) {
  if (!text) return "";
  let s = String(text);

  // NFC normalização Unicode
  s = s.normalize("NFC");

  // Remove caracteres de controle invisíveis (exceto \n, \t, \r)
  s = s.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/g, "");

  // Remove zero-width e directional marks
  s = s.replace(/[\u200b-\u200f\u2060\ufeff]/g, "");

  // Narrow no-break space → espaço normal
  s = s.replace(/\u202f/g, " ");
  // Non-breaking space → espaço normal
  s = s.replace(/\xa0/g, " ");

  // Dupla barra invertida → simples (apenas quando seguida de letra ou símbolo)
  s = s.replace(/\\\\(?=[a-zA-Z0-9\\-_])/g, "\\");

  // Reduz pipes excessivos (3+) → |
  s = s.replace(/\|{3,}/g, "|");

  // Reduz asteriscos excessivos (3+) → **
  s = s.replace(/\*{3,}/g, "**");

  // Reduz hashes excessivos (4+) → ###
  s = s.replace(/#{4,}/g, "###");

  // Reduz & excessivos (2+) → &
  s = s.replace(/&{2,}/g, "&");

  // Remove backticks soltos excessivos (3+ seguidos sem conteúdo)
  s = s.replace(/`{3,}(?!`)/g, "``");

  // Colapsa espaços/tabs múltiplos em um só
  s = s.replace(/[ \t]+/g, " ");

  // Quebras de linha excessivas → no máximo 2
  s = s.replace(/\n{3,}/g, "\n\n");

  // Remove linhas que são só símbolos visuais (----, ====, ****, ####)
  s = s.replace(/^[\s]*[-=\*#_~`|]{5,}[\s]*$/gm, "");

  // Remove espaço antes de pontuação
  s = s.replace(/\s+([,;.!?])/g, "$1");

  // Remove espaço duplo após pontuação
  s = s.replace(/([,;.!?])\s+/g, "$1 ");

  return s.trim();
}

/**
 * escapeHTML — escapa caracteres HTML perigosos.
 * Usar SEMPRE antes de inserir texto dinâmico no DOM.
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

/**
 * validateContent — garante que conteúdo não é vazio/inválido antes de processar.
 */
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

/**
 * sanitizeForMarkdown — remove artefatos markdown pesados mas preserva estrutura.
 * Usado quando o texto vai ser convertido para markdown ou exibido como texto corrido.
 */
export function sanitizeForMarkdown(text) {
  let s = sanitizeOutput(text);
  if (!s) return "";

  // Remove blocos de código mas preserva conteúdo
  s = s.replace(/```[a-zA-Z0-9_-]*\n?([\s\S]*?)```/g, function (_m, body) {
    return String(body || "").trim();
  });

  // Inline code → texto
  s = s.replace(/`([^`]+)`/g, "$1");

  // Links [texto](url) → texto (url)
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, "$1 ($2)");

  // Imagens ![alt](url) → alt
  s = s.replace(/!\[([^\]]*)\]\([^)\s]+\)/g, "$1");

  // Bold/italic excessivo → texto
  s = s.replace(/\*\*\*([^*]+)\*\*\*/g, "$1");
  s = s.replace(/\*\*([^*]+)\*\*/g, "$1");
  s = s.replace(/(^|[\s(])\*([^\s*][^*]*?)\*(?=[\s)\.,;:!?]|$)/g, "$1$2");
  s = s.replace(/__([^_]+)__/g, "$1");

  // Strikethrough
  s = s.replace(/~~([^~]+?)~~/g, "$1");

  // Cabeçalhos no início da linha
  s = s.replace(/^[ \t]{0,3}#{1,6}[ \t]+/gm, "");

  // Blockquote
  s = s.replace(/^[ \t]{0,3}>\s?/gm, "");

  // Lista → marcador
  s = s.replace(/^[ \t]{0,6}[*\-+][ \t]+/gm, "• ");

  return s.trim();
}

/**
 * sanitizeForExport — prepara texto para exportação (PDF, CSV, XLSX, TXT).
 * Remove artefatos visuais mas preserva tabelas e estrutura.
 */
export function sanitizeForExport(text) {
  let s = sanitizeOutput(text);
  if (!s) return "";

  // Remove LaTeX bruto
  s = s.replace(/\$\$[\s\S]*?\$\$/g, " ");
  s = s.replace(/(^|\s)\$[^\$\n]+\$(\s|$)/g, " ");
  s = s.replace(/\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}/g, " ");
  s = s.replace(/\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?/g, " ");
  s = s.replace(/\\[a-zA-Z]+/g, " ");

  // Remove tags HTML cruas
  s = s.replace(/<[^>]{1,200}>/g, " ");

  // Remove linhas de separação markdown
  s = s.replace(/^\s*[|%-]{3,}.*$/gm, "");

  // Remove cabeçalhos markdown
  s = s.replace(/^\s*#+\s*/gm, "");

  // Remove negrito/italico
  s = s.replace(/\*\*([^*]+)\*\*/g, "$1");
  s = s.replace(/\*([^*]+)\*/g, "$1");

  // Normaliza linhas
  s = s
    .split("\n")
    .map(function (line) {
      return line.replace(/[ \t]+/g, " ").trim();
    })
    .join("\n");

  s = s.replace(/\n{3,}/g, "\n\n");

  return s.trim();
}

export default {
  sanitizeOutput,
  escapeHTML,
  validateContent,
  sanitizeForMarkdown,
  sanitizeForExport,
};
