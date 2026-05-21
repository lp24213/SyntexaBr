"use client";

import React, { useState } from "react";
import {
  multimodalExportPdf,
  multimodalExportXlsx,
  multimodalExportDocx,
  multimodalExportTxt,
} from "../lib/api";
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
  let s = sanitizeForExport(String(raw || ""));

  s = s.replace(/```[\w-]*\n?[\s\S]*?```/g, "\n");
  s = s.replace(/`([^`]+)`/g, "$1");
  s = s.replace(/\$\$[\s\S]*?\$\$/g, " ");
  s = s.replace(/(^|\s)\$[^\$\n]+\$(\s|$)/g, " ");
  s = s.replace(/\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}/g, " ");
  s = s.replace(/\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?/g, " ");
  s = s.replace(/\\[a-zA-Z]+/g, " ");
  s = s.replace(/<[^>]{1,200}>/g, " ");
  s = s.replace(/^\s*#+\s*/gm, "");
  s = s.replace(/\*\*([^*]+)\*\*/g, "$1");
  s = s.replace(/\*([^*]+)\*/g, "$1");
  s = s.replace(/^\s*[|%]{3,}.*$/gm, "");

  const lines = s.split("\n");
  const kept = lines.filter(function (line) {
    const t = line.trim();
    if (!t) return true;
    if (/^(import |from |#include|using |package |def |class |public |const |let |var |function |SELECT |INSERT |CREATE TABLE)/i.test(t))
      return false;
    if (/^(BEGIN:|\\\\documentclass|\\\\usepackage|\\\\section)/i.test(t)) return false;
    return true;
  });
  s = kept.join("\n");

  s = s
    .split("\n")
    .map(function (line) {
      return line.replace(/[ \t]+/g, " ").trim();
    })
    .join("\n");
  s = s.replace(/\n{3,}/g, "\n\n");
  s = s.trim();

  if (s.length < 30 && String(raw || "").length > 80) {
    return (
      "Resumo: a mensagem anterior continha sobretudo código ou marcação técnica. " +
      "Peça à Syntexa um texto explicativo simples e volte a exportar."
    );
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
  return "© Syntexa — Todos os direitos reservados";
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

/** Gera ficheiro real no browser ou via API — `kind`: pdf | xlsx | docx | csv | txt */
export async function downloadStructuredExport(kind, rawText, token) {
  let plain = plainTextForExport(rawText);
  if (!String(plain || "").trim()) {
    plain = fallbackBody();
  }
  const table = detectTable(plain);
  const title = defaultExportTitle();
  const subtitle = defaultSubtitle();
  const docTitleBanner = "Syntexa — " + new Date().toLocaleDateString("pt-BR");
  const brandedTitle = "Syntexa — Relatório Inteligente";

  if (kind === "csv") {
    const csv = buildCsvBlob(plain, table);
    downloadBlob(new Blob([csv], { type: "text/csv;charset=utf-8" }), "syntexa-export.csv");
    return;
  }

  /** Secções PDF/Word alinhadas: texto + tabela real quando detetada. */
  function buildSectionsForRichDocs() {
    if (table && table.rows && table.rows.length >= 2) {
      const introBody = (table.intro || "").trim();
      const out = [];
      if (introBody) out.push({ heading: "Resumo executivo", body: introBody.slice(0, 50000) });
      out.push({
        heading: "Dados estruturados",
        body: "",
        table_rows: table.rows,
      });
      out.push({ heading: "Rodapé", body: copyrightLine() });
      return out;
    }
    const chunks = plain.split(/\n{2,}/).filter(Boolean);
    if (chunks.length > 1) {
      return chunks.slice(0, 40).map(function (body, i) {
        return { heading: "Secção " + (i + 1), body: body.slice(0, 8000) };
      });
    }
    return [
      { heading: "Conteúdo", body: plain.slice(0, 50000) },
      { heading: "Rodapé", body: copyrightLine() },
    ];
  }

  if (kind === "txt") {
    const header =
      "Syntexa — exportação\n" +
      subtitle +
      "\n" +
      "-".repeat(44) +
      "\n\n";
    const blob = await multimodalExportTxt(
      { title: brandedTitle, body: (header + plain + "\n\n" + copyrightLine()).slice(0, 500000) },
      token || undefined
    );
    downloadBlob(blob, "syntexa-resposta.txt");
    return;
  }

  if (kind === "pdf") {
    const sections = buildSectionsForRichDocs();
    const blob = await multimodalExportPdf({ title: brandedTitle, subtitle, sections }, token || undefined);
    downloadBlob(blob, "syntexa-resposta.pdf");
    return;
  }

  if (kind === "xlsx") {
    let rows;
    let header = true;
    if (table && table.rows && table.rows.length) {
      const ncol = table.rows[0].length;
      const intro = String(table.intro || "").trim();
      if (intro) {
        const introLines = intro
          .split(/\n/)
          .map(function (l) {
            return l.trim();
          })
          .filter(Boolean);
        rows = [];
        for (let li = 0; li < introLines.length; li++) {
          const row = [introLines[li]];
          while (row.length < ncol) row.push("");
          rows.push(row);
        }
        const blank = [];
        for (let c = 0; c < ncol; c++) blank.push("");
        rows.push(blank);
        for (let r = 0; r < table.rows.length; r++) {
          rows.push(table.rows[r].slice());
        }
        header = false;
      } else {
        rows = table.rows;
        header = rows.length > 1;
      }
    } else {
      const lines = plain
        .split(/\n+/)
        .map(function (l) {
          return l.trim();
        })
        .filter(Boolean);
      if (lines.length) {
        rows = [["#", "Texto"]].concat(
          lines.map(function (line, i) {
            return [String(i + 1), line];
          })
        );
      } else {
        rows = [["Mensagem"], [fallbackBody()]];
      }
      header = rows.length > 1;
    }
    const blob = await multimodalExportXlsx(
      {
        sheet_title: "Dados",
        rows: rows.concat([[""], [copyrightLine()]]),
        header,
        document_title: docTitleBanner,
      },
      token || undefined
    );
    downloadBlob(blob, "syntexa-resposta.xlsx");
    return;
  }

  if (kind === "docx") {
    const sections = buildSectionsForRichDocs().map(function (sec) {
      var out = {
        heading: sec.heading,
        body: String(sec.body || "").slice(0, 8000),
      };
      if (sec.table_rows) out.table_rows = sec.table_rows;
      return out;
    });
    const blob = await multimodalExportDocx({ title: brandedTitle, sections }, token || undefined);
    downloadBlob(blob, "syntexa-resposta.docx");
    return;
  }
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

  async function run(kind) {
    setBusy(true);
    try {
      const raw =
        typeof getExportText === "function" ? String(getExportText() || "").trim() : "";
      await downloadStructuredExport(kind, raw, token || undefined);
    } finally {
      setBusy(false);
    }
  }

  const btn =
    "shrink-0 rounded-lg border border-zinc-600 px-2.5 py-2 text-xs disabled:opacity-40 hover:bg-zinc-800/10 inline-flex items-center";

  return (
    <div className={"flex w-full min-w-0 flex-col gap-2 " + (className || "")}>
      <div className="flex min-h-[2.5rem] w-full min-w-0 flex-nowrap items-center gap-1.5 overflow-x-auto overflow-y-visible pb-0.5 [scrollbar-width:thin]">
        <button type="button" disabled={busy} className={btn} onClick={() => void run("pdf")}>
          <IconLabel>
            <ToolbarIcon path="M7 3h7l5 5v13H7zM14 3v5h5M9 15h8M9 18h6" />
            PDF
          </IconLabel>
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("xlsx")}>
          <IconLabel>
            <ToolbarIcon path="M4 5h16v14H4zM4 10h16M9 5v14" />
            Excel
          </IconLabel>
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("docx")}>
          <IconLabel>
            <ToolbarIcon path="M7 3h7l5 5v13H7zM14 3v5h5M9 15h6" />
            Word
          </IconLabel>
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("csv")}>
          <IconLabel>
            <ToolbarIcon path="M4 6h16M4 12h16M4 18h16M8 4v16M16 4v16" />
            CSV
          </IconLabel>
        </button>
        <button type="button" disabled={busy} className={btn} onClick={() => void run("txt")}>
          <IconLabel>
            <ToolbarIcon path="M6 5h12M12 5v14M8 19h8" />
            TXT
          </IconLabel>
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
