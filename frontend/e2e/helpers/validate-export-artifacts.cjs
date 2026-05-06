/**
 * Lê ficheiros gerados pelo chat (export bar) e valida conteúdo — não só tamanho em bytes.
 *
 * Sobre React #418: é erro de hidratação (markup estático ≠ primeiro render no cliente).
 * Causas comuns: Math.random/data no SSR, ano em rodapé, timestamps. Corrigido no app
 * (CryptoBackground, rodapé shell, sessionId em educação, etc.); após deploy some da consola.
 */
const fs = require("fs");
const pdfParse = require("pdf-parse");
const XLSX = require("xlsx");
const mammoth = require("mammoth");

/** Junta todas as células da primeira folha numa string (para procurar marcador / números). */
function readXlsxAllText(filePath) {
  var buf = fs.readFileSync(filePath);
  var wb = XLSX.read(buf, { type: "buffer" });
  var out = "";
  var sn = wb.SheetNames[0];
  if (!sn) return "";
  var ws = wb.Sheets[sn];
  var rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
  for (var r = 0; r < rows.length; r++) {
    var row = rows[r];
    if (!Array.isArray(row)) continue;
    for (var c = 0; c < row.length; c++) {
      out += " " + String(row[c]);
    }
  }
  return out.trim();
}

function readCsvUtf8(filePath) {
  return fs.readFileSync(filePath).toString("utf8").replace(/^\uFEFF/, "");
}

async function readPdfText(filePath) {
  var buf = fs.readFileSync(filePath);
  try {
    var data = await pdfParse(buf);
    var t = String((data && data.text) || "").trim();
    if (t.length > 20) return t;
  } catch (_) {}
  try {
    var pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
    var getDocument = pdfjs.getDocument;
    var task = getDocument({ data: new Uint8Array(buf), useSystemFonts: true });
    var pdf = await task.promise;
    var text = "";
    for (var pi = 1; pi <= pdf.numPages; pi++) {
      var page = await pdf.getPage(pi);
      var tc = await page.getTextContent();
      for (var j = 0; j < tc.items.length; j++) {
        var it = tc.items[j];
        if (it && typeof it.str === "string") text += it.str + " ";
      }
      text += "\n";
    }
    if (text.trim().length > 10) return text;
  } catch (_) {}
  return buf.toString("latin1");
}

async function readDocxText(filePath) {
  var buf = fs.readFileSync(filePath);
  var raw = await mammoth.extractRawText({ buffer: buf });
  var md = await mammoth.convertToMarkdown({ buffer: buf });
  var a = String((raw && raw.value) || "");
  var b = String((md && md.value) || "");
  return (a + "\n" + b).trim();
}

function validateMarker(text, marker) {
  var raw = String(text || "");
  var m = String(marker || "");
  var ok = raw.indexOf(m) !== -1;
  if (!ok && m.length > 4) {
    var compact = function (s) {
      return String(s || "")
        .replace(/\s+/g, "")
        .replace(/_/g, "");
    };
    ok = compact(raw).indexOf(compact(m)) !== -1;
  }
  return {
    ok: ok,
    preview: raw.slice(0, 1200),
    length: raw.length,
  };
}

/** Tabela mínima: palavras-chave + números (planilha pode ser uma coluna por linha). */
function looksLikePriceTable(text) {
  var raw = String(text || "");
  var t = raw.toLowerCase();
  var hasHeader = /produto|pre(ç|c)o|qtd|quantidade|preço|r\$/.test(t);
  var hasDigit = /\d/.test(raw);
  var hasSep = /\|/.test(raw) || /[,;]\s*\d/.test(raw) || /\n/.test(raw);
  if (hasHeader && hasDigit && hasSep) return true;
  if (hasHeader && hasDigit && raw.length > 40) return true;
  return false;
}

module.exports = {
  readXlsxAllText,
  readCsvUtf8,
  readPdfText,
  readDocxText,
  validateMarker,
  looksLikePriceTable,
};
