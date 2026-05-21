"use client";
import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ChatLayout } from "../../components/chat-layout";
import { DesktopDevPanel } from "../../components/desktop-dev-panel";
import { Button } from "../../components/ui/button";
import {
  FileExportMenu,
  plainTextForExport,
  downloadStructuredExport,
} from "../../components/FileExportMenu";
import { ChatRichContent } from "../../components/chat-rich-content";
import { toExportReadyText } from "../../lib/chat-rich-format";
import {
  USER_FACING_TRY_AGAIN,
  USER_FACING_CONNECTION,
  chatCompletion,
  chatCompletionStreamWithFallback,
  chatCompletionWithMedia,
  publicChat,
  generateImage,
  generateMusic,
  generateSpeech,
  generateVideo,
  getProfile,
  publicChatStreamWithFallback,
  publicChatWithMedia,
  getChatSessionMessages,
  listChatSessions,
  multimodalAnalyze,
  multimodalSmartExport,
  getApiBase,
  getClientLocale,
} from "../../lib/api";

/** Detecta pedido de mídia em PT-BR (crie/gere/gerar/mande/envie imagem, vídeo, áudio). */
function detectMediaIntent(text) {
  var w = (text || "").toLowerCase();
  var create =
    /\b(crie|criar|gere|gera|gerar|desenhe|desenha|faça|faca|fazer|fa[çc]o|elabore|produza|monte|gerem|criem|façam|facam|manda|mande|envia|envie|me\s+manda|me\s+mande|me\s+envia|me\s+envie)\b/.test(
      w
    );
  var img =
    /\b(imagem|foto|fotografia|ilustra(ç|c)(a|ã)o|ilustracao|desenho)\b/.test(w) ||
    /\b(imagem|foto)\s+de\s+/.test(w);
  var vid =
    /\b(v(í|i)deo|vídeos|videos|clip(\s+de)?|anima(ç|c)(a|ã)o|animacao)\b/.test(w);
  var aud =
    /\b(áudio|audio|som|música|musica|trilha|beat|música instrumental)\b/.test(w) &&
    !/\b(voz|falar|ler em voz|texto em voz|narra(ç|c)(a|ã)o)\b/.test(w);
  var speech =
    /\b(gere voz|fale em voz|leia em voz|texto em voz|narra(ç|c)(a|ã)o|narração|leia isso|fale isso)\b/.test(
      w
    );
  var verbImg =
    /\b(gere|gera|gerar|crie|criar|manda|mande|envia|envie)\s+(?:uma\s+|um\s+)?(imagem|foto|ilustra|desenho)\b/.test(
      w
    );
  return {
    wantsImage:
      (create && img) ||
      verbImg ||
      /\bquero\s+(?:uma\s+)?(imagem|foto)\b/.test(w) ||
      /\bgere\s+(uma\s+)?(imagem|foto)\b/.test(w) ||
      /\bgera\s+(uma\s+)?(imagem|foto)\b/.test(w) ||
      /\bgerar\s+(?:uma\s+)?(imagem|foto)\b/.test(w),
    wantsVideo:
      (create && vid) ||
      /\b(gere|gera|gerar|crie|criar|manda|mande)\s+(?:um\s+)?(vídeo|video|clip)\b/.test(w) ||
      /\bgere\s+(um\s+)?v(í|i)deo\b/.test(w) ||
      /\bgera\s+(um\s+)?v(í|i)deo\b/.test(w),
    wantsAudio:
      (create && aud) ||
      /\b(gere|gera|gerar|crie|criar)\s+(?:um\s+)?(áudio|audio|som|música|musica)\b/.test(w) ||
      /\bgere\s+(um\s+)?(áudio|audio|som)\b/.test(w) ||
      /\bgera\s+(um\s+)?(áudio|audio|som)\b/.test(w),
    wantsSpeech: speech,
  };
}

function _badEncodingScore(text) {
  var t = String(text || "");
  var badMarks = (t.match(/Ã|Â|â|�|Ð|þ/g) || []).length;
  var replacement = (t.match(/\uFFFD/g) || []).length;
  var weird = (t.match(/[^\x09\x0A\x0D\x20-\x7EÀ-ÿ]/g) || []).length;
  return badMarks * 4 + replacement * 6 + weird;
}

function _looksNaturalPT(text) {
  var t = String(text || "");
  if (!t) return false;
  if (/[áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]/.test(t)) return true;
  return /\b(que|não|como|para|com|uma|isso|imagem|verdadeira|resposta)\b/i.test(t);
}

function _latin1ToUtf8Candidate(raw) {
  try {
    var bytes = new Uint8Array(
      Array.from(raw).map(function (ch) {
        return ch.charCodeAt(0) & 0xff;
      })
    );
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
  } catch {
    return raw;
  }
}

function _escapeDecodeCandidate(raw) {
  try {
    return decodeURIComponent(escape(raw));
  } catch {
    return raw;
  }
}

function maybeFixMojibake(text) {
  var raw = String(text || "");
  if (!raw) return raw;
  var candidates = [raw];
  candidates.push(_latin1ToUtf8Candidate(raw));
  candidates.push(_escapeDecodeCandidate(raw));
  candidates.push(_latin1ToUtf8Candidate(_latin1ToUtf8Candidate(raw)));
  candidates.push(_escapeDecodeCandidate(_latin1ToUtf8Candidate(raw)));
  var best = raw;
  var bestScore = _badEncodingScore(raw);
  for (var i = 0; i < candidates.length; i++) {
    var c = String(candidates[i] || "");
    if (!c) continue;
    var score = _badEncodingScore(c);
    if (score < bestScore) {
      best = c;
      bestScore = score;
    } else if (score === bestScore && _looksNaturalPT(c) && !_looksNaturalPT(best)) {
      best = c;
    }
  }
  return best;
}

function normalizeBrokenPortuguese(text) {
  var out = String(text || "");
  if (!out) return out;
  var replacements = [
    [/\bN�o\b/g, "Não"],
    [/\bn�o\b/g, "não"],
    [/\bposs�vel\b/gi, "possível"],
    [/\bh�\b/g, "há"],
    [/\bH�\b/g, "Há"],
    [/\bgal�xia\b/gi, "galáxia"],
    [/\bL�ctea\b/g, "Láctea"],
    [/\bn�mero\b/gi, "número"],
    [/\bbilh�es\b/gi, "bilhões"],
    [/\bmilh�es\b/gi, "milhões"],
    [/\best�\b/gi, "está"],
    [/\bnÃ£o\b/g, "não"],
    [/\bNÃ£o\b/g, "Não"],
  ];
  for (var i = 0; i < replacements.length; i++) {
    out = out.replace(replacements[i][0], replacements[i][1]);
  }
  return out;
}

function stripBadControlChars(text) {
  var s = String(text || "");
  var out = "";
  for (var i = 0; i < s.length; i++) {
    var c = s.charCodeAt(i);
    if (c === 0xfffd) continue;
    if (c === 9 || c === 10 || c === 13 || c >= 32) out += s.charAt(i);
  }
  return out;
}

function stripVisualNoiseLines(text) {
  var lines = String(text || "").split("\n");
  var out = [];
  for (var i = 0; i < lines.length; i++) {
    var ln = String(lines[i] || "");
    var t = ln.trim();
    if (!t) {
      out.push("");
      continue;
    }
    // remove linhas com "lixo visual" puro: |||---***___%%% etc
    if (/^[|_\-*=~`^#%&$@!+.:;,\\/()\[\]{}<>?¨"'’`´]+$/.test(t)) continue;
    // remove linhas extremamente simbólicas com poucos caracteres alfanuméricos
    var alnum = (t.match(/[a-zA-Z0-9À-ÿ]/g) || []).length;
    var sym = (t.match(/[^a-zA-Z0-9À-ÿ\s]/g) || []).length;
    if (sym >= 6 && alnum <= 2) continue;
    out.push(ln);
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Remove ** # ` e artefactos comuns de LLM; deixa texto legível no chat. */
function stripMarkdownForChatDisplay(text) {
  var t = String(text || "");
  if (!t) return t;
  t = t.replace(/```[\s\S]*?```/g, "\n");
  t = t.replace(/`([^`]+)`/g, "$1");
  t = t.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  t = t.replace(/\*\*\*([^*]+)\*\*\*/g, "$1");
  t = t.replace(/\*\*([^*]+)\*\*/g, "$1");
  t = t.replace(/\*([^*\n]{2,120})\*/g, "$1");
  t = t.replace(/__([^_]+)__/g, "$1");
  t = t.replace(new RegExp("^#{1,6}\\s+", "gm"), "");
  t = t.replace(new RegExp("^\\s*[-*+]\\s+", "gm"), "• ");
  t = t.replace(/[\u200b\u200c\u200d\ufeff]/g, "");
  t = t.replace(/[ \t]+/g, " ");
  t = t.replace(/\n{3,}/g, "\n\n");
  t = t.replace(/\s+,/g, ",");
  t = t.replace(/\s+\./g, ".");
  return t.trim();
}

function sanitizeChatText(text) {
  return stripVisualNoiseLines(
    stripMarkdownForChatDisplay(
      stripBadControlChars(normalizeBrokenPortuguese(maybeFixMojibake(text)))
    )
  );
}

/** Durante SSE: não aplicar heurísticas agressivas de mojibake em cada chunk (evita texto cortado). */
function sanitizeChatStreamDelta(prev, chunk) {
  return stripBadControlChars(String(prev || "") + String(chunk || ""));
}

function isAssistantPlaceholderContent(s) {
  return /^(?:Gerando|A gerar)\s/i.test(String(s || ""));
}

function isImagePlaceholderContent(s) {
  return /^(?:Gerando|A gerar)\s+imagem/i.test(String(s || ""));
}

/** Bolha só com aviso de download (export rápido) — não é “conteúdo” para o próximo ficheiro. */
function isAssistantExportSuccessNoise(s) {
  var t = String(s || "").trim();
  if (!t) return true;
  if (/^(?:Excel|PDF|Word|CSV|TXT|Ficheiro)\s+gerado\b/i.test(t) && /download|navegador/i.test(t)) return true;
  if (/ficheiro real,\s*não código no chat/i.test(t)) return true;
  return false;
}

function absoluteApiFileUrl(path) {
  if (!path || typeof path !== "string") return "";
  if (/^https?:\/\//i.test(path)) return path;
  var base = getApiBase().replace(/\/$/, "");
  var p = path.startsWith("/") ? path : "/" + path;
  return base + p;
}

function downloadLabelForSmartFile(f) {
  var k = String((f && f.kind) || "").toLowerCase();
  var map = {
    xlsx: "Baixar XLSX",
    pdf: "Baixar PDF",
    docx: "Baixar DOCX",
    ods: "Baixar ODS",
    csv: "Baixar CSV",
    txt: "Baixar TXT",
  };
  return map[k] || "Baixar " + (k || "ficheiro").toUpperCase();
}

function DownloadIcon() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", fill: "none", className: "h-3.5 w-3.5 shrink-0", "aria-hidden": true },
    React.createElement("path", {
      d: "M12 4v10m0 0l-4-4m4 4l4-4M5 18h14",
      stroke: "currentColor",
      strokeWidth: "1.8",
      strokeLinecap: "round",
      strokeLinejoin: "round",
    })
  );
}

function CheckCircleIcon() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", fill: "none", className: "h-3.5 w-3.5 shrink-0 text-emerald-700", "aria-hidden": true },
    React.createElement("path", {
      d: "M9 12.5l2 2 4-4m6 1.5a9 9 0 11-18 0 9 9 0 0118 0z",
      stroke: "currentColor",
      strokeWidth: "1.8",
      strokeLinecap: "round",
      strokeLinejoin: "round",
    })
  );
}

/** Última resposta “real” do assistente (ignora placeholders e bolhas só com ficheiros gerados). */
function getLastAssistantExportText(messageList) {
  if (!Array.isArray(messageList)) return "";
  var i;
  for (i = messageList.length - 1; i >= 0; i--) {
    var m = messageList[i];
    if (!m || m.role !== "assistant" || !m.content) continue;
    if (isAssistantPlaceholderContent(m.content)) continue;
    if (isAssistantExportSuccessNoise(m.content)) continue;
    if (m.smartFiles && m.smartFiles.length) continue;
    return toExportReadyText(String(m.content));
  }
  for (i = messageList.length - 1; i >= 0; i--) {
    m = messageList[i];
    if (!m || m.role !== "assistant" || !m.content) continue;
    if (isAssistantPlaceholderContent(m.content)) continue;
    if (isAssistantExportSuccessNoise(m.content)) continue;
    return toExportReadyText(String(m.content));
  }
  return "";
}

/**
 * Pedido para gerar documento/planilha com conteúdo novo descrito na mensagem (não exportar só a última bolha).
 * Evita confundir “gera planilha de alimentação…” com export da resposta anterior.
 */
function isGenerativeDocumentRequest(text) {
  var t = String(text || "");
  var w = t.toLowerCase();
  if (t.length >= 130) return true;
  if (
    /\b(alimenta(ç|c)|nutri(ç|c)|dieta|card(á|a)pio|ectomorfo|mesomorfo|hipertrofia|massa muscular|bulking|macros?|calorias)\b/.test(
      w
    )
  )
    return true;
  if (/\b(planilha|excel|xlsx)\b/.test(w) && /\b(de|para|sobre|com)\s+\w{4,}/.test(w)) return true;
  if (/\b(n(ã|a)o quero|nao quero|sem biografia|n(ã|a)o (é|e) sobre)\b/i.test(t)) return true;
  return false;
}

/** Para smart-export: não reutilizar texto antigo do chat quando o pedido já descreve o ficheiro. */
function shouldOmitPriorAssistantForSmartExport(text) {
  return isGenerativeDocumentRequest(text);
}

/** Pedido explícito de exportar a última resposta em PDF (evita depender do LLM gerar LaTeX). */
function detectPdfExportIntent(text) {
  var w = String(text || "").toLowerCase();
  return (
    /\b(exporta|exporte|baixa|baixar|gera|gere|cria|crie)\s+(um\s+)?(pdf|documento\s+pdf|ficheiro\s+pdf|arquivo\s+pdf)\b/.test(
      w
    ) ||
    /\b(quero|preciso|mande|manda)\s+(um\s+)?pdf\b/.test(w) ||
    /\bpdf\b.*\b(export|download|baixa|gera)\b/.test(w)
  );
}

/** PDF / Excel / Word / CSV — intercetado antes do LLM para gerar ficheiro real, não “código no chat”. */
function detectStructuredFileExportIntent(text) {
  if (detectPdfExportIntent(text)) return "pdf";
  var w = String(text || "").toLowerCase();
  if (
    /\b(xlsx|excel|planilha|folha de cálculo|folha de calculo|libreoffice|calc)\b/.test(w) &&
    /\b(gera|gere|exporta|exporte|baixa|baixar|cria|crie|descarrega|manda|mande)\b/.test(w)
  )
    return "xlsx";
  if (
    /\b(docx|word|microsoft\s+word|\.docx)\b/.test(w) &&
    /\b(gera|gere|exporta|baixa|cria|crie|manda|mande)\b/.test(w)
  )
    return "docx";
  if (
    /\b(csv|ficheiro\s+csv|arquivo\s+csv)\b/.test(w) &&
    /\b(gera|gere|exporta|baixa|cria|crie)\b/.test(w)
  )
    return "csv";
  return null;
}

/** Pacote servidor: planilha financeira / contrato — ficheiros reais, não markdown. */
function detectSmartJobIntent(text) {
  var w = String(text || "").toLowerCase();
  var verb = /\b(faz|faça|faca|gera|gere|gerar|cria|crie|monta|manda|mande|exporta|exporte|envia|envie|preciso|quero|me manda)\b/.test(
    w
  );
  if (
    verb &&
    (/\bods\b/.test(w) ||
      /open\s*document\s*spreadsheet/.test(w) ||
      /libreoffice\s+calc/.test(w) ||
      /\b(exporta|exporte)\s+(em\s+)?ods\b/.test(w))
  )
    return true;
  var financialHeavy = /\b(orçamento|orcamento|financeir|receita|despesa|fluxo de caixa|custos?|saldo|balanço|balanco)\b/.test(
    w
  );
  var sheet = /\b(planilha|excel|xlsx|csv|tabela|spreadsheet|folha de cálculo|folha de calculo)\b/.test(w);
  var pdf = /\b(pdf|\.pdf|documento pdf|arquivo pdf|ficheiro pdf)\b/.test(w);
  var docx = /\b(docx|word|microsoft word|\.docx|documento word)\b/.test(w);
  var docHint = /\b(contrato|currículo|curriculo|relatório|relatorio|cronograma|currículo vitae|cv\b)\b/.test(
    w
  );
  var listHint = /\b(lista|planilha|excel|xlsx|csv|tabela|cronograma)\b/.test(w);
  if (verb && sheet && financialHeavy) return true;
  if (verb && sheet && !financialHeavy) return true;
  if (verb && pdf && !sheet) return true;
  if (verb && docx && !sheet && !pdf) return true;
  if (/\b(odf|ods|open\s*document)\b/.test(w) && verb) return true;
  if (verb && docHint && /\b(gera|gere|cria|crie|faz|faça|faca|manda|mande|exporta|exporte|envia)\b/.test(w))
    return true;
  if (verb && listHint && /\b(gera|gere|cria|crie|faz|exporta|manda)\b/.test(w)) return true;
  if (
    /\b(preciso|quero)\b/.test(w) &&
    /\b(planilha|excel|xlsx|pdf|docx|word|csv|ods|contrato|arquivo|ficheiro|anexo)\b/.test(w)
  )
    return true;
  if (
    /\b(manda|mande|envia)\b/.test(w) &&
    /\b(arquivo|ficheiro|anexo)\b/.test(w)
  )
    return true;
  if (
    /\b(contrato|currículo|curriculo|relatório|relatorio)\b/.test(w) &&
    /\b(gera|gere|cria|crie|faz|faça|faca|manda|mande|exporta|exporte)\b/.test(w)
  )
    return true;
  return false;
}

function detectImageCorrectionFollowup(text, messages) {
  var w = String(text || "").toLowerCase().trim();
  if (!w) return false;
  var correctionHints = [
    "isso não é",
    "isso nao é",
    "isso nao e",
    "quero uma",
    "quero um",
    "quero foto real",
    "quero imagem real",
    "verdadeira",
    "mais realista",
    "ficou errado",
  ];
  var hasHint = correctionHints.some(function (h) {
    return w.indexOf(h) >= 0;
  });
  if (!hasHint) return false;
  if (!Array.isArray(messages) || messages.length === 0) return false;
  for (var i = messages.length - 1; i >= 0; i--) {
    var m = messages[i];
    if (!m || m.role !== "assistant") continue;
    if (m.media && m.media.type === "image") return true;
    if (String(m.content || "").toLowerCase().indexOf("imagem gerada") >= 0) return true;
    return false;
  }
  return false;
}

/** Horário local nas bolhas (pt-BR): dia da semana, data e hora. */
function timeLabel(date) {
  try {
    var d = date instanceof Date ? date : new Date();
    var locale = getClientLocale();
    return d.toLocaleString(locale, {
      weekday: "short",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (e) {
    return "";
  }
}

function formatSessionTimestamp(iso) {
  if (!iso) return "";
  try {
    return timeLabel(new Date(iso));
  } catch (e) {
    return "";
  }
}

/** Base64 grande em data: URL quebra o <img> no Chrome ("erro de visualização"); Blob URL é estável. */
function base64ToDisplayUrl(imageBase64, mime) {
  var clean = String(imageBase64 || "").replace(/\s/g, "");
  if (!clean) return "";
  if (typeof window === "undefined") {
    return "data:" + (mime || "image/png") + ";base64," + clean;
  }
  try {
    var binary = atob(clean);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    var blob = new Blob([bytes], { type: mime || "image/png" });
    return URL.createObjectURL(blob);
  } catch (e) {
    return "data:" + (mime || "image/png") + ";base64," + clean;
  }
}

function ChatImage(props) {
  var src = props.src;
  var failed = React.useState(false);
  var setFailed = failed[1];
  var glow = React.useState(true);
  var setGlow = glow[1];
  React.useEffect(
    function () {
      setGlow(true);
      var tm = setTimeout(function () {
        setGlow(false);
      }, 900);
      return function () {
        clearTimeout(tm);
        if (src && String(src).indexOf("blob:") === 0) {
          try {
            URL.revokeObjectURL(src);
          } catch (e) {}
        }
      };
    },
    [src]
  );
  if (failed[0]) {
    return React.createElement(
      "p",
      { className: "mt-3 text-sm text-amber-300/90" },
      "Não foi possível exibir a imagem (dados inválidos ou limite do navegador). Gere de novo."
    );
  }
  return React.createElement(
    motion.div,
    {
      initial: { opacity: 0, scale: 0.98, y: 6 },
      animate: { opacity: 1, scale: 1, y: 0 },
      transition: { duration: 0.32, ease: "easeOut" },
      className:
        "relative mt-3 " +
        (glow[0] ? "ring-2 ring-violet-300/70 shadow-[0_0_0_4px_rgba(139,92,246,0.12)]" : ""),
    },
    React.createElement(
      "span",
      {
        className:
          "absolute right-2 top-2 z-10 rounded-full border border-violet-200 bg-white/90 px-2 py-0.5 text-[10px] font-semibold text-violet-700 shadow-sm backdrop-blur",
      },
      "4K Ready"
    ),
    React.createElement("img", {
      src: src,
      alt: props.alt || "Imagem gerada",
      className: "max-h-[420px] w-full rounded-xl border border-zinc-200 object-contain",
      loading: "eager",
      decoding: "async",
      onError: function () {
        setFailed(true);
      },
    })
  );
}

function ImageGenerationPlaceholder(props) {
  var label = props.label || "Gerando imagem em alta qualidade...";
  var elapsedState = React.useState(0);
  var elapsed = elapsedState[0];
  var setElapsed = elapsedState[1];

  React.useEffect(function () {
    var t0 = Date.now();
    var id = setInterval(function () {
      setElapsed(Date.now() - t0);
    }, 450);
    return function () {
      clearInterval(id);
    };
  }, []);

  var stages = ["Compondo cena", "Refinando detalhes", "Aprimorando iluminação", "Finalizando render"];
  var idx = Math.min(stages.length - 1, Math.floor(elapsed / 1600));
  var pct = Math.min(96, 18 + Math.floor(elapsed / 90));
  var eta = Math.max(2, 12 - Math.floor(elapsed / 1000));

  return React.createElement(
    "div",
    { className: "space-y-2" },
    React.createElement(
      "div",
      { className: "flex items-center gap-2 text-sm text-zinc-700" },
      React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true }),
      React.createElement("span", null, label)
    ),
    React.createElement(
      "div",
      { className: "relative overflow-hidden rounded-xl border border-zinc-200 bg-zinc-100 p-3" },
      React.createElement("div", { className: "h-44 w-full animate-pulse rounded-lg bg-gradient-to-r from-zinc-100 via-zinc-200 to-zinc-100" }),
      React.createElement(
        "span",
        {
          className:
            "absolute right-3 top-3 rounded-full border border-violet-200 bg-white/90 px-2 py-0.5 text-[10px] font-semibold text-violet-700",
        },
        "Render IA • 4K"
      ),
      React.createElement(
        "div",
        { className: "absolute bottom-3 left-3 right-3 space-y-1.5 rounded-lg border border-zinc-200 bg-white/85 px-2 py-2 backdrop-blur-sm" },
        React.createElement("p", { className: "text-[10px] font-medium text-zinc-700" }, stages[idx]),
        React.createElement("p", { className: "text-[10px] text-zinc-500" }, "ETA aproximado: ", String(eta), "s"),
        React.createElement(
          "div",
          { className: "h-1.5 w-full overflow-hidden rounded-full bg-zinc-200" },
          React.createElement(motion.div, {
            className: "h-full rounded-full bg-violet-500",
            animate: { width: pct + "%" },
            transition: { duration: 0.35, ease: "easeOut" },
          })
        )
      )
    )
  );
}

/** Prompt limpo para o provedor (menos "Olá crie..." repetido). */
function extractPromptForProvider(text, kind) {
  var t = (text || "").trim();
  if (!t) return "";
  if (kind === "image") {
    var m = t.match(
      /(?:imagem|foto|ilustra(?:ção|çao)|desenho)\s+(?:de|com|que|mostrando)\s+([\s\S]+)/i
    );
    if (m && m[1]) return m[1].trim().replace(/\s+/g, " ").slice(0, 4000);
  }
  if (kind === "video") {
    var mv = t.match(/(?:vídeo|video|videoclip)\s+(?:de|com|sobre)\s+([\s\S]+)/i);
    if (mv && mv[1]) return mv[1].trim().replace(/\s+/g, " ").slice(0, 4000);
  }
  return t.replace(/^(olá|oi|eae|opa)[!,.\s]*/i, "").trim().slice(0, 4000);
}

function mediaGenPlaceholderLabel(kind) {
  if (kind === "image") return "Gerando imagem em alta qualidade...";
  if (kind === "video") return "Gerando vídeo...";
  if (kind === "speech") return "Gerando voz...";
  return "Gerando áudio...";
}

function IconAttach() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", className: "h-4 w-4", fill: "none", "aria-hidden": true },
    React.createElement("path", { d: "M8 12.5l6.2-6.2a3 3 0 114.2 4.2l-8.6 8.6a5 5 0 11-7.1-7.1L12 2.8", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}
function IconSend() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", className: "h-4 w-4", fill: "none", "aria-hidden": true },
    React.createElement("path", { d: "M21 3L10 14", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("path", { d: "M21 3l-7 18-4-7-7-4 18-7z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" })
  );
}

/** Resumo legível da resposta /v1/multimodal/analyze para a bolha do chat. */
function formatMultimodalResult(data) {
  if (!data || typeof data !== "object") return "Análise indisponível.";
  var lines = [];
  lines.push("Análise (" + (data.detected_kind || "?") + ", " + (data.size || 0) + " bytes)");
  if (data.ocr && data.ocr.text) {
    lines.push("Texto extraído:\n" + String(data.ocr.text).slice(0, 4000));
  }
  if (data.text_preview) {
    lines.push("Pré-visualização:\n" + String(data.text_preview).slice(0, 4000));
  }
  if (data.vision && data.vision.stats) {
    lines.push("Imagem: " + data.vision.stats.width + "×" + data.vision.stats.height + " px");
  }
  if (data.vision && data.vision.description) {
    lines.push("Descrição:\n" + String(data.vision.description).slice(0, 4000));
  }
  if (data.transcription && data.transcription.text) {
    lines.push("Transcrição:\n" + String(data.transcription.text).slice(0, 4000));
  }
  if (data.note) lines.push(String(data.note));
  if (data.detail && !data.ok) lines.push(String(data.detail));
  return lines.join("\n\n") || "Nada a mostrar.";
}

export default function ChatPage() {
  const uiLocale = getClientLocale();
  const isEnglishUi = String(uiLocale || "").toLowerCase().startsWith("en");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: isEnglishUi
        ? "Hello, this is Syntexa. How can I help you?"
        : "Olá, aqui é a Syntexa. Em que posso te ajudar?",
      timestamp: "",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mediaBusy, setMediaBusy] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [plan, setPlan] = useState("anon");
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [canStop, setCanStop] = useState(false);
  const [multimodalBusy, setMultimodalBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [sessionsRefreshKey, setSessionsRefreshKey] = useState(0);
  const [focusMode, setFocusMode] = useState("");
  const [ttsBusyIdx, setTtsBusyIdx] = useState(null);
  const [fileExportBusy, setFileExportBusy] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const abortRef = useRef(null);
  /** Evita envios concorrentes (duplo clique, Enter+clique). */
  const sendBusyRef = useRef(false);
  const lastSendAtRef = useRef(0);
  var messagesEndRef = useRef(null);

  useEffect(function () {
    try {
      var el = messagesEndRef.current;
      if (el) el.scrollIntoView({ behavior: "smooth", block: "end" });
    } catch (e) {}
  }, [messages, loading, mediaBusy]);

  function isAuthErrorMessage(msg) {
    var txt = String(msg || "").toLowerCase();
    return (
      txt.indexOf("não foi possível validar as credenciais") >= 0 ||
      txt.indexOf("sessão expirada") >= 0 ||
      txt.indexOf("sessao expirada") >= 0 ||
      txt.indexOf("acesso não autorizado") >= 0 ||
      txt.indexOf("acesso nao autorizado") >= 0 ||
      txt.indexOf("unauthorized") >= 0 ||
      txt.indexOf("not authenticated") >= 0 ||
      txt.indexOf("401") >= 0
    );
  }

  function finalizeStreamingAssistantText() {
    setMessages(function (prev) {
      var p = prev.slice();
      if (!p.length) return prev;
      var last = p[p.length - 1];
      if (
        last &&
        last.role === "assistant" &&
        last.content != null &&
        !(last.smartFiles && last.smartFiles.length)
      ) {
        var fixed = sanitizeChatText(String(last.content));
        if (fixed !== last.content) p[p.length - 1] = Object.assign({}, last, { content: fixed });
      }
      return p;
    });
  }

  useEffect(function () {
    setMessages(function (prev) {
      if (prev.length !== 1) return prev;
      var m = prev[0];
      if (m.role !== "assistant" || m.timestamp) return prev;
      return [{ ...m, timestamp: timeLabel() }];
    });
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const token = window.localStorage.getItem("syntexa_token");
      setAuthToken(token);
      setIsAdmin(window.localStorage.getItem("syntexa_is_admin") === "1");
      if (!token) {
        setPlan("anon");
        return;
      }
      getProfile(token).then((profile) => {
        if (profile && profile.subscription_plan) {
          setPlan(profile.subscription_plan);
          window.localStorage.setItem("syntexa_plan", profile.subscription_plan);
        } else {
          setPlan(window.localStorage.getItem("syntexa_plan") || "free");
        }
      }).catch(() => setPlan(window.localStorage.getItem("syntexa_plan") || "free"));
    } catch {
      setPlan("anon");
    }
  }, []);

  useEffect(function () {
    try {
      var params = new URLSearchParams(window.location.search || "");
      var q = (params.get("q") || "").trim();
      var mode = (params.get("mode") || "").trim().toLowerCase();
      if (q && !input.trim()) setInput(q);
      if (mode) setFocusMode(mode);
    } catch {}
  }, []);

  function getFocusSystemPrompt(mode) {
    if (mode === "bank") {
      return [
        "MODO FOCO: banco e finanças no Brasil.",
        "Responda em formato executável com seções fixas:",
        "1) Diagnóstico rápido (até 5 bullets).",
        "2) Plano de ação de 7 dias (Dia 1..7, objetivo por dia).",
        "3) Controle financeiro pronto (campos para receita, despesa, saldo, Pix, pendências).",
        "4) Riscos e alertas (inadimplência, juros, atraso fiscal, concentração de receita).",
        "5) Próximo passo imediato (uma ação para agora).",
      ].join(" ");
    }
    if (mode === "agro") {
      return [
        "MODO FOCO: agronegócio no Brasil.",
        "Responda em formato executável com seções fixas:",
        "1) Diagnóstico da operação rural (produção, custo, gargalo).",
        "2) Plano de manejo e execução (curto prazo e safra).",
        "3) Quadro de custos (insumos, mão de obra, máquinas, logística).",
        "4) Indicadores-chave (custo/ha, margem, produtividade, ponto de equilíbrio).",
        "5) Próximo passo imediato no campo.",
      ].join(" ");
    }
    if (mode === "tax") {
      return [
        "MODO FOCO: impostos e regularização no Brasil.",
        "Responda em formato executável com seções fixas:",
        "1) Situação fiscal atual (o que está pendente).",
        "2) Checklist de documentos (objetivo e direto).",
        "3) Passo a passo com ordem de execução (Receita Federal / prefeitura / estado quando aplicável).",
        "4) Riscos de multa e como reduzir risco.",
        "5) Próximo passo imediato com prazo sugerido.",
      ].join(" ");
    }
    if (mode === "sales_whatsapp") {
      return [
        "MODO FOCO: vendas no WhatsApp.",
        "Responda em formato executável com seções fixas:",
        "1) Estratégia rápida de abordagem.",
        "2) Script pronto (abertura, qualificação, oferta, fechamento).",
        "3) Respostas prontas para 5 objeções comuns.",
        "4) Cadência de follow-up (D0, D1, D3, D7).",
        "5) Próximo envio exato para o cliente agora.",
      ].join(" ");
    }
    return "";
  }

  function applyFocusToHistory(history) {
    var systemPrompt = getFocusSystemPrompt(focusMode);
    if (!systemPrompt) return history;
    var hasSystem = Array.isArray(history) && history.some(function (m) { return m && m.role === "system"; });
    if (hasSystem) return history;
    return [{ role: "system", content: systemPrompt }].concat(history);
  }

  function getFocusComposerActions(mode) {
    if (mode === "bank") {
      return [
        ["Plano 7 Dias", "Monte um plano financeiro de 7 dias com tarefas diárias, objetivo e indicador de sucesso."],
        ["Fluxo de Caixa", "Crie um modelo de fluxo de caixa semanal com receitas, despesas, saldo e previsão."],
        ["Cobrança WhatsApp", "Escreva mensagens de cobrança por WhatsApp em 3 tons: cordial, firme e última tentativa."],
      ];
    }
    if (mode === "agro") {
      return [
        ["Plano da Safra", "Monte um plano de safra com cronograma, etapas críticas, custos e riscos."],
        ["Custos por Hectare", "Monte uma planilha-modelo de custos por hectare com categorias e fórmula de margem."],
        ["Checklist Campo", "Crie checklist operacional diário para fazenda com prioridade e responsável."],
      ];
    }
    if (mode === "tax") {
      return [
        ["Checklist Receita", "Crie checklist prático de regularização fiscal no Brasil com ordem de execução."],
        ["IRPF Passo a Passo", "Explique passo a passo de IRPF com documentos necessários e erros comuns."],
        ["Nota Fiscal", "Monte um processo simples para emissão e controle de notas fiscais no dia a dia."],
      ];
    }
    if (mode === "sales_whatsapp") {
      return [
        ["Script de Vendas", "Crie script completo de vendas no WhatsApp: abertura, qualificação, oferta e fechamento."],
        ["Quebra de Objeções", "Liste 10 objeções comuns e resposta pronta para cada uma no WhatsApp."],
        ["Cadência D0-D7", "Monte cadência de follow-up D0, D1, D3 e D7 com mensagens curtas e CTA."],
      ];
    }
    return [];
  }

  async function runFocusedQuickPrompt(promptText) {
    var content = String(promptText || "").trim();
    if (!content || loading || mediaBusy || fileExportBusy) return;
    if (sendBusyRef.current) return;
    sendBusyRef.current = true;
    try {
      await processOutgoingUserContent(content);
    } finally {
      sendBusyRef.current = false;
    }
  }

  /** Mesmo pipeline que Enter: mídia, ficheiros inteligentes, chat — usado também pela voz (STT → aqui). */
  async function processOutgoingUserContent(content) {
    var token = null;
    try {
      token = window.localStorage.getItem("syntexa_token");
    } catch (e) {
      token = null;
    }
    var cw = content.toLowerCase();
    var financialSheetCmd =
      /\b(orçamento|orcamento|financeir|receita|despesa|fluxo\s+de\s+caixa|custos?|saldo|balanço|balanco)\b/.test(
        cw
      ) &&
      /\b(planilha|excel|xlsx|csv|tabela|folha\s+de\s+c[aá]lculo|folha\s+de\s+calculo)\b/.test(cw);

    /* Export estruturado (PDF/Excel/…) da última resposta — antes do pacote smart (planilha financeira modelo vai para smart). */
    var structuredExportKind = detectStructuredFileExportIntent(content);
    if (structuredExportKind && !financialSheetCmd && !isGenerativeDocumentRequest(content)) {
      var lastAsst2 = getLastAssistantExportText(messages);
      if (!lastAsst2) {
        setMessages((prev) =>
          prev.concat([
            { role: "user", content: content, timestamp: timeLabel() },
            {
              role: "assistant",
              content:
                "Não há resposta anterior para exportar. Peça primeiro um texto; depois use os botões PDF, Excel, Word ou CSV na barra, ou os botões por mensagem.",
              timestamp: timeLabel(),
            },
          ])
        );
        setInput("");
        return;
      }
      var exportLabels = { pdf: "PDF", xlsx: "Excel", docx: "Word", csv: "CSV" };
      var genLine =
        "Gerando " + (exportLabels[structuredExportKind] || "ficheiro") + "…";
      setFileExportBusy(true);
      setMessages((prev) =>
        prev.concat([
          { role: "user", content: content, timestamp: timeLabel() },
          { role: "assistant", content: genLine, timestamp: timeLabel() },
        ])
      );
      setInput("");
      try {
        await downloadStructuredExport(structuredExportKind, lastAsst2, token || undefined);
        setMessages((prev) => {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content:
              (exportLabels[structuredExportKind] || "Ficheiro") +
              " gerado — o download deve começar no navegador (ficheiro real, não código no chat).",
            timestamp: timeLabel(),
          };
          return p;
        });
      } catch (errEx) {
        var mpex = errEx instanceof Error ? errEx.message : String(errEx);
        setMessages((prev) => {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content: /sess[aã]o|401|autorizado/i.test(mpex)
              ? "Inicie sessão para exportar ficheiros, ou tente de novo em instantes."
              : USER_FACING_TRY_AGAIN,
            timestamp: timeLabel(),
          };
          return p;
        });
      } finally {
        setFileExportBusy(false);
      }
      return;
    }

    var mediaIntent = detectMediaIntent(content);
    var imageCorrectionFollowup = detectImageCorrectionFollowup(content, messages);
    var wantsImage = mediaIntent.wantsImage;
    var wantsVideo = mediaIntent.wantsVideo;
    var wantsAudio = mediaIntent.wantsAudio;
    var wantsSpeech = mediaIntent.wantsSpeech;
    if (imageCorrectionFollowup) wantsImage = true;
    var wantsM = wantsImage || wantsVideo || wantsAudio || wantsSpeech;
    var smartW = detectSmartJobIntent(content);

    /* Pedido misto (ex.: imagem + planilha/PDF): gera mídia primeiro, depois ficheiros — mesmo fluxo que texto. */
    if (smartW && wantsM) {
      var kindC = wantsImage
        ? "image"
        : wantsVideo
          ? "video"
          : wantsSpeech
            ? "speech"
            : "audio";
      var labelC =
        kindC === "image"
          ? "imagem"
          : kindC === "video"
            ? "video"
            : kindC === "speech"
              ? "voz"
              : "audio";
      var userMsgC = { role: "user", content: content, timestamp: timeLabel() };
      var genLabelC = mediaGenPlaceholderLabel(kindC);
      setMessages(function (prev) {
        return prev.concat([
          userMsgC,
          { role: "assistant", content: genLabelC, timestamp: timeLabel() },
        ]);
      });
      setInput("");
      setAttachments([]);
      setMediaBusy(true);
      try {
        var resultC;
        var provImageC = extractPromptForProvider(content, "image");
        var provVideoC = extractPromptForProvider(content, "video");
        var provOtherC = extractPromptForProvider(content, "text");
        if (kindC === "image") resultC = await generateImage(provImageC || content, token);
        if (kindC === "video") resultC = await generateVideo(provVideoC || content, token);
        if (kindC === "audio") resultC = await generateMusic(provOtherC || content, token);
        if (kindC === "speech") resultC = await generateSpeech(provOtherC || content, token);

        if (kindC === "image" && resultC && resultC.image_base64) {
          var mimeC = resultC.mime || "image/png";
          var imageUrlC = base64ToDisplayUrl(resultC.image_base64, mimeC);
          setMessages(function (prev) {
            var p = prev.slice();
            p[p.length - 1] = {
              role: "assistant",
              content: "Imagem gerada.",
              timestamp: timeLabel(),
              media: { type: "image", url: imageUrlC },
            };
            return p;
          });
        } else if (kindC === "image" && resultC && (resultC.url || resultC.image_url)) {
          var imgUC = resultC.url || resultC.image_url;
          setMessages(function (prev) {
            var p = prev.slice();
            p[p.length - 1] = {
              role: "assistant",
              content: "Imagem gerada.",
              timestamp: timeLabel(),
              media: { type: "image", url: imgUC },
            };
            return p;
          });
        } else {
          var mediaUrlC =
            (resultC &&
              (resultC.url ||
                resultC.video_url ||
                resultC.audio_url ||
                resultC.file_url ||
                resultC.output_url)) ||
            "";
          if (mediaUrlC) {
            setMessages(function (prev) {
              var p = prev.slice();
              p[p.length - 1] = {
                role: "assistant",
                content:
                  kindC === "video"
                    ? "Vídeo gerado."
                    : kindC === "speech"
                      ? "Fala gerada."
                      : "Áudio gerado.",
                timestamp: timeLabel(),
                media: {
                  type: kindC === "video" ? "video" : "audio",
                  url: mediaUrlC,
                },
              };
              return p;
            });
          } else {
            setMessages(function (prev) {
              var p = prev.slice();
              p[p.length - 1] = {
                role: "assistant",
                content: USER_FACING_TRY_AGAIN,
                timestamp: timeLabel(),
              };
              return p;
            });
          }
        }
      } catch (errC) {
        var msgC = errC instanceof Error ? errC.message : String(errC);
        var netDownC =
          msgC === "Failed to fetch" ||
          msgC.indexOf("NetworkError") !== -1 ||
          msgC.indexOf("Load failed") !== -1;
        setMessages(function (prev) {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content: netDownC ? USER_FACING_CONNECTION : USER_FACING_TRY_AGAIN,
            timestamp: timeLabel(),
          };
          return p;
        });
      } finally {
        setMediaBusy(false);
      }

      setMessages(function (prev) {
        return prev.concat([
          {
            role: "assistant",
            content: "Gerando ficheiros reais (Excel, PDF, …)…",
            timestamp: timeLabel(),
          },
        ]);
      });
      setLoading(true);
      try {
        var assistHybrid = shouldOmitPriorAssistantForSmartExport(content)
          ? ""
          : getLastAssistantExportText(messages) ||
            "[Mídia gerada neste pedido.] " + content.slice(0, 4000);
        var rC = await multimodalSmartExport(content, token, true, assistHybrid);
        if (!rC || !rC.ok) throw new Error((rC && rC.detail) || "Falha");
        var sfC = Array.isArray(rC.files) ? rC.files : [];
        var ttsUC = rC.tts && rC.tts.audio_url;
        setMessages(function (prev) {
          var p = prev.slice();
          if (p.length)
            p[p.length - 1] = {
              role: "assistant",
              content: String(rC.summary || "").trim(),
              timestamp: timeLabel(),
              smartFiles: sfC,
              ttsAudioUrl: ttsUC || undefined,
            };
          return p;
        });
      } catch (eC) {
        var meC = eC instanceof Error ? eC.message : String(eC);
        setMessages(function (prev) {
          var p = prev.slice();
          if (p.length)
            p[p.length - 1] = {
              role: "assistant",
              content: /400|não suportad|inválid/i.test(meC)
                ? "Não reconheci o pedido para gerar ficheiros automaticamente. Tente reformular (planilha, PDF, contrato)."
                : USER_FACING_TRY_AGAIN,
              timestamp: timeLabel(),
            };
          return p;
        });
      } finally {
        setLoading(false);
      }
      return;
    }

    if (smartW) {
      var assistForFiles = shouldOmitPriorAssistantForSmartExport(content)
        ? ""
        : getLastAssistantExportText(messages);
      setMessages(function (prev) {
        return prev.concat([
          { role: "user", content: content, timestamp: timeLabel() },
          {
            role: "assistant",
            content: "Gerando ficheiros reais (Excel, PDF, …)…",
            timestamp: timeLabel(),
          },
        ]);
      });
      setInput("");
      setLoading(true);
      try {
        var r = await multimodalSmartExport(content, token, true, assistForFiles);
        if (!r || !r.ok) throw new Error((r && r.detail) || "Falha");
        var sf = Array.isArray(r.files) ? r.files : [];
        var ttsU = r.tts && r.tts.audio_url;
        setMessages(function (prev) {
          var p = prev.slice();
          if (p.length) p[p.length - 1] = {
            role: "assistant",
            content: String(r.summary || "").trim(),
            timestamp: timeLabel(),
            smartFiles: sf,
            ttsAudioUrl: ttsU || undefined,
          };
          return p;
        });
      } catch (e) {
        var me = e instanceof Error ? e.message : String(e);
        setMessages(function (prev) {
          var p = prev.slice();
          if (p.length)
            p[p.length - 1] = {
              role: "assistant",
              content: /400|não suportad|inválid/i.test(me)
                ? "Não reconheci o pedido para gerar ficheiros automaticamente. Tente: «faz uma planilha financeira e manda» ou «gera um contrato»."
                : USER_FACING_TRY_AGAIN,
              timestamp: timeLabel(),
            };
          return p;
        });
      } finally {
        setLoading(false);
      }
      return;
    }

    // Fluxo especial: texto pedindo mídia chama diretamente o gerador real.
    if (wantsImage || wantsVideo || wantsAudio || wantsSpeech) {
      var kind = wantsImage
        ? "image"
        : wantsVideo
          ? "video"
          : wantsSpeech
            ? "speech"
            : "audio";
      var label =
        kind === "image"
          ? "imagem"
          : kind === "video"
            ? "video"
            : kind === "speech"
              ? "voz"
              : "audio";
      var userMsg = { role: "user", content: content, timestamp: timeLabel() };
      var genLabel = mediaGenPlaceholderLabel(kind);
      setMessages((prev) =>
        prev.concat([
          userMsg,
          {
            role: "assistant",
            content: genLabel,
            timestamp: timeLabel(),
          },
        ])
      );
      setInput("");
      setAttachments([]);
      setMediaBusy(true);
      try {
        var result;
        var provImage = extractPromptForProvider(content, "image");
        var provVideo = extractPromptForProvider(content, "video");
        var provOther = extractPromptForProvider(content, "text");
        if (kind === "image")
          result = await generateImage(provImage || content, token);
        if (kind === "video")
          result = await generateVideo(provVideo || content, token);
        if (kind === "audio") result = await generateMusic(provOther || content, token);
        if (kind === "speech") result = await generateSpeech(provOther || content, token);

        if (kind === "image" && result && result.image_base64) {
          var mime = result.mime || "image/png";
          var imageUrl = base64ToDisplayUrl(result.image_base64, mime);
          setMessages((prev) => {
            var p = prev.slice();
            // substitui o placeholder "Gerando imagem..." pela resposta final com mídia
            p[p.length - 1] = {
              role: "assistant",
              content: "Imagem gerada.",
              timestamp: timeLabel(),
              media: { type: "image", url: imageUrl },
            };
            return p;
          });
          return;
        }

        if (kind === "image" && result && (result.url || result.image_url)) {
          var imgU = result.url || result.image_url;
          setMessages((prev) => {
            var p = prev.slice();
            p[p.length - 1] = {
              role: "assistant",
              content: "Imagem gerada.",
              timestamp: timeLabel(),
              media: { type: "image", url: imgU },
            };
            return p;
          });
          return;
        }

        var mediaUrl =
          (result &&
            (result.url ||
              result.video_url ||
              result.audio_url ||
              result.file_url ||
              result.output_url)) ||
          "";
        if (mediaUrl) {
          setMessages((prev) => {
            var p = prev.slice();
            p[p.length - 1] = {
              role: "assistant",
              content:
                kind === "video"
                  ? "Vídeo gerado."
                  : kind === "speech"
                    ? "Fala gerada."
                    : "Áudio gerado.",
              timestamp: timeLabel(),
              media: {
                type: kind === "video" ? "video" : "audio",
                url: mediaUrl,
              },
            };
            return p;
          });
          return;
        }

        setMessages((prev) => {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content: USER_FACING_TRY_AGAIN,
            timestamp: timeLabel(),
          };
          return p;
        });
      } catch (err) {
        var msg = err instanceof Error ? err.message : String(err);
        var netDown =
          msg === "Failed to fetch" ||
          msg.indexOf("NetworkError") !== -1 ||
          msg.indexOf("Load failed") !== -1;
        setMessages((prev) => {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content: netDown ? USER_FACING_CONNECTION : USER_FACING_TRY_AGAIN,
            timestamp: timeLabel(),
          };
          return p;
        });
      } finally {
        setMediaBusy(false);
      }
      return;
    }

    // Fluxo padrão: chat textual (público ou autenticado).
    var nextHistoryRaw = messages.concat([{ role: "user", content: content, timestamp: timeLabel() }]);
    var nextHistory = applyFocusToHistory(nextHistoryRaw);
    setMessages(nextHistoryRaw);
    setInput("");
    setAttachments([]);
    setLoading(true);
    try {
      var reply;
      var hasMedia = attachments && attachments.length > 0;
      if (token) {
        try {
          if (hasMedia) {
            reply = await chatCompletionWithMedia(token, nextHistory, attachments, currentSessionId);
            setMessages((prev) => prev.concat([{ role: "assistant", content: sanitizeChatText(reply), timestamp: timeLabel() }]));
          } else {
            setMessages((prev) => prev.concat([{ role: "assistant", content: "", timestamp: timeLabel() }]));
            const controller = new AbortController();
            abortRef.current = controller;
            setCanStop(true);
            try {
              await chatCompletionStreamWithFallback(token, nextHistory, function (chunk) {
                setMessages((prev) => {
                  var p = prev.slice();
                  var last = p[p.length - 1];
                  if (last && last.role === "assistant") {
                    p[p.length - 1] = {
                      ...last,
                      content: sanitizeChatStreamDelta(last.content, chunk),
                      timestamp: last.timestamp || timeLabel(),
                    };
                  }
                  return p;
                });
              }, controller.signal, currentSessionId);
              finalizeStreamingAssistantText();
            } finally {
              setCanStop(false);
              abortRef.current = null;
            }
          }
        } catch (authErr) {
          var authMsg = authErr instanceof Error ? authErr.message : String(authErr);
          if (!isAuthErrorMessage(authMsg)) throw authErr;
          try {
            window.localStorage.removeItem("syntexa_token");
          } catch {}
          setAuthToken(null);
          setPlan("anon");
          if (hasMedia) {
            reply = await publicChatWithMedia(nextHistory, attachments);
            setMessages((prev) => prev.concat([{ role: "assistant", content: sanitizeChatText(reply), timestamp: timeLabel() }]));
          } else {
            setMessages((prev) => prev.concat([{ role: "assistant", content: "", timestamp: timeLabel() }]));
            const controller = new AbortController();
            abortRef.current = controller;
            setCanStop(true);
            try {
              await publicChatStreamWithFallback(nextHistory, function (chunk) {
                setMessages((prev) => {
                  var p = prev.slice();
                  var last = p[p.length - 1];
                  if (last && last.role === "assistant") {
                    p[p.length - 1] = {
                      ...last,
                      content: sanitizeChatStreamDelta(last.content, chunk),
                      timestamp: last.timestamp || timeLabel(),
                    };
                  }
                  return p;
                });
              }, controller.signal);
              finalizeStreamingAssistantText();
            } finally {
              setCanStop(false);
              abortRef.current = null;
            }
          }
        }
        try {
          var freshToken = null;
          try {
            freshToken = window.localStorage.getItem("syntexa_token");
          } catch (_) {
            freshToken = null;
          }
          var freshSessionsAny = await listChatSessions(freshToken);
          if (Array.isArray(freshSessionsAny) && freshSessionsAny.length > 0 && !currentSessionId) {
            setCurrentSessionId(freshSessionsAny[0].id);
          }
        } catch {}
        setSessionsRefreshKey(function (n) { return n + 1; });
      } else {
        if (hasMedia) {
          reply = await publicChatWithMedia(nextHistory, attachments);
          setMessages((prev) => prev.concat([{ role: "assistant", content: sanitizeChatText(reply), timestamp: timeLabel() }]));
        } else {
          setMessages((prev) => prev.concat([{ role: "assistant", content: "", timestamp: timeLabel() }]));
          const controller = new AbortController();
          abortRef.current = controller;
          setCanStop(true);
          try {
            await publicChatStreamWithFallback(nextHistory, function (chunk) {
              setMessages((prev) => {
                var p = prev.slice();
                var last = p[p.length - 1];
                if (last && last.role === "assistant") {
                  p[p.length - 1] = {
                    ...last,
                    content: sanitizeChatStreamDelta(last.content, chunk),
                    timestamp: last.timestamp || timeLabel(),
                  };
                }
                return p;
              });
            }, controller.signal);
            finalizeStreamingAssistantText();
          } finally {
            setCanStop(false);
            abortRef.current = null;
          }
        }
      }
    } catch (err) {
      try {
        if (typeof console !== "undefined" && console.error) console.error("[chat]", err);
      } catch (_) {}
      var msg = err instanceof Error ? err.message : String(err);
      var netDown =
        msg === "Failed to fetch" ||
        msg.indexOf("NetworkError") !== -1 ||
        msg.indexOf("Load failed") !== -1;
      var recovered = false;
      try {
        var rt = null;
        try {
          rt = window.localStorage.getItem("syntexa_token");
        } catch (_) {
          rt = null;
        }
        if (rt) {
          var fullRec = await chatCompletion(rt, nextHistory, currentSessionId);
          recovered = true;
          setMessages(function (prev) {
            var p = prev.slice();
            if (p.length && p[p.length - 1].role === "assistant") {
              p[p.length - 1] = {
                ...p[p.length - 1],
                content: sanitizeChatText(fullRec),
                timestamp: timeLabel(),
              };
              return p;
            }
            return prev.concat([{ role: "assistant", content: sanitizeChatText(fullRec), timestamp: timeLabel() }]);
          });
          try {
            var refreshed = await listChatSessions(rt);
            if (Array.isArray(refreshed) && refreshed.length > 0 && !currentSessionId) {
              setCurrentSessionId(refreshed[0].id);
            }
          } catch {}
          setSessionsRefreshKey(function (n) { return n + 1; });
        } else {
          var fullPub = await publicChat(nextHistory);
          recovered = true;
          setMessages(function (prev) {
            var p = prev.slice();
            if (p.length && p[p.length - 1].role === "assistant") {
              p[p.length - 1] = {
                ...p[p.length - 1],
                content: sanitizeChatText(fullPub),
                timestamp: timeLabel(),
              };
              return p;
            }
            return prev.concat([{ role: "assistant", content: sanitizeChatText(fullPub), timestamp: timeLabel() }]);
          });
        }
      } catch (re) {
        try {
          if (typeof console !== "undefined" && console.error) console.error("[chat recover]", re);
        } catch (_) {}
      }
      if (!recovered) {
        setMessages(function (prev) {
          var p2 = prev.slice();
          if (p2.length && p2[p2.length - 1].role === "assistant") {
            p2[p2.length - 1] = {
              ...p2[p2.length - 1],
              content: netDown ? USER_FACING_CONNECTION : USER_FACING_TRY_AGAIN,
              timestamp: timeLabel(),
            };
            return p2;
          }
          return prev.concat([
            {
              role: "assistant",
              content: netDown ? USER_FACING_CONNECTION : USER_FACING_TRY_AGAIN,
              timestamp: timeLabel(),
            },
          ]);
        });
      }
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage() {
    if (sendBusyRef.current) return;
    var content = input.trim();
    if (!content || loading || mediaBusy || fileExportBusy) return;
    var _now = typeof Date !== "undefined" ? Date.now() : 0;
    if (_now && _now - lastSendAtRef.current < 400) return;
    lastSendAtRef.current = _now;

    var userMessages = messages.filter((m) => m.role === "user").length;
    var maxForPlan =
      plan === "anon"
        ? 120
        : plan === "free"
          ? 200
          : plan === "basic"
            ? 500
            : 999999;
    if (userMessages >= maxForPlan) {
      setMessages((prev) =>
        prev.concat([
          {
            role: "assistant",
            content:
              "Limite de mensagens do modo atual foi atingido (uso mensal ou diário, conforme o plano). Faça login com conta gratuita ou paga para limites maiores, ou aguarde a renovação do período.",
            timestamp: timeLabel(),
          },
        ])
      );
      return;
    }

    sendBusyRef.current = true;
    try {
      await processOutgoingUserContent(content);
    } finally {
      sendBusyRef.current = false;
    }
  }

  /** Voz: mesmo pipeline que Enter (mídia + ficheiros + chat), sem /voice/conversation no servidor. */
  async function submitVoiceTranscript(raw) {
    var content = String(raw || "").trim();
    if (!content || loading || mediaBusy || fileExportBusy) return;
    if (sendBusyRef.current) return;
    var userMessages = messages.filter((m) => m.role === "user").length;
    var maxForPlan =
      plan === "anon"
        ? 120
        : plan === "free"
          ? 200
          : plan === "basic"
            ? 500
            : 999999;
    if (userMessages >= maxForPlan) {
      setMessages((prev) =>
        prev.concat([
          {
            role: "assistant",
            content:
              "Limite de mensagens do modo atual foi atingido (uso mensal ou diário, conforme o plano). Faça login com conta gratuita ou paga para limites maiores, ou aguarde a renovação do período.",
            timestamp: timeLabel(),
          },
        ])
      );
      return;
    }
    sendBusyRef.current = true;
    try {
      await processOutgoingUserContent(content);
    } finally {
      sendBusyRef.current = false;
    }
  }

  /**
   * Resposta de POST /v1/multimodal/voice/conversation (STT + intenções no servidor + TTS).
   * Mantido completo: imagem, vídeo, áudio, smart files, texto. Usar com AudioRecorder pipelineMode="server".
   * Padrão no UI: pipelineMode="chat" (STT → submitVoiceTranscript = mesmo fluxo que digitar).
   */
  function applyMultimodalVoiceServerResult(data) {
    var tr = (data && data.transcript) || "";
    var reply = (data && data.reply) || "";
    var tts = data && data.tts;
    var ttsU = tts && tts.audio_url;
    var files = (data && data.files) || [];
    var smartFs = files.length ? files : undefined;
    var imgB64 = data && data.image_base64;
    var imgMime = (data && data.mime) || "image/png";
    var imgRemote = data && data.image_url;
    var vidU =
      (data && data.video_url) ||
      (data && data.media && data.media.type === "video" && data.media.url);
    var musU =
      (data && data.audio_url) ||
      (data && data.media && data.media.type === "audio" && data.media.url);

    if (imgB64) {
      var imageUrl = base64ToDisplayUrl(imgB64, imgMime);
      setMessages(function (prev) {
        return prev.concat([
          { role: "user", content: tr || "(áudio)", timestamp: timeLabel() },
          {
            role: "assistant",
            content: "Imagem gerada.",
            timestamp: timeLabel(),
            media: { type: "image", url: imageUrl },
            ttsAudioUrl: ttsU || undefined,
          },
        ]);
      });
      return;
    }
    if (imgRemote) {
      setMessages(function (prev) {
        return prev.concat([
          { role: "user", content: tr || "(áudio)", timestamp: timeLabel() },
          {
            role: "assistant",
            content: "Imagem gerada.",
            timestamp: timeLabel(),
            media: { type: "image", url: String(imgRemote) },
            ttsAudioUrl: ttsU || undefined,
          },
        ]);
      });
      return;
    }
    if (vidU) {
      setMessages(function (prev) {
        return prev.concat([
          { role: "user", content: tr || "(áudio)", timestamp: timeLabel() },
          {
            role: "assistant",
            content: sanitizeChatText(reply) || "Vídeo gerado.",
            timestamp: timeLabel(),
            media: { type: "video", url: String(vidU) },
            ttsAudioUrl: ttsU || undefined,
          },
        ]);
      });
      return;
    }
    if (musU) {
      setMessages(function (prev) {
        return prev.concat([
          { role: "user", content: tr || "(áudio)", timestamp: timeLabel() },
          {
            role: "assistant",
            content: sanitizeChatText(reply) || "Áudio gerado.",
            timestamp: timeLabel(),
            media: { type: "audio", url: String(musU) },
            ttsAudioUrl: ttsU || undefined,
          },
        ]);
      });
      return;
    }
    if (smartFs) {
      setMessages(function (prev) {
        return prev.concat([
          { role: "user", content: tr || "(áudio)", timestamp: timeLabel() },
          {
            role: "assistant",
            content: sanitizeChatText(reply),
            timestamp: timeLabel(),
            smartFiles: smartFs,
            ttsAudioUrl: ttsU || undefined,
          },
        ]);
      });
      return;
    }
    setMessages(function (prev) {
      return prev.concat([
        { role: "user", content: tr || "(áudio)", timestamp: timeLabel() },
        {
          role: "assistant",
          content: sanitizeChatText(reply),
          timestamp: timeLabel(),
          ttsAudioUrl: ttsU || undefined,
        },
      ]);
    });
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (loading || mediaBusy || fileExportBusy) return;
      sendMessage();
    }
  }

  function handleNewConversation() {
    setMessages([
      {
        role: "assistant",
        content: isEnglishUi
          ? "Hello, this is Syntexa. How can I help you?"
          : "Olá, aqui é a Syntexa. Em que posso te ajudar?",
        timestamp: "",
      },
    ]);
    setAttachments([]);
    setCurrentSessionId(null);
  }

  function handleFilesChange(e) {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setAttachments(files);
  }

  function openFilePicker() {
    var inputEl = document.getElementById("syntexa-file-input");
    if (inputEl) inputEl.click();
  }

  function applyQuickAction(kind) {
    setShowQuickActions(false);
    if (kind === "upload") {
      openFilePicker();
      return;
    }
    if (kind === "image") {
      setInput("Gere uma imagem com estilo premium sobre: ");
      return;
    }
    if (kind === "web") {
      setInput("Pesquise na web e me traga as fontes sobre: ");
      return;
    }
    if (kind === "deep") {
      setInput("Investigue a fundo este tema e me entregue um plano completo: ");
      return;
    }
    if (kind === "canvas") {
      window.location.href = "/planos";
      return;
    }
    if (kind === "github") {
      if (isAdmin) {
        window.location.href = "/admin/mobile-release";
      } else {
        setInput("Me ajude com versionamento GitHub e pipeline de release para este projeto: ");
      }
      return;
    }
    if (kind === "questionnaire") {
      if (isAdmin) {
        window.location.href = "/admin/institucional";
      } else {
        setInput("Monte um questionário estruturado para coleta de requisitos com clientes: ");
      }
    }
  }

  function handleDragOverChat(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }

  function handleDragLeaveChat(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }

  function handleDropChat(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    var fl = Array.from(e.dataTransfer.files || []);
    if (fl.length > 0) setAttachments(fl);
  }

  async function handleAnalyzeAttachments() {
    if (!attachments.length || multimodalBusy || loading || mediaBusy) return;
    var tok = null;
    try {
      tok = window.localStorage.getItem("syntexa_token");
    } catch (e) {
      tok = null;
    }
    setMultimodalBusy(true);
    try {
      for (var i = 0; i < attachments.length; i++) {
        var file = attachments[i];
        var data = await multimodalAnalyze(file, { deep: false, token: tok });
        var summary = formatMultimodalResult(data);
        setMessages(function (prev) {
          return prev.concat([
            {
              role: "assistant",
            content: sanitizeChatText(summary),
              timestamp: timeLabel(),
            },
          ]);
        });
      }
    } catch (err) {
      setMessages(function (prev) {
        return prev.concat([
          {
            role: "assistant",
            content: USER_FACING_TRY_AGAIN,
            timestamp: timeLabel(),
          },
        ]);
      });
    } finally {
      setMultimodalBusy(false);
    }
  }

  async function handleGenerateMedia(kind) {
    var prompt = input.trim();
    if (!prompt || loading || mediaBusy) return;
    var tok = null;
    try {
      tok = window.localStorage.getItem("syntexa_token");
    } catch (e) {
      tok = null;
    }
    var label =
      kind === "image"
        ? "imagem"
        : kind === "video"
          ? "video"
          : kind === "speech"
            ? "voz"
            : "audio";
    var genLine = mediaGenPlaceholderLabel(kind);
    setMessages((prev) =>
      prev.concat([
        { role: "user", content: "Gerar " + label + ": " + prompt, timestamp: timeLabel() },
        { role: "assistant", content: genLine, timestamp: timeLabel() },
      ])
    );
    setInput("");
    setMediaBusy(true);
    try {
      var result;
      var pImg = extractPromptForProvider(prompt, "image") || prompt;
      var pVid = extractPromptForProvider(prompt, "video") || prompt;
      var pOth = extractPromptForProvider(prompt, "text") || prompt;
      if (kind === "image") result = await generateImage(pImg, tok);
      if (kind === "video") result = await generateVideo(pVid, tok);
      if (kind === "audio") result = await generateMusic(pOth, tok);
      if (kind === "speech") result = await generateSpeech(pOth, tok);

      if (kind === "image" && result && result.image_base64) {
        var mime2 = result.mime || "image/png";
        var imageUrl2 = base64ToDisplayUrl(result.image_base64, mime2);
        setMessages((prev) => {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content: "Imagem gerada.",
            timestamp: timeLabel(),
            media: { type: "image", url: imageUrl2 },
          };
          return p;
        });
        return;
      }

      if (kind === "image" && result && (result.url || result.image_url)) {
        var imgU2 = result.url || result.image_url;
        setMessages((prev) => {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content: "Imagem gerada.",
            timestamp: timeLabel(),
            media: { type: "image", url: imgU2 },
          };
          return p;
        });
        return;
      }

      var mediaUrl =
        (result && (result.url || result.video_url || result.audio_url || result.file_url || result.output_url)) ||
        "";
      if (mediaUrl) {
        setMessages((prev) => {
          var p = prev.slice();
          p[p.length - 1] = {
            role: "assistant",
            content:
              kind === "video"
                ? "Vídeo gerado."
                : kind === "speech"
                  ? "Fala gerada."
                  : "Áudio gerado.",
            timestamp: timeLabel(),
            media: { type: kind === "video" ? "video" : "audio", url: mediaUrl },
          };
          return p;
        });
        return;
      }

      setMessages((prev) => {
        var p = prev.slice();
        p[p.length - 1] = {
          role: "assistant",
          content: "Não consegui gerar o arquivo de mídia agora. Tente novamente em alguns instantes.",
          timestamp: timeLabel(),
        };
        return p;
      });
    } catch (err) {
      var raw = err instanceof Error ? err.message : String(err);
      var netDown =
        raw === "Failed to fetch" ||
        raw.indexOf("NetworkError") !== -1 ||
        raw.indexOf("Load failed") !== -1;
      setMessages((prev) => {
        var p = prev.slice();
        p[p.length - 1] = {
          role: "assistant",
          content: netDown ? USER_FACING_CONNECTION : USER_FACING_TRY_AGAIN,
          timestamp: timeLabel(),
        };
        return p;
      });
    } finally {
      setMediaBusy(false);
    }
  }

  function exportAssistantFileForMessage(kind, text) {
    var tok = null;
    try {
      tok = window.localStorage.getItem("syntexa_token");
    } catch (e) {
      tok = null;
    }
    setFileExportBusy(true);
    (async function () {
      try {
        await downloadStructuredExport(kind, text, tok || undefined);
      } catch (e) {
        setMessages(function (prev) {
          return prev.concat([
            {
              role: "assistant",
              content: USER_FACING_TRY_AGAIN,
              timestamp: timeLabel(),
            },
          ]);
        });
      } finally {
        setFileExportBusy(false);
      }
    })();
  }

  function listenAssistantForMessage(globalIdx, text) {
    var tok = null;
    try {
      tok = window.localStorage.getItem("syntexa_token");
    } catch (e) {
      tok = null;
    }
    setTtsBusyIdx(globalIdx);
    (async function () {
      try {
        var r = await generateSpeech(plainTextForExport(text).slice(0, 8000), tok);
        var url = r && r.audio_url;
        if (url) {
          setMessages(function (prev) {
            var p = prev.slice();
            if (p[globalIdx])
              p[globalIdx] = Object.assign({}, p[globalIdx], { ttsAudioUrl: url });
            return p;
          });
        }
      } catch (e) {
        setMessages(function (prev) {
          return prev.concat([
            {
              role: "assistant",
              content: USER_FACING_TRY_AGAIN,
              timestamp: timeLabel(),
            },
          ]);
        });
      } finally {
        setTtsBusyIdx(null);
      }
    })();
  }

  function downloadAttachmentFile(file) {
    try {
      var u = URL.createObjectURL(file);
      var a = document.createElement("a");
      a.href = u;
      a.download = file.name || "anexo";
      a.click();
      setTimeout(function () {
        try {
          URL.revokeObjectURL(u);
        } catch (e2) {}
      }, 2500);
    } catch (e) {}
  }

  var visible = messages.filter((m) => m.role !== "system");
  var lastVisible = visible.length ? visible[visible.length - 1] : null;
  var waitingFirstStreamToken =
    loading &&
    !fileExportBusy &&
    !mediaBusy &&
    lastVisible &&
    lastVisible.role === "assistant" &&
    !String(lastVisible.content || "").trim();
  var showTyping = Boolean(waitingFirstStreamToken);

  function handleStop() {
    try {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    } catch (e) {}
    setCanStop(false);
  }

  return React.createElement(
    ChatLayout,
    {
      onNewConversation: handleNewConversation,
      sessionsRefreshKey: sessionsRefreshKey,
      onSelectSession: async function (sessionId) {
        try {
          let token = null;
          try {
            token = window.localStorage.getItem("syntexa_token");
          } catch {
            token = null;
          }
          if (!token) return;
          const msgs = await getChatSessionMessages(sessionId, token);
          if (!Array.isArray(msgs)) return;
          const mapped = msgs.map(function (m) {
            return {
              role: m.role,
              content: sanitizeChatText(m.content),
              timestamp: formatSessionTimestamp(m.created_at),
            };
          });
          setCurrentSessionId(sessionId);
          setMessages(mapped);
          setAttachments([]);
        } catch (e) {
          // ignora erro de histórico para não quebrar o chat
        }
      },
    },
    React.createElement("div", { className: "flex min-h-0 w-full max-w-full flex-1 flex-col overflow-hidden" },
      React.createElement(DesktopDevPanel, null),
      focusMode
        ? React.createElement(
            "div",
            { className: "mx-auto mt-1 mb-2 w-full max-w-3xl rounded-xl border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs text-cyan-900" },
            "Modo focado ativo: ",
            focusMode === "bank" ? "Banco & Finanças" :
            focusMode === "agro" ? "Agro" :
            focusMode === "tax" ? "Impostos / Receita" :
            focusMode === "sales_whatsapp" ? "Vendas WhatsApp" : "Especializado",
            ". As respostas priorizam execução prática nesse domínio."
          )
        : null,
      React.createElement("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto overflow-x-hidden overscroll-contain px-3 py-4 sm:px-8 sm:py-5" },
        React.createElement("div", { className: "mx-auto flex w-full max-w-3xl flex-col gap-4" },
          visible.map((m, idx) => {
            var hideEmptyStreamingSlot =
              loading &&
              !fileExportBusy &&
              !mediaBusy &&
              m.role === "assistant" &&
              !String(m.content || "").trim() &&
              idx === visible.length - 1;
            if (hideEmptyStreamingSlot) return null;
            var safeContent = sanitizeChatText(m.content || "");
            var globalIdx = messages.indexOf(m);
            var cn = m.role === "user" ? "syntexa-bubble-user ml-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed break-words" : "syntexa-bubble-assistant mr-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed break-words";
            return React.createElement(motion.div, { key: idx, initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0.3, delay: idx * 0.03 },
              className: cn + " rounded-2xl mb-3 px-3 py-2 sm:px-5 sm:py-4 max-w-[98vw] sm:max-w-[70%] font-[system-ui,-apple-system,'SF Pro Display','Segoe UI',sans-serif] text-[15px] leading-relaxed" },
              React.createElement("div", { className: "flex items-center justify-between mb-1.5" },
                React.createElement("span", { className: "text-[12px] font-semibold text-zinc-400" }, m.role === "user" ? "Você" : "Syntexa"),
                m.timestamp && React.createElement("span", { className: "text-[11px] text-zinc-400 ml-2" }, m.timestamp)
              ),
              (m.role === "assistant" && isAssistantPlaceholderContent(m.content))
                ? isImagePlaceholderContent(m.content)
                  ? React.createElement(ImageGenerationPlaceholder, { label: safeContent })
                  : React.createElement(
                      "div",
                      { className: "flex items-center gap-2 whitespace-pre-wrap" },
                      React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true }),
                      React.createElement("span", null, safeContent)
                    )
                : m.role === "assistant"
                  ? React.createElement(ChatRichContent, { text: safeContent })
                  : React.createElement("p", { className: "whitespace-pre-wrap" }, safeContent),
              m.role === "assistant" &&
                m.smartFiles &&
                m.smartFiles.length > 0 &&
                React.createElement(
                  "div",
                  { className: "mt-2 space-y-2" },
                  React.createElement(
                    "p",
                    { className: "text-xs font-medium text-emerald-800 inline-flex items-center gap-1.5" },
                    React.createElement(CheckCircleIcon, null),
                    "Arquivo criado com sucesso"
                  ),
                  React.createElement(
                    "div",
                    { className: "flex flex-wrap gap-1.5" },
                  m.smartFiles.map(function (f, fi) {
                    return React.createElement(
                      "button",
                      {
                        type: "button",
                        key: "sf-" + fi,
                        className:
                          "rounded-lg border border-emerald-600/80 bg-emerald-50 px-2 py-1 text-[10px] font-medium text-emerald-950 hover:bg-emerald-100",
                        onClick: function () {
                          (async function () {
                            try {
                              var tok = null;
                              try {
                                tok = window.localStorage.getItem("syntexa_token");
                              } catch (e0) {
                                tok = null;
                              }
                              if (f.data_base64) {
                                var raw = atob(String(f.data_base64 || ""));
                                var arr = new Uint8Array(raw.length);
                                for (var bi = 0; bi < raw.length; bi++) arr[bi] = raw.charCodeAt(bi);
                                var blob = new Blob([arr], {
                                  type: (f.mime || "application/octet-stream").split(";")[0].trim(),
                                });
                                var u = URL.createObjectURL(blob);
                                var a = document.createElement("a");
                                a.href = u;
                                a.download = f.filename || "syntexa-download";
                                a.click();
                                setTimeout(function () {
                                  try {
                                    URL.revokeObjectURL(u);
                                  } catch (e2) {}
                                }, 2500);
                                return;
                              }
                              if (f.download_url) {
                                var hdr = {};
                                if (tok) hdr.Authorization = "Bearer " + tok;
                                var r = await fetch(absoluteApiFileUrl(f.download_url), { headers: hdr });
                                if (!r.ok) throw new Error("download");
                                var b = await r.blob();
                                var u2 = URL.createObjectURL(b);
                                var a2 = document.createElement("a");
                                a2.href = u2;
                                a2.download = f.filename || "syntexa-download";
                                a2.click();
                                setTimeout(function () {
                                  try {
                                    URL.revokeObjectURL(u2);
                                  } catch (e3) {}
                                }, 2500);
                              }
                            } catch (err) {}
                          })();
                        },
                      },
                      React.createElement(
                        "span",
                        { className: "inline-flex items-center gap-1.5" },
                        React.createElement(DownloadIcon, null),
                        downloadLabelForSmartFile(f)
                      )
                    );
                  })
                )
              ),
              m.role === "assistant" &&
                !isAssistantPlaceholderContent(m.content) &&
                String(safeContent || "").trim() &&
                globalIdx >= 0 &&
                !(m.smartFiles && m.smartFiles.length) &&
                React.createElement(
                  "div",
                  { className: "mt-2 flex flex-wrap gap-1.5" },
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      disabled: fileExportBusy,
                      className:
                        "rounded-lg border border-zinc-300 bg-white px-2 py-1 text-[10px] text-zinc-800 hover:bg-zinc-50 disabled:opacity-40",
                      onClick: function () {
                        exportAssistantFileForMessage("pdf", toExportReadyText(m.content || ""));
                      },
                    },
                    "PDF"
                  ),
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      disabled: fileExportBusy,
                      className:
                        "rounded-lg border border-zinc-300 bg-white px-2 py-1 text-[10px] text-zinc-800 hover:bg-zinc-50 disabled:opacity-40",
                      onClick: function () {
                        exportAssistantFileForMessage("xlsx", toExportReadyText(m.content || ""));
                      },
                    },
                    "Excel"
                  ),
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      disabled: fileExportBusy,
                      className:
                        "rounded-lg border border-zinc-300 bg-white px-2 py-1 text-[10px] text-zinc-800 hover:bg-zinc-50 disabled:opacity-40",
                      onClick: function () {
                        exportAssistantFileForMessage("docx", toExportReadyText(m.content || ""));
                      },
                    },
                    "Word"
                  ),
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      disabled: fileExportBusy,
                      className:
                        "rounded-lg border border-zinc-300 bg-white px-2 py-1 text-[10px] text-zinc-800 hover:bg-zinc-50 disabled:opacity-40",
                      onClick: function () {
                        exportAssistantFileForMessage("csv", toExportReadyText(m.content || ""));
                      },
                    },
                    "CSV"
                  ),
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      disabled: fileExportBusy,
                      className:
                        "rounded-lg border border-zinc-300 bg-white px-2 py-1 text-[10px] text-zinc-800 hover:bg-zinc-50 disabled:opacity-40",
                      onClick: function () {
                        exportAssistantFileForMessage("txt", toExportReadyText(m.content || ""));
                      },
                    },
                    "TXT"
                  ),
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      disabled: ttsBusyIdx === globalIdx,
                      className:
                        "rounded-lg border border-zinc-300 bg-white px-2 py-1 text-[10px] text-zinc-800 hover:bg-zinc-50 disabled:opacity-40",
                      onClick: function () {
                        listenAssistantForMessage(globalIdx, m.content || "");
                      },
                    },
                    ttsBusyIdx === globalIdx ? "Voz…" : "Ouvir"
                  )
                ),
              m.role === "assistant" &&
                m.ttsAudioUrl &&
                React.createElement("audio", {
                  src: m.ttsAudioUrl,
                  controls: true,
                  className: "mt-2 w-full max-w-full",
                }),
              m.media && m.media.type === "image" &&
                React.createElement(ChatImage, {
                  src: m.media.url,
                  alt: "Imagem gerada",
                }),
              m.media && m.media.type === "image" &&
                React.createElement(
                  "a",
                  {
                    href: m.media.url,
                    download: "",
                    target: "_blank",
                    rel: "noreferrer",
                    className:
                      "mt-2 inline-flex items-center text-xs font-medium text-emerald-700 hover:text-emerald-900 underline decoration-emerald-400/70",
                  },
                  "Baixar imagem"
                ),
              m.media && m.media.type === "video" &&
                (String(m.media.url || "").startsWith("data:image/")
                  ? React.createElement("img", {
                      src: m.media.url,
                      alt: "Video gerado",
                      className: "mt-3 max-h-[420px] w-full rounded-xl border border-zinc-200 object-contain",
                    })
                  : React.createElement("video", {
                      src: m.media.url,
                      controls: true,
                      className: "mt-3 max-h-[420px] w-full rounded-xl border border-zinc-200",
                    })),
              m.media && m.media.type === "video" &&
                !String(m.media.url || "").startsWith("data:image/") &&
                React.createElement(
                  "a",
                  {
                    href: m.media.url,
                    download: "",
                    target: "_blank",
                    rel: "noreferrer",
                    className:
                      "mt-2 inline-flex items-center text-xs font-medium text-emerald-700 hover:text-emerald-900 underline decoration-emerald-400/70",
                  },
                  "Baixar vídeo"
                ),
              m.media && m.media.type === "audio" &&
                React.createElement("audio", {
                  src: m.media.url,
                  controls: true,
                  className: "mt-3 w-full",
                }),
              m.media && m.media.type === "audio" &&
                React.createElement(
                  "a",
                  {
                    href: m.media.url,
                    download: "",
                    target: "_blank",
                    rel: "noreferrer",
                    className:
                      "mt-2 inline-flex items-center text-xs font-medium text-emerald-700 hover:text-emerald-900 underline decoration-emerald-400/70",
                  },
                  "Baixar áudio"
                ));
          }),
          showTyping && React.createElement(motion.div, { key: "typing-once", initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25 }, className: "syntexa-bubble-assistant mr-auto max-w-[85%] sm:max-w-[80%] rounded-[18px] px-4 py-3 sm:px-5 sm:py-4" },
            React.createElement("div", { className: "mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-zinc-600" }, "Syntexa"),
            React.createElement("div", { className: "flex items-center gap-2 text-sm text-zinc-700" },
              React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true }),
              React.createElement("span", null, "Processando resposta..."))),
          visible.length === 0 &&
            React.createElement(
              "div",
              { className: "mt-10 text-center text-sm text-zinc-400" },
              "Pergunte qualquer coisa sobre estudos, trabalho ou negócio e deixe a Syntexa destravar o próximo passo com você."
            ),
          React.createElement("div", { ref: messagesEndRef, "aria-hidden": true }))
        ),
      React.createElement(
        "div",
        {
          className:
            "shrink-0 z-30 overflow-visible border-t border-zinc-200 bg-[#f7f7fa] px-3 py-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] sm:px-8 sm:py-4" +
            (dragOver ? " ring-2 ring-emerald-500/50 ring-inset" : ""),
          onDragOver: handleDragOverChat,
          onDragLeave: handleDragLeaveChat,
          onDrop: handleDropChat,
        },
        React.createElement(
          "div",
          { className: "mx-auto flex w-full max-w-3xl flex-col gap-3" },
          React.createElement(
            "div",
            { className: "min-w-0 w-full overflow-visible text-[11px] text-zinc-500" },
            React.createElement(FileExportMenu, {
              token: authToken,
              className: "",
              getExportText: function () {
                return getLastAssistantExportText(messages);
              },
              voicePipelineMode:
                typeof process !== "undefined" &&
                process.env &&
                String(process.env.NEXT_PUBLIC_VOICE_PIPELINE || "")
                  .toLowerCase() === "server"
                  ? "server"
                  : "chat",
              onVoiceSubmitChat: function (transcript) {
                return submitVoiceTranscript(transcript);
              },
              onVoicePipelineResult: applyMultimodalVoiceServerResult,
              onVoiceError: function (err) {
                setMessages(function (prev) {
                  return prev.concat([
                    {
                      role: "assistant",
                      content: String(err || USER_FACING_TRY_AGAIN),
                      timestamp: timeLabel(),
                    },
                  ]);
                });
              },
            }),
            attachments.length > 0 &&
              React.createElement(
                "button",
                {
                  type: "button",
                  disabled: multimodalBusy || loading || mediaBusy,
                  onClick: function () {
                    void handleAnalyzeAttachments();
                  },
                  className:
                    "rounded-lg border border-violet-400/60 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-950 hover:bg-violet-100 disabled:opacity-40",
                },
                multimodalBusy ? "A analisar…" : "Analisar ficheiros"
              )
          ),
          attachments.length > 0 &&
            React.createElement(
              "div",
              { className: "flex flex-wrap items-center gap-2 text-xs text-zinc-700" },
              attachments.map((file) =>
                React.createElement(
                  "span",
                  {
                    key: file.name + file.size,
                    className:
                      "inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1.5",
                  },
                  React.createElement("span", { className: "h-2 w-2 shrink-0 rounded-full bg-emerald-400" }),
                  React.createElement("span", { className: "max-w-[200px] truncate" }, file.name),
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      className:
                        "shrink-0 text-[11px] font-medium text-emerald-700 underline decoration-emerald-400/70 hover:text-emerald-900",
                      onClick: function () {
                        downloadAttachmentFile(file);
                      },
                    },
                    "Baixar"
                  )
                )
              )
            ),
          React.createElement(
            "div",
            { className: "flex flex-col gap-2" },
            focusMode &&
              React.createElement(
                "div",
                { className: "flex flex-wrap gap-2" },
                getFocusComposerActions(focusMode).map(function (item) {
                  return React.createElement(
                    "div",
                    {
                      key: item[0],
                      className: "inline-flex items-center gap-1",
                    },
                    React.createElement(
                      "button",
                      {
                        type: "button",
                        onClick: function () {
                          setInput(item[1]);
                        },
                        className:
                          "rounded-full border border-cyan-300 bg-cyan-50 px-3 py-1 text-[11px] font-medium text-cyan-900 hover:bg-cyan-100",
                      },
                      item[0]
                    ),
                    React.createElement(
                      "button",
                      {
                        type: "button",
                        onClick: function () {
                          void runFocusedQuickPrompt(item[1]);
                        },
                        disabled: loading || mediaBusy || fileExportBusy,
                        title: "Executar direto",
                        className:
                          "rounded-full border border-emerald-300 bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-900 hover:bg-emerald-100 disabled:opacity-40",
                      },
                      "Vai"
                    )
                  );
                })
              ),
            React.createElement(
              "div",
              { className: "relative flex gap-2 items-end" },
              React.createElement("input", {
                id: "syntexa-file-input",
                type: "file",
                multiple: true,
                accept:
                  "image/*,video/*,audio/*,application/pdf,.pdf,.txt,.md,.json,.csv,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,.xlsx",
                className: "hidden",
                onChange: handleFilesChange,
              }),
              showQuickActions &&
                React.createElement(
                  "div",
                  {
                    className:
                      "absolute bottom-12 left-0 z-40 w-64 rounded-2xl border border-zinc-200 bg-white p-2 shadow-2xl",
                  },
                  [
                    ["upload", "Carregar fotos e ficheiros"],
                    ["image", "Criar imagem"],
                    ["web", "Pesquisar na web"],
                    ["deep", "Investigar a fundo"],
                    ["canvas", "Canvas"],
                  ]
                    .concat(
                      isAdmin
                        ? [
                            ["github", "GitHub / release"],
                            ["questionnaire", "Questionários"],
                          ]
                        : []
                    )
                    .map(function (item) {
                    return React.createElement(
                      "button",
                      {
                        key: item[0],
                        type: "button",
                        onClick: function () {
                          applyQuickAction(item[0]);
                        },
                        className:
                          "flex w-full items-center rounded-xl px-3 py-2 text-left text-xs text-zinc-700 hover:bg-zinc-100",
                      },
                      item[1]
                    );
                  })
                ),
              React.createElement(
                "button",
                {
                  type: "button",
                  "aria-label": "Abrir ações rápidas",
                  onClick: function () {
                    setShowQuickActions(function (v) {
                      return !v;
                    });
                  },
                  className:
                    "shrink-0 flex items-center justify-center w-10 h-10 rounded-xl border border-zinc-200 bg-white text-zinc-800 hover:bg-zinc-50 text-lg leading-none",
                },
                "+"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  "aria-label": "Anexar arquivo",
                  onClick: function () {
                    openFilePicker();
                  },
                  className:
                    "syntexa-attach-btn shrink-0 flex items-center justify-center w-10 h-10 rounded-xl border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50",
                },
                React.createElement(IconAttach, null)
              ),
              React.createElement("textarea", {
                value: input,
                onChange: (e) => setInput(e.target.value),
                onKeyDown: handleKeyDown,
                rows: 2,
                placeholder: "Digite sua mensagem...",
                className:
                  "syntexa-input min-h-[44px] max-h-28 flex-1 resize-none rounded-2xl px-4 py-3 text-sm shadow-sm",
              }),
              React.createElement(
                Button,
              { onClick: sendMessage, className: "shrink-0 self-end inline-flex items-center gap-2", disabled: loading || mediaBusy || multimodalBusy },
                loading
                  ? React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true })
                  : React.createElement(IconSend, null),
                loading ? "Enviando" : "Enviar"
              ),
              canStop &&
                React.createElement(
                  Button,
                  {
                    type: "button",
                    variant: "outline",
                    onClick: handleStop,
                    className: "shrink-0 self-end ml-2 border-red-400 text-red-300 hover:bg-red-500/10",
                  },
                  "Parar"
                )
            )
          )
        )
      )
    )
  );
}
