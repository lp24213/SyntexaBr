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
function buildCsvBlob(plain, table) {
  if (table && table.rows && table.rows.length) {
    const ncol = table.rows[0].length;
    const outMatrix = [];
    const intro = String(table.intro || "").trim();
    if (intro) {
      const introLines = intro.split(/\n/).map(function (l) {
        return l.trim();
      });
      for (let li = 0; li < introLines.length; li++) {
        if (!introLines[li]) continue;
        const row = [introLines[li]];
        while (row.length < ncol) row.push("");
        outMatrix.push(row);
      }
      if (outMatrix.length) {
        const blank = [];
        for (let c = 0; c < ncol; c++) blank.push("");
        outMatrix.push(blank);
      }
    }
    for (let r = 0; r < table.rows.length; r++) {
      outMatrix.push(table.rows[r].slice());
    }
    const rows = outMatrix.map(function (row) {
      while (row.length < ncol) row.push("");
      return row.slice(0, ncol).map(quoteCsvCell);
    });
    rows.push([quoteCsvCell(copyrightLine())]);
    return "\uFEFF" + rows.join("\n");
  }
  const lines = plain
    .split(/\n+/)
    .map(function (l) {
      return l.trim();
    })
    .filter(Boolean);
  const out = [["#", "Texto"]];
  for (let i = 0; i < lines.length; i++) {
    out.push([String(i + 1), lines[i]]);
  }
  out.push(["", ""]);
  out.push(["", copyrightLine()]);
  return (
    "\uFEFF" +
    out
      .map(function (row) {
        return row
          .map(function (cell) {
            return '"' + String(cell).replace(/"/g, '""') + '"';
          })
          .join(",");
      })
      .join("\n")
  );
}

export function downloadBlobNamed(blob, name) {
  downloadBlob(blob, name);
}

// Em produção, sempre usar api.syntexabr.com.br (não .pages.dev)
// Importar a mesma função que api.js usa para consistência
const PRODUCTION_API_BASE = "https://api.syntexabr.com.br";
const API_BASE = PRODUCTION_API_BASE;

/** Chama o backend para gerar PDF/DOCX/XLSX reais e faz download do binário. */
async function downloadFromBackend(kind, plain, table, token) {
  const title = "Syntexa — Relatório Inteligente";
  const subtitle = defaultSubtitle();
  let url, body, filename, mime;

  if (kind === "pdf") {
    url = API_BASE + "/v1/multimodal/export/pdf";
    const sections = [];
    if (table && table.rows && table.rows.length >= 2) {
      if (table.intro) sections.push({ heading: "Introdução", body: table.intro });
      sections.push({ heading: "Dados", body: "", table_rows: table.rows });
    } else {
      sections.push({ heading: "Conteúdo", body: plain || fallbackBody() });
    }
    body = JSON.stringify({ title, subtitle, sections });
    filename = "syntexa-documento.pdf";
    mime = "application/pdf";
  } else if (kind === "docx") {
    url = API_BASE + "/v1/multimodal/export/docx";
    const sections = [];
    if (table && table.rows && table.rows.length >= 2) {
      if (table.intro) sections.push({ heading: "Introdução", body: table.intro });
      sections.push({ heading: "Dados", body: "", table_rows: table.rows });
    } else {
      sections.push({ heading: "Conteúdo", body: plain || fallbackBody() });
    }
    body = JSON.stringify({ title, sections });
    filename = "syntexa-documento.docx";
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  } else if (kind === "xlsx") {
    url = API_BASE + "/v1/multimodal/export/xlsx";
    let rows;
    if (table && table.rows && table.rows.length >= 2) {
      rows = table.rows;
    } else {
      rows = [["Conteúdo"], [plain || fallbackBody()]];
    }
    body = JSON.stringify({ sheet_title: "Syntexa", rows, header: true, document_title: title });
    filename = "syntexa-planilha.xlsx";
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  }

  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;
  const resp = await fetch(url, { method: "POST", headers, body });
  if (!resp.ok) throw new Error("Erro do servidor ao gerar " + kind.toUpperCase() + " (" + resp.status + ")");
  const blob = await resp.blob();
  downloadBlob(blob, filename);
}

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
  const blocks = String(rawText || "").split(/\n\n(?=Você:|Assistente:)/);
  const out = [];
  blocks.forEach(function (block) {
    const isUser = block.indexOf("Você:") === 0;
    const isAI = block.indexOf("Assistente:") === 0;
    const content = block.replace(/^(Você:|Assistente:)\s*/, "").trim();
    if (!content) return;
    out.push({ role: isUser ? "user" : isAI ? "ai" : "doc", content: content });
  });
  return out;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * EXPORTAÇÃO PRINCIPAL
 * ═════════════════════════════════════════════════════════════════════════ */

/** Gera ficheiro client-side. `kind`: pdf | xlsx | docx | csv | txt | html */
export async function downloadStructuredExport(kind, rawText, token) {
  // Debug: garantir que temos conteúdo
  if (!rawText || String(rawText).trim().length === 0) {
    alert("Nenhum conteúdo para exportar. Envie uma mensagem primeiro.");
    return;
  }

  let plain = plainTextForExport(rawText);
  if (!String(plain || "").trim()) plain = fallbackBody();
  const table = detectTable(plain);

  // ── TXT ─────────────────────────────────────────────────────────────────────
  if (kind === "txt") {
    const chat = splitChatBlocks(rawText);
    let out = "";
    if (chat.length) {
      chat.forEach(function (m) {
        if (m.role === "user") out += "─── PERGUNTA ───\n" + m.content + "\n\n";
        else if (m.role === "ai") out += "─── RESPOSTA ───\n" + m.content + "\n\n";
        else out += m.content + "\n\n";
      });
    } else {
      out = plain;
    }
    downloadBlob(
      new Blob([out.trim() + "\n"], { type: "text/plain;charset=utf-8" }),
      "documento.txt"
    );
    return;
  }

  // ── CSV ─────────────────────────────────────────────────────────────────────
  if (kind === "csv") {
    const csv = buildCsvBlob(plain, table);
    downloadBlob(new Blob([csv], { type: "text/csv;charset=utf-8" }), "documento.csv");
    return;
  }

  // ── Conteúdo principal: extrai conversa em PERGUNTA/RESPOSTA + parseia markdown
  const chat = splitChatBlocks(rawText);
  // Concatena só o conteúdo (sem rótulos role) para parsing; mantém perguntas como heading h3
  const blocksAll = [];
  if (chat.length) {
    chat.forEach(function (m) {
      if (m.role === "user") {
        blocksAll.push({ type: "h3", text: "Pergunta" });
        // Tratar texto como parágrafo
        blocksAll.push({ type: "p", text: m.content });
      } else if (m.role === "ai") {
        // Parseia markdown completo da resposta
        const parsed = parseMarkdown(m.content);
        if (parsed.length) parsed.forEach(function (b) { blocksAll.push(b); });
        else blocksAll.push({ type: "p", text: m.content });
      } else {
        const parsed = parseMarkdown(m.content);
        parsed.forEach(function (b) { blocksAll.push(b); });
      }
    });
  } else {
    parseMarkdown(plain).forEach(function (b) { blocksAll.push(b); });
  }

  // ── XLSX — usa o pacote xlsx para gerar ficheiro nativo .xlsx ──────────────
  if (kind === "xlsx" || kind === "_xlsx_legacy") {
    const wb = XLSX.utils.book_new();

    // Coleta tabelas markdown encontradas; se não houver tabelas, gera linhas de texto.
    const markdownTables = blocksAll.filter(function (b) { return b.type === "table"; });

    if (markdownTables.length) {
      markdownTables.forEach(function (t, idx) {
        const aoa = [t.header.slice()];
        t.rows.forEach(function (r) { aoa.push(r.slice()); });
        const ws = XLSX.utils.aoa_to_sheet(aoa);
        // Largura das colunas baseada no maior conteúdo
        const ncol = t.header.length;
        const colW = [];
        for (let c = 0; c < ncol; c++) {
          let max = String(t.header[c] || "").length;
          t.rows.forEach(function (r) { max = Math.max(max, String(r[c] || "").length); });
          colW.push({ wch: Math.min(60, Math.max(12, max + 2)) });
        }
        ws["!cols"] = colW;
        // Wrap text e altura mínima
        const range = XLSX.utils.decode_range(ws["!ref"]);
        for (let R = range.s.r; R <= range.e.r; ++R) {
          for (let C = range.s.c; C <= range.e.c; ++C) {
            const addr = XLSX.utils.encode_cell({ r: R, c: C });
            const cell = ws[addr];
            if (!cell) continue;
            cell.s = cell.s || {};
            cell.s.alignment = { vertical: "top", wrapText: true };
            if (R === 0) cell.s.font = { bold: true };
          }
        }
        XLSX.utils.book_append_sheet(wb, ws, "Tabela " + (idx + 1));
      });
    } else if (table && table.rows && table.rows.length) {
      // Tabela detectada por separadores não-markdown
      const aoa = table.rows.slice();
      const ws = XLSX.utils.aoa_to_sheet(aoa);
      const ncol = aoa[0].length;
      const colW = [];
      for (let c = 0; c < ncol; c++) {
        let max = 12;
        aoa.forEach(function (r) { max = Math.max(max, String(r[c] || "").length); });
        colW.push({ wch: Math.min(60, max + 2) });
      }
      ws["!cols"] = colW;
      XLSX.utils.book_append_sheet(wb, ws, "Dados");
    } else {
      // Conversa completa em duas colunas (Tipo | Conteúdo)
      const aoa = [["Tipo", "Conteúdo"]];
      if (chat.length) {
        chat.forEach(function (m) {
          const tag = m.role === "user" ? "Pergunta" : m.role === "ai" ? "Resposta" : "Documento";
          aoa.push([tag, m.content]);
        });
      } else {
        aoa.push(["Texto", plain]);
      }
      const ws = XLSX.utils.aoa_to_sheet(aoa);
      ws["!cols"] = [{ wch: 14 }, { wch: 100 }];
      // Wrap text na coluna B
      const range = XLSX.utils.decode_range(ws["!ref"]);
      ws["!rows"] = [];
      for (let R = range.s.r; R <= range.e.r; ++R) {
        const rowH = R === 0 ? 22 : 60;
        ws["!rows"].push({ hpt: rowH });
        for (let C = range.s.c; C <= range.e.c; ++C) {
          const addr = XLSX.utils.encode_cell({ r: R, c: C });
          const cell = ws[addr];
          if (!cell) continue;
          cell.s = cell.s || {};
          cell.s.alignment = { vertical: "top", wrapText: true };
          if (R === 0) cell.s.font = { bold: true };
        }
      }
      XLSX.utils.book_append_sheet(wb, ws, "Documento");
    }

    const arr = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    downloadBlob(
      new Blob([arr], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }),
      "documento.xlsx"
    );
    return;
  }

  // ── HTML — documento autónomo, visual limpo, SEM branding ──────────────────
  if (kind === "html") {
    const htmlDoc = buildCleanHtmlDocument(blocksAll);
    downloadBlob(new Blob([htmlDoc], { type: "text/html;charset=utf-8" }), "documento.html");
    return;
  }

  // ── PDF — html2pdf.js no cliente, visual profissional, SEM branding ────────
  if (kind === "pdf" || kind === "_pdf_legacy") {
    const html2pdf = (await import("html2pdf.js")).default;
    const innerHtml = blocksToHtml(blocksAll);

    // Container OFFSCREEN com largura fixa A4 ~794px @ 96dpi
    const pdfWrap = document.createElement("div");
    pdfWrap.style.cssText = [
      "position:fixed",
      "left:-10000px",
      "top:0",
      "width:794px",
      "background:#ffffff",
      "color:#1e293b",
      "font-family:'Segoe UI',Inter,Arial,sans-serif",
      "padding:48px 56px",
      "box-sizing:border-box",
      "line-height:1.6",
    ].join(";");
    pdfWrap.innerHTML = innerHtml || '<p style="color:#94a3b8;font-style:italic;text-align:center;padding:40px;">Sem conteúdo para exportar.</p>';

    document.body.appendChild(pdfWrap);
    try {
      await html2pdf().set({
        margin: [12, 0, 14, 0],
        filename: "documento.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff", logging: false, windowWidth: 794 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait", compress: true },
        pagebreak: { mode: ["css", "legacy"] },
      }).from(pdfWrap).save();
    } finally {
      try { document.body.removeChild(pdfWrap); } catch (e) { /* ignore */ }
    }
    return;
  }

  // ── DOCX — RTF que o Word abre nativamente, sem branding ──────────────────
  if (kind === "docx" || kind === "_docx_legacy") {
    function _rtfSafe(s) {
      return String(s || "").replace(/[\\{}]/g, "").replace(/[\u0080-\uffff]/g, function (c) {
        return "\\u" + c.charCodeAt(0) + "?";
      });
    }
    var rtf = "{\\rtf1\\ansi\\ansicpg1252\\deff0\n";
    rtf += "{\\fonttbl{\\f0\\fswiss\\fcharset0 Calibri;}{\\f1\\fswiss\\fcharset0 Calibri;}}\n";
    rtf += "{\\colortbl ;\\red15\\green23\\blue42;\\red100\\green116\\blue139;\\red255\\green255\\blue255;\\red30\\green41\\blue59;}\n";

    blocksAll.forEach(function (b) {
      if (b.type === "h1") {
        rtf += "\\pard\\sb240\\sa120\\cf1\\f1\\fs36\\b " + _rtfSafe(b.text) + "\\b0\\par\n";
      } else if (b.type === "h2") {
        rtf += "\\pard\\sb200\\sa100\\cf1\\f1\\fs28\\b " + _rtfSafe(b.text) + "\\b0\\par\n";
      } else if (b.type === "h3") {
        rtf += "\\pard\\sb160\\sa80\\cf1\\f1\\fs24\\b " + _rtfSafe(b.text) + "\\b0\\par\n";
      } else if (b.type === "p") {
        rtf += "\\pard\\sb60\\sa120\\cf1\\f0\\fs22 " + _rtfSafe(b.text).replace(/\n/g, "\\line ") + "\\par\n";
      } else if (b.type === "ul") {
        b.items.forEach(function (it) {
          rtf += "\\pard\\fi-300\\li500\\sb40\\sa60\\cf1\\f0\\fs22 \\bullet  " + _rtfSafe(it) + "\\par\n";
        });
      } else if (b.type === "ol") {
        b.items.forEach(function (it, idx) {
          rtf += "\\pard\\fi-300\\li500\\sb40\\sa60\\cf1\\f0\\fs22 " + (idx + 1) + ".  " + _rtfSafe(it) + "\\par\n";
        });
      } else if (b.type === "code") {
        rtf += "\\pard\\sb80\\sa80\\cf4\\f0\\fs20 " + _rtfSafe(b.text).replace(/\n/g, "\\line ") + "\\par\n";
      } else if (b.type === "quote") {
        rtf += "\\pard\\li400\\sb80\\sa80\\cf2\\f0\\fs22\\i " + _rtfSafe(b.text).replace(/\n/g, "\\line ") + "\\i0\\par\n";
      } else if (b.type === "hr") {
        rtf += "\\pard\\brdrb\\brdrs\\brdrw10\\brsp20\\par\n";
      } else if (b.type === "table") {
        var ncolsT = b.header.length;
        var cellW = Math.floor(8600 / ncolsT);
        // Header
        rtf += "\\trowd\\trgaph115\\trleft0\n";
        for (var c0 = 0; c0 < ncolsT; c0++) {
          rtf += "\\clcbpat1 \\clbrdrt\\brdrs\\brdrw10\\clbrdrb\\brdrs\\brdrw10\\clbrdrl\\brdrs\\brdrw10\\clbrdrr\\brdrs\\brdrw10 ";
          rtf += "\\cellx" + ((c0 + 1) * cellW) + "\n";
        }
        b.header.forEach(function (h) {
          rtf += "\\pard\\intbl\\cf3\\f1\\fs20\\b " + _rtfSafe(h) + "\\b0\\cell\n";
        });
        rtf += "\\row\n";
        // Rows
        b.rows.forEach(function (r, ri) {
          rtf += "\\trowd\\trgaph115\\trleft0\n";
          for (var c1 = 0; c1 < ncolsT; c1++) {
            if (ri % 2 === 1) rtf += "\\clcbpat3 ";
            rtf += "\\clbrdrt\\brdrs\\brdrw10\\clbrdrb\\brdrs\\brdrw10\\clbrdrl\\brdrs\\brdrw10\\clbrdrr\\brdrs\\brdrw10 ";
            rtf += "\\cellx" + ((c1 + 1) * cellW) + "\n";
          }
          r.forEach(function (cell) {
            rtf += "\\pard\\intbl\\cf1\\f0\\fs20 " + _rtfSafe(cell) + "\\cell\n";
          });
          rtf += "\\row\n";
        });
        rtf += "\\pard\\par\n";
      }
    });

    rtf += "}";
    downloadBlob(new Blob([rtf], { type: "application/msword" }), "documento.docx");
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

  async function run(kind) {
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
        <button type="button" disabled={busy} className={btn} onClick={() => void run("pdf")}>
          <ToolbarIcon path="M7 3h7l5 5v13H7zM14 3v5h5M9 15h8M9 18h6" />
          PDF
        </button>
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
