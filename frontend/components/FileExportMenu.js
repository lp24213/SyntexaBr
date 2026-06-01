"use client";

import React, { useState } from "react";
import * as XLSX from "xlsx";
import { sanitizeForExport } from "../lib/sanitizeOutput";
import { AudioRecorder } from "./AudioRecorder";

function ToolbarIcon(props) {
  var path = props.path;
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5 shrink-0" aria-hidden="true">
      <path d={path} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconLabel(props) {
  return <span className="inline-flex items-center gap-1.5">{props.children}</span>;
}

function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.rel = "noopener";
  try {
    document.body.appendChild(a);
    a.click();
  } finally {
    try {
      a.remove();
    } catch (e) {
      /* ignore */
    }
  }
  setTimeout(function () {
    try {
      URL.revokeObjectURL(url);
    } catch (e) {
      /* ignore */
    }
  }, 2500);
}

/**
 * Remove código/LaTeX/markdown pesado mas **mantém quebras de linha e tabelas em texto**.
 * (A versão antiga colapsava todo o [ \\t]+ no texto inteiro e destruía linhas/tabelas.)
 */
export function plainTextForExport(raw) {
  if (!raw) return "";
  let s = String(raw);

  // 1. Remove blocos de código (não são conteúdo para export)
  s = s.replace(/```[\w-]*\n?[\s\S]*?```/g, "\n");
  s = s.replace(/`([^`]+)`/g, "$1");

  // 2. Remove LaTeX/math
  s = s.replace(/\$\$[\s\S]*?\$\$/g, " ");
  s = s.replace(/(^|\s)\$[^\$\n]+\$(\s|$)/g, " ");
  s = s.replace(/\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}/g, " ");
  s = s.replace(/\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?/g, " ");
  s = s.replace(/\\[a-zA-Z]+/g, " ");

  // 3. Remove HTML tags
  s = s.replace(/<[^>]{1,200}>/g, " ");

  // 4. Remove markdown headings e bold/italic — mas NÃO pipes
  s = s.replace(/^\s*#+\s*/gm, "");
  s = s.replace(/\*\*\*([^*]+)\*\*\*/g, "$1");
  s = s.replace(/\*\*([^*]+)\*\*/g, "$1");
  s = s.replace(/\*([^*]+)\*/g, "$1");
  s = s.replace(/~~([^~]*)~~/g, "$1");

  // 5. Processar linha a linha — preservar linhas de tabela (contêm |) intactas
  const lines = s.split("\n");
  const kept = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const t = line.trim();
    // Linha de tabela Markdown — preservar sem alterar
    if (t.indexOf("|") !== -1) {
      kept.push(t);
      continue;
    }
    // Linha vazia — manter
    if (!t) { kept.push(""); continue; }
    // Filtrar linhas de código soltas
    if (/^(import |from |#include|using |package |def |class |public |const |let |var |function |SELECT |INSERT |CREATE TABLE)/i.test(t)) continue;
    if (/^(BEGIN:|\\documentclass|\\usepackage|\\section)/i.test(t)) continue;
    // Linha normal — colapsar espaços
    kept.push(line.replace(/[ \t]+/g, " ").trim());
  }
  s = kept.join("\n");
  s = s.replace(/\n{3,}/g, "\n\n");
  s = s.trim();

  if (s.length < 30 && String(raw).length > 80) {
    return "Resumo: a mensagem continha sobretudo código técnico. Peça um texto explicativo e exporte novamente.";
  }
  return s.slice(0, 120000);
}

/** Linha tipo `| A | B |` ou linha separadora de tabela Markdown. */
function parsePipeTableRow(line) {
  const t = String(line || "").trim();
  if (!t || !/\|/.test(t)) return null;
  if (/^\|[\s\-:|]+\|\s*$/.test(t)) return null;
  const parts = t.split("|");
  const cells = [];
  for (let p = 0; p < parts.length; p++) {
    const c = parts[p].trim();
    if (p === 0 && c === "") continue;
    if (p === parts.length - 1 && c === "") continue;
    cells.push(c);
  }
  if (cells.length < 2) return null;
  return cells;
}

function isMarkdownTableSeparator(line) {
  const t = String(line || "").trim();
  return /^\|[\s\-:|]+\|\s*$/.test(t) || /^[\s\-:|]+$/.test(t);
}

/**
 * Extrai tabela (pipes estilo Markdown) + texto anterior.
 */
function extractPipeTable(plain) {
  const lines = plain.split(/\n/).map(function (l) {
    return l.trim();
  });
  for (let start = 0; start < lines.length; start++) {
    let r0 = parsePipeTableRow(lines[start]);
    if (!r0) continue;
    let idx = start + 1;
    if (idx < lines.length && isMarkdownTableSeparator(lines[idx])) idx++;
    const block = [r0];
    while (idx < lines.length) {
      const rn = parsePipeTableRow(lines[idx]);
      if (!rn || rn.length !== r0.length) break;
      block.push(rn);
      idx++;
    }
    if (block.length >= 2) {
      const intro = lines.slice(0, start).join("\n").trim();
      return { intro, rows: block };
    }
  }
  return null;
}

/**
 * Tabela com separador ; (comum em PT-BR quando não há pipes).
 */
function extractSemicolonTable(plain) {
  const lines = plain.split(/\n/).map(function (l) {
    return l.trim();
  });
  for (let start = 0; start < lines.length; start++) {
    const p = lines[start].split(";").map(function (x) {
      return x.trim();
    });
    if (p.length < 2 || p.some(function (x) {
      return !x;
    }))
      continue;
    const block = [p];
    let j = start + 1;
    while (j < lines.length) {
      const q = lines[j].split(";").map(function (x) {
        return x.trim();
      });
      if (q.length !== p.length) break;
      block.push(q);
      j++;
    }
    if (block.length >= 2) {
      const intro = lines.slice(0, start).join("\n").trim();
      return { intro, rows: block };
    }
  }
  return null;
}

/** Linhas com tabulação (colar do Excel). */
function extractTabTable(plain) {
  const lines = plain.split(/\n/).map(function (l) {
    return l.trim();
  });
  for (let start = 0; start < lines.length; start++) {
    if (!lines[start] || !/\t/.test(lines[start])) continue;
    const p = lines[start].split(/\t/).map(function (x) {
      return x.trim();
    });
    if (p.length < 2) continue;
    const block = [p];
    let j = start + 1;
    while (j < lines.length) {
      if (!/\t/.test(lines[j])) break;
      const q = lines[j].split(/\t/).map(function (x) {
        return x.trim();
      });
      if (q.length !== p.length) break;
      block.push(q);
      j++;
    }
    if (block.length >= 2) {
      const intro = lines.slice(0, start).join("\n").trim();
      return { intro, rows: block };
    }
  }
  return null;
}

/**
 * Vírgulas como separador (ex.: dados colados de CSV). Exige ≥3 colunas para não confundir com frases.
 */
function extractCommaTable(plain) {
  const lines = plain.split(/\n/).map(function (l) {
    return l.trim();
  });
  for (let start = 0; start < lines.length; start++) {
    const p = lines[start].split(",").map(function (x) {
      return x.trim();
    });
    if (p.length < 3 || p.some(function (x) {
      return !x;
    }))
      continue;
    const block = [p];
    let j = start + 1;
    while (j < lines.length) {
      const q = lines[j].split(",").map(function (x) {
        return x.trim();
      });
      if (q.length !== p.length || q.some(function (x) {
        return !x;
      }))
        break;
      block.push(q);
      j++;
    }
    if (block.length >= 2) {
      const intro = lines.slice(0, start).join("\n").trim();
      return { intro, rows: block };
    }
  }
  return null;
}

function detectTable(plain) {
  return (
    extractPipeTable(plain) ||
    extractTabTable(plain) ||
    extractSemicolonTable(plain) ||
    extractCommaTable(plain)
  );
}

/** Conteúdo mínimo quando não há texto útil. */
function fallbackBody() {
  return "(Não há texto na resposta do assistente para exportar. Peça uma resposta e tente de novo.)";
}

function defaultExportTitle() {
  return "Syntexa";
}

function defaultSubtitle() {
  return new Date().toLocaleString("pt-BR");
}

function quoteCsvCell(cell) {
  return '"' + String(cell != null ? cell : "").replace(/"/g, '""') + '"';
}

function copyrightLine() {
  return "";
}

/** CSV: colunas reais com tabela; senão duas colunas (#, linha) para abrir bem no Excel. */
// DEPRECATED: usar apenas a lógica dentro de downloadStructuredExport()
// function buildCsvBlob(plain, table) { ... }

export function downloadBlobNamed(blob, name) {
  downloadBlob(blob, name);
}

// Em produção, sempre usar api.syntexabr.com.br (não .pages.dev)
// Importar a mesma função que api.js usa para consistência
const PRODUCTION_API_BASE = "https://api.syntexabr.com.br";
const API_BASE = PRODUCTION_API_BASE;

/* ═══════════════════════════════════════════════════════════════════════════
 * HELPERS DE PARSING — Markdown leve → segmentos estruturados
 * ═════════════════════════════════════════════════════════════════════════ */

function escHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** Converte markdown inline (negrito/itálico/código/links) para HTML. */
function inlineMd(s) {
  return escHtml(s)
    .replace(/\*\*\*([^*\n]+)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<![*])\*([^*\n]{1,200})\*(?!\*)/g, "<em>$1</em>")
    .replace(/`([^`\n]+)`/g, '<code style="background:#f1f5f9;padding:1px 5px;border-radius:3px;font-family:Consolas,monospace;font-size:0.92em;">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" style="color:#2563eb;text-decoration:underline;">$1</a>');
}

/** Detecta separador Markdown de tabela. */
function isTableSep(line) {
  return /^\s*\|?[\s\-:|]+\|?\s*$/.test(String(line || "")) && /[-]/.test(String(line || ""));
}

/** Parseia uma linha tipo `| a | b |` em array de células. Retorna null se inválido. */
function parseTableRow(line) {
  const t = String(line || "").trim();
  if (!t || t.indexOf("|") === -1) return null;
  const stripped = t.replace(/^\||\|$/g, "");
  return stripped.split("|").map(function (c) { return c.trim(); });
}

/**
 * Parse de markdown estruturado → array de blocos:
 *   { type: "h1"|"h2"|"h3"|"p"|"ul"|"ol"|"table"|"code"|"hr"|"quote", ... }
 */
function parseMarkdown(raw) {
  const lines = String(raw || "").split(/\r?\n/);
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    let line = lines[i];
    const trimmed = line.trim();

    // Bloco vazio
    if (!trimmed) { i++; continue; }

    // Bloco de código ```
    if (/^```/.test(trimmed)) {
      const codeLines = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i].trim())) {
        codeLines.push(lines[i]);
        i++;
      }
      i++;
      blocks.push({ type: "code", text: codeLines.join("\n") });
      continue;
    }

    // Linha horizontal
    if (/^(\*\s*\*\s*\*+|-\s*-\s*-+|_\s*_\s*_+)$/.test(trimmed)) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // Citação >
    if (/^>\s?/.test(trimmed)) {
      const quoteLines = [];
      while (i < lines.length && /^>\s?/.test(lines[i].trim())) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({ type: "quote", text: quoteLines.join("\n") });
      continue;
    }

    // Headings
    let m;
    if ((m = trimmed.match(/^(#{1,6})\s+(.+)$/))) {
      const level = Math.min(m[1].length, 3);
      blocks.push({ type: "h" + level, text: m[2].trim() });
      i++;
      continue;
    }

    // Tabela markdown
    if (trimmed.indexOf("|") !== -1 && i + 1 < lines.length && isTableSep(lines[i + 1])) {
      const headerCells = parseTableRow(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].trim().indexOf("|") !== -1) {
        const r = parseTableRow(lines[i]);
        if (!r) break;
        // Normalizar n.º de colunas
        while (r.length < headerCells.length) r.push("");
        rows.push(r.slice(0, headerCells.length));
        i++;
      }
      blocks.push({ type: "table", header: headerCells, rows: rows });
      continue;
    }

    // Lista não-ordenada
    if (/^[-*+]\s+/.test(trimmed)) {
      const items = [];
      while (i < lines.length && /^[-*+]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*+]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items: items });
      continue;
    }

    // Lista ordenada
    if (/^\d+[.)]\s+/.test(trimmed)) {
      const items = [];
      while (i < lines.length && /^\d+[.)]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+[.)]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items: items });
      continue;
    }

    // Parágrafo (junta linhas até linha vazia ou início de outro bloco)
    const paraLines = [line];
    i++;
    while (i < lines.length) {
      const t2 = lines[i].trim();
      if (!t2) break;
      if (/^(#{1,6}\s|[-*+]\s|\d+[.)]\s|>\s|```|---|\*\*\*)/.test(t2)) break;
      if (t2.indexOf("|") !== -1 && i + 1 < lines.length && isTableSep(lines[i + 1])) break;
      paraLines.push(lines[i]);
      i++;
    }
    blocks.push({ type: "p", text: paraLines.join("\n").trim() });
  }
  return blocks;
}

/** Converte blocos parseados em HTML inline-styled (para html2pdf e ficheiro HTML standalone). */
function blocksToHtml(blocks, opts) {
  opts = opts || {};
  const out = [];
  blocks.forEach(function (b) {
    if (b.type === "h1") {
      out.push('<h1 style="font-size:22px;font-weight:700;margin:24px 0 12px;color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:8px;">' + inlineMd(b.text) + "</h1>");
    } else if (b.type === "h2") {
      out.push('<h2 style="font-size:18px;font-weight:600;margin:20px 0 10px;color:#0f172a;">' + inlineMd(b.text) + "</h2>");
    } else if (b.type === "h3") {
      out.push('<h3 style="font-size:15px;font-weight:600;margin:16px 0 8px;color:#1e293b;">' + inlineMd(b.text) + "</h3>");
    } else if (b.type === "p") {
      const html = inlineMd(b.text).replace(/\n/g, "<br/>");
      out.push('<p style="margin:0 0 12px;font-size:13px;line-height:1.7;color:#1e293b;text-align:justify;">' + html + "</p>");
    } else if (b.type === "ul") {
      const items = b.items.map(function (it) {
        return '<li style="margin:0 0 6px;line-height:1.65;">' + inlineMd(it) + "</li>";
      }).join("");
      out.push('<ul style="margin:8px 0 14px 22px;padding:0;font-size:13px;color:#1e293b;">' + items + "</ul>");
    } else if (b.type === "ol") {
      const items = b.items.map(function (it) {
        return '<li style="margin:0 0 6px;line-height:1.65;">' + inlineMd(it) + "</li>";
      }).join("");
      out.push('<ol style="margin:8px 0 14px 22px;padding:0;font-size:13px;color:#1e293b;">' + items + "</ol>");
    } else if (b.type === "table") {
      const thead = b.header.map(function (h) {
        return '<th style="background:#0f172a;color:#fff;padding:10px 12px;text-align:left;font-weight:600;font-size:12px;border:1px solid #0f172a;">' + inlineMd(h) + "</th>";
      }).join("");
      const tbody = b.rows.map(function (r, ri) {
        const bg = ri % 2 === 0 ? "#ffffff" : "#f8fafc";
        const tds = r.map(function (c) {
          return '<td style="padding:8px 12px;border:1px solid #e2e8f0;font-size:12px;color:#1e293b;background:' + bg + ';vertical-align:top;">' + inlineMd(c) + "</td>";
        }).join("");
        return "<tr>" + tds + "</tr>";
      }).join("");
      out.push('<table style="width:100%;border-collapse:collapse;margin:12px 0 16px;font-family:inherit;"><thead><tr>' + thead + "</tr></thead><tbody>" + tbody + "</tbody></table>");
    } else if (b.type === "code") {
      out.push('<pre style="background:#0f172a;color:#e2e8f0;padding:12px 16px;border-radius:6px;font-family:Consolas,Monaco,monospace;font-size:11px;line-height:1.55;overflow:auto;white-space:pre-wrap;margin:10px 0 14px;">' + escHtml(b.text) + "</pre>");
    } else if (b.type === "quote") {
      out.push('<blockquote style="margin:10px 0;padding:8px 14px;border-left:3px solid #94a3b8;background:#f8fafc;color:#475569;font-style:italic;font-size:13px;line-height:1.65;">' + inlineMd(b.text).replace(/\n/g, "<br/>") + "</blockquote>");
    } else if (b.type === "hr") {
      out.push('<hr style="border:none;border-top:1px solid #cbd5e1;margin:18px 0;"/>');
    }
  });
  return out.join("\n");
}

/** Separa raw chat-text em mensagens. Cada mensagem retorna { role, content }. */
function splitChatBlocks(rawText) {
  const text = String(rawText || "").trim();
  if (!text) return [];
  
  // Encontra todas as posições de "Você:" e "Assistente:"
  const out = [];
  let lastIdx = 0;
  const regex = /\n(Você:|Assistente:)\s*/g;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    const role = match[1].trim();
    const startIdx = match.index + match[0].length;
    
    // Encontra o próximo rótulo ou fim do texto
    const nextMatch = regex.exec(text);
    const endIdx = nextMatch ? nextMatch.index : text.length;
    
    const content = text.substring(startIdx, endIdx).trim();
    
    if (content && content.length > 0) {
      out.push({
        role: role === "Você:" ? "user" : "ai",
        content: content
      });
    }
    
    if (!nextMatch) break;
    // Volta o lastIndex para encontrar proxima iteracao
    regex.lastIndex = nextMatch.index + 1;
  }
  
  return out;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * EXPORTAÇÃO PRINCIPAL — VERSÃO CORRIGIDA
 * ═════════════════════════════════════════════════════════════════════════ */

/** Gera ficheiro. `kind`: pdf | xlsx | docx | csv | txt | html */
export async function downloadStructuredExport(kind, rawText, token, options) {
  options = options || {};
  // Validação
  if (!rawText || String(rawText).trim().length === 0) {
    throw new Error("Nenhum conteúdo para exportar. Envie uma mensagem primeiro.");
  }
  
  if (!kind || typeof kind !== "string") {
    throw new Error("Tipo de exportação inválido.");
  }
  
  const rawStr = String(rawText).trim();
  if (rawStr.length > 500000) {
    throw new Error("Conteúdo muito grande para exportar (máx. 500KB). Divida em partes menores.");
  }

  const title = "Syntexa — Documento";
  const subtitle = new Date().toLocaleString("pt-BR");
  
  // ─────────────────────────────────────────────────────────────────────────────
  // TXT: Split por "Você:" e "Assistente:" + salva como plaintext
  if (kind === "txt") {
    const chat = splitChatBlocks(rawText);
    let out = "";
    chat.forEach(function (m) {
      const label = m.role === "user" ? "PERGUNTA:" : "RESPOSTA:";
      out += label + "\n" + m.content + "\n\n";
    });
    if (!out.trim()) out = rawText;
    downloadBlob(
      new Blob([out.trim() + "\n"], { type: "text/plain;charset=utf-8" }),
      "documento.txt"
    );
    return;
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // CSV: Perguntas e respostas em 2 colunas
  if (kind === "csv") {
    const chat = splitChatBlocks(rawText);
    const rows = [["Tipo", "Conteúdo"]];
    chat.forEach(function (m) {
      const tipo = m.role === "user" ? "Pergunta" : "Resposta";
      rows.push([tipo, m.content]);
    });
    const csv = rows.map(function (row) {
      return row.map(function (cell) {
        return '"' + String(cell).replace(/"/g, '""') + '"';
      }).join(",");
    }).join("\n");
    downloadBlob(
      new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" }),
      "documento.csv"
    );
    return;
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // HTML: Gera HTML auto-contido com CSS
  if (kind === "html") {
    const chat = splitChatBlocks(rawText);
    const bodyHtml = chat.map(function (m) {
      const heading = m.role === "user" ? '<h3 style="color:#0f172a;margin-top:20px;margin-bottom:8px;">Pergunta</h3>' : '<h3 style="color:#0f172a;margin-top:20px;margin-bottom:8px;">Resposta</h3>';
      const content = '<p style="margin:0 0 12px;font-size:14px;line-height:1.7;color:#1e293b;text-align:justify;">' + escHtml(m.content).replace(/\n/g, "<br/>") + '</p>';
      return heading + content;
    }).join("\n");
    const htmlDoc = buildCleanHtmlDocument([]);
    // Inject content
    const htmlWithContent = htmlDoc.replace(
      /<div class="page-body">/,
      '<div class="page-body">' + bodyHtml
    );
    downloadBlob(
      new Blob([htmlWithContent], { type: "text/html;charset=utf-8" }),
      "documento.html"
    );
    return;
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // PDF, DOCX, XLSX: Envia para backend (MUITO MAIS CONFIÁVEL)
  // Converte a conversa em sections estruturadas
  const chat = splitChatBlocks(rawText);
  const sections = [];
  
  chat.forEach(function (m) {
    if (m.role === "user") {
      sections.push({
        heading: "Pergunta",
        body: m.content
      });
    } else if (m.role === "ai") {
      sections.push({
        heading: "Resposta",
        body: m.content
      });
    }
  });
  
  if (sections.length === 0) {
    sections.push({ heading: "Conteúdo", body: rawText });
  }

  // PDF via backend
  if (kind === "pdf" || kind === "pdf-styled" || kind === "pdf-simple") {
    const styled = kind === "pdf-styled" || (kind === "pdf" ? true : false);
    const includeFooter = options.includeFooter || false;
    const url = API_BASE + "/v1/multimodal/export/pdf";
    const body = JSON.stringify({
      title, subtitle, sections,
      styled: styled,
      include_footer: includeFooter
    });
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;
    
    try {
      const resp = await fetch(url, { method: "POST", headers, body });
      if (!resp.ok) throw new Error("Status " + resp.status);
      const blob = await resp.blob();
      const suffix = styled ? "visual" : "simples";
      downloadBlob(blob, `documento-${suffix}.pdf`);
      console.log("[EXPORT SUCCESS] PDF gerado via backend");
    } catch (err) {
      console.error("[EXPORT ERROR] PDF:", err);
      throw err;
    }
    return;
  }

  // DOCX via backend
  if (kind === "docx") {
    const url = API_BASE + "/v1/multimodal/export/docx";
    const body = JSON.stringify({ title, sections });
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;
    
    try {
      const resp = await fetch(url, { method: "POST", headers, body });
      if (!resp.ok) throw new Error("Status " + resp.status);
      const blob = await resp.blob();
      downloadBlob(blob, "documento.docx");
      console.log("[EXPORT SUCCESS] DOCX gerado via backend");
    } catch (err) {
      console.error("[EXPORT ERROR] DOCX:", err);
      throw err;
    }
    return;
  }

  // XLSX via backend
  if (kind === "xlsx") {
    const rows = [["Tipo", "Conteúdo"]];
    chat.forEach(function (m) {
      const tipo = m.role === "user" ? "Pergunta" : "Resposta";
      rows.push([tipo, m.content]);
    });
    
    const url = API_BASE + "/v1/multimodal/export/xlsx";
    const body = JSON.stringify({
      sheet_title: "Documento",
      rows: rows,
      header: true,
      document_title: title
    });
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;
    
    try {
      const resp = await fetch(url, { method: "POST", headers, body });
      if (!resp.ok) throw new Error("Status " + resp.status);
      const blob = await resp.blob();
      downloadBlob(blob, "documento.xlsx");
      console.log("[EXPORT SUCCESS] XLSX gerado via backend");
    } catch (err) {
      console.error("[EXPORT ERROR] XLSX:", err);
      throw err;
    }
    return;
  }
}

/** Constrói HTML self-contained limpo e profissional, sem logotipo nem rodapé Syntexa. */
function buildCleanHtmlDocument(blocks) {
  const bodyHtml = blocksToHtml(blocks);
  const date = new Date().toLocaleString("pt-BR");
  return [
    "<!DOCTYPE html>",
    '<html lang="pt-BR">',
    "<head>",
    '<meta charset="utf-8"/>',
    '<meta name="viewport" content="width=device-width,initial-scale=1"/>',
    "<title>Documento</title>",
    "<style>",
    "*{box-sizing:border-box;}",
    "body{margin:0;padding:0;font-family:'Segoe UI',Inter,Arial,sans-serif;background:#f8fafc;color:#1e293b;line-height:1.65;}",
    ".page{max-width:860px;margin:40px auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;box-shadow:0 4px 32px rgba(15,23,42,.07);}",
    ".page-head{padding:28px 40px 20px;border-bottom:1px solid #e2e8f0;background:#fff;}",
    ".page-head .date{font-size:11px;color:#94a3b8;letter-spacing:.04em;margin-bottom:4px;}",
    ".page-body{padding:32px 40px 40px;}",
    "h1,h2,h3{color:#0f172a;font-weight:700;line-height:1.25;}",
    "h1{font-size:24px;margin:0 0 18px;}",
    "h2{font-size:19px;margin:28px 0 12px;border-bottom:1px solid #e2e8f0;padding-bottom:6px;}",
    "h3{font-size:15px;margin:20px 0 8px;color:#334155;}",
    "p{margin:0 0 13px;font-size:14px;line-height:1.7;text-align:justify;}",
    "ul,ol{margin:6px 0 14px 24px;padding:0;font-size:14px;color:#1e293b;}",
    "li{margin:0 0 6px;line-height:1.65;}",
    "table{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px;}",
    "thead th{background:#0f172a;color:#fff;text-align:left;padding:10px 14px;font-weight:600;font-size:12px;letter-spacing:.03em;}",
    "tbody td{padding:9px 14px;border:1px solid #e2e8f0;color:#1e293b;vertical-align:top;}",
    "tbody tr:nth-child(even) td{background:#f8fafc;}",
    "pre{background:#0f172a;color:#e2e8f0;padding:14px 18px;border-radius:8px;font-family:Consolas,monospace;font-size:12px;line-height:1.55;overflow:auto;white-space:pre-wrap;margin:12px 0 16px;}",
    "code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace;font-size:92%;}",
    "blockquote{margin:12px 0;padding:10px 16px;border-left:4px solid #cbd5e1;background:#f8fafc;color:#475569;font-style:italic;font-size:13px;}",
    "hr{border:none;border-top:1px solid #e2e8f0;margin:22px 0;}",
    "@media print{body{background:#fff;}.page{border:none;box-shadow:none;margin:0;border-radius:0;}}",
    "</style>",
    "</head>",
    "<body>",
    '<div class="page">',
    '<div class="page-head">',
    '<div class="date">' + date + "</div>",
    "</div>",
    '<div class="page-body">',
    bodyHtml || '<p style="color:#94a3b8;font-style:italic;text-align:center;padding:30px;">Sem conteúdo para exportar.</p>',
    "</div>",
    "</div>",
    "</body>",
    "</html>",
  ].join("\n");
}

/**
 * Barra PDF/Excel/… + **uma** entrada de voz (IA): STT → mesmo fluxo que enviar texto.
 * @param {"chat"|"server"} [voicePipelineMode="chat"] — server usa /v1/multimodal/voice/conversation
 */
export function FileExportMenu({
  token,
  className,
  getExportText,
  onVoiceSubmitChat,
  onVoicePipelineResult,
  onVoiceError,
  voicePipelineMode = "chat",
}) {
  const [busy, setBusy] = useState(false);
  const [exportError, setExportError] = useState("");
  const [pdfOpen, setPdfOpen] = useState(false);

  async function run(kind) {
    setPdfOpen(false);
    setBusy(true);
    setExportError("");
    try {
      const raw =
        typeof getExportText === "function" ? String(getExportText() || "").trim() : "";
      await downloadStructuredExport(kind, raw, token || undefined);
    } catch (err) {
      var msg = err instanceof Error ? err.message : String(err);
      setExportError(msg || "Falha ao exportar. Verifique sua conexão e tente novamente.");
    } finally {
      setBusy(false);
    }
  }

  const btn =
    "shrink-0 h-9 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-3 text-xs text-[#475569] hover:bg-[#f1f5f9] disabled:opacity-40 inline-flex items-center gap-1.5 transition-colors";

  return (
    <div className={"flex w-full min-w-0 flex-col gap-1 " + (className || "")}>
      {exportError && (
        <p className="text-xs text-red-500 px-1" role="alert">{exportError}</p>
      )}
      <div className="flex min-h-[2.25rem] w-full min-w-0 flex-nowrap items-center gap-1.5 overflow-x-auto pb-0.5 [scrollbar-width:none]">
        {busy && <span className="syntexa-spinner shrink-0" aria-hidden="true" />}
        <div className="relative inline-flex items-center">
          <button type="button" disabled={busy} className={btn + " rounded-r-none border-r-0"} onClick={() => void run("pdf-styled")}>
            <ToolbarIcon path="M7 3h7l5 5v13H7zM14 3v5h5M9 15h8M9 18h6" />
            PDF
          </button>
          <button
            type="button"
            disabled={busy}
            className={btn + " rounded-l-none px-2"}
            onClick={() => setPdfOpen((v) => !v)}
            aria-haspopup="true"
            aria-expanded={pdfOpen}
          >
            <svg viewBox="0 0 24 24" fill="none" className="h-3 w-3" aria-hidden="true">
              <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          {pdfOpen && (
            <div className="absolute left-0 top-[calc(100%+4px)] z-30 min-w-[10rem] rounded-lg border border-[#e2e8f0] bg-white shadow-lg overflow-hidden">
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-xs text-[#475569] hover:bg-[#f1f5f9]"
                onClick={() => { setPdfOpen(false); run("pdf-styled"); }}
              >
                <span className="inline-block h-2 w-2 rounded-full bg-[#3b82f6]" />
                Com visual (estilizado)
              </button>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-xs text-[#475569] hover:bg-[#f1f5f9]"
                onClick={() => { setPdfOpen(false); run("pdf-simple"); }}
              >
                <span className="inline-block h-2 w-2 rounded-full bg-[#94a3b8]" />
                Simples (limpo)
              </button>
            </div>
          )}
        </div>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("xlsx")}>
          <ToolbarIcon path="M4 5h16v14H4zM4 10h16M9 5v14" />
          Excel
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("docx")}>
          <ToolbarIcon path="M7 3h7l5 5v13H7zM14 3v5h5M9 15h6" />
          Word
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("html")}>
          <ToolbarIcon path="M4 4h16v16H4zM4 9h16M9 4v5" />
          HTML
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("csv")}>
          <ToolbarIcon path="M4 6h16M4 12h16M4 18h16M8 4v16M16 4v16" />
          CSV
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("txt")}>
          <ToolbarIcon path="M6 5h12M12 5v14M8 19h8" />
          TXT
        </button>
      </div>
      {typeof onVoiceSubmitChat === "function" && (
        <div className="relative z-20 flex w-full min-w-0 shrink-0 items-center border-t border-zinc-200/90 pt-2">
          <AudioRecorder
            key="syntexa-toolbar-voz-ia"
            token={token}
            mode="pipeline"
            pipelineMode={voicePipelineMode === "server" ? "server" : "chat"}
            onVoiceSubmitChat={onVoiceSubmitChat}
            onVoicePipelineResult={
              voicePipelineMode === "server" && typeof onVoicePipelineResult === "function"
                ? onVoicePipelineResult
                : undefined
            }
            onError={onVoiceError}
            buttonLabel="Voz (IA)"
            buttonIcon={<ToolbarIcon path="M12 3a4 4 0 014 4v5a4 4 0 11-8 0V7a4 4 0 014-4zm-7 9h2a5 5 0 0010 0h2a7 7 0 01-6 6.92V21h-2v-2.08A7 7 0 015 12z" />}
            className="inline-flex w-full min-w-0 sm:w-auto"
          />
        </div>
      )}
    </div>
  );
}
