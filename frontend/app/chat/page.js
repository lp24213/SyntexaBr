"use client";
import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ChatLayout } from "../../components/chat-layout";
import { Button } from "../../components/ui/button";
import {
  FileExportMenu,
  plainTextForExport,
  downloadStructuredExport,
} from "../../components/FileExportMenu";
import { AudioRecorder } from "../../components/AudioRecorder";
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
  multimodalAnalyze,
  multimodalSmartExport,
} from "../../lib/api";

/** Detecta pedido de mídia em PT-BR (crie/gere imagem, vídeo, áudio — não só "gere uma imagem"). */
function detectMediaIntent(text) {
  var w = (text || "").toLowerCase();
  var create =
    /\b(crie|criar|gere|gera|desenhe|desenha|faça|faca|fazer|fa[çc]o|elabore|produza|monte|gerem|criem|façam|facam)\b/.test(
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
  return {
    wantsImage:
      (create && img) ||
      /\bgere\s+(uma\s+)?(imagem|foto)\b/.test(w) ||
      /\bgera\s+(uma\s+)?(imagem|foto)\b/.test(w),
    wantsVideo:
      (create && vid) ||
      /\bgere\s+(um\s+)?v(í|i)deo\b/.test(w) ||
      /\bgera\s+(um\s+)?v(í|i)deo\b/.test(w),
    wantsAudio:
      (create && aud) ||
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

function sanitizeChatText(text) {
  return stripBadControlChars(normalizeBrokenPortuguese(maybeFixMojibake(text)));
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
  var verb = /\b(faz|faça|faca|gera|gere|cria|crie|monta|manda|mande|exporta|exporte|envia|preciso|quero|me manda)\b/.test(
    w
  );
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
    return d.toLocaleString("pt-BR", {
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
  React.useEffect(
    function () {
      return function () {
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
  return React.createElement("img", {
    src: src,
    alt: props.alt || "Imagem gerada",
    className: "mt-3 max-h-[420px] w-full rounded-xl border border-zinc-200 object-contain",
    loading: "eager",
    decoding: "async",
    onError: function () {
      setFailed(true);
    },
  });
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
  if (kind === "image") return "Gerando imagem...";
  if (kind === "video") return "Gerando vídeo...";
  if (kind === "speech") return "Gerando voz...";
  return "Gerando áudio...";
}

function IconImage() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", className: "h-4 w-4", fill: "none", "aria-hidden": true },
    React.createElement("rect", { x: "3", y: "4", width: "18", height: "16", rx: "3", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M7 15l3-3 2 2 4-4 1 1v5H7z", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("circle", { cx: "9", cy: "9", r: "1.2", fill: "currentColor" })
  );
}
function IconVideo() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", className: "h-4 w-4", fill: "none", "aria-hidden": true },
    React.createElement("rect", { x: "3", y: "5", width: "14", height: "14", rx: "3", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M17 10l4-2v8l-4-2z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" })
  );
}
function IconAudio() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", className: "h-4 w-4", fill: "none", "aria-hidden": true },
    React.createElement("path", { d: "M5 14h3l4 4V6L8 10H5z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M16 9a4 4 0 010 6", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("path", { d: "M18 6a8 8 0 010 12", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}
function IconMic() {
  return React.createElement(
    "svg",
    { viewBox: "0 0 24 24", className: "h-4 w-4", fill: "none", "aria-hidden": true },
    React.createElement("rect", { x: "9", y: "3", width: "6", height: "11", rx: "3", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M6 11a6 6 0 0012 0M12 17v4M9 21h6", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
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
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Olá, aqui é a Syntexa. Em que posso te ajudar?",
      timestamp: timeLabel(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mediaBusy, setMediaBusy] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [plan, setPlan] = useState("anon");
  const [listening, setListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [canStop, setCanStop] = useState(false);
  const [multimodalBusy, setMultimodalBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [ttsBusyIdx, setTtsBusyIdx] = useState(null);
  const [fileExportBusy, setFileExportBusy] = useState(false);
  const abortRef = useRef(null);
  /** Evita envios concorrentes (duplo clique, Enter+clique). */
  const sendBusyRef = useRef(false);
  var messagesEndRef = useRef(null);

  useEffect(function () {
    try {
      var el = messagesEndRef.current;
      if (el) el.scrollIntoView({ behavior: "smooth", block: "end" });
    } catch (e) {}
  }, [messages, loading, mediaBusy]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) setRecognition(new SpeechRecognition());
  }, []);

  function isAuthErrorMessage(msg) {
    var txt = String(msg || "").toLowerCase();
    return (
      txt.indexOf("não foi possível validar as credenciais") >= 0 ||
      txt.indexOf("not authenticated") >= 0 ||
      txt.indexOf("401") >= 0
    );
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

  async function sendMessage() {
    if (sendBusyRef.current) return;
    var content = input.trim();
    if (!content || loading || mediaBusy || fileExportBusy) return;
    var token = null;
    try {
      token = window.localStorage.getItem("syntexa_token");
    } catch {
      token = null;
    }

    var userMessages = messages.filter((m) => m.role === "user").length;
    var maxForPlan =
      plan === "anon"
        ? 120
        : plan === "free"
          ? 200
          : plan === "basic"
            ? 500
            : 999999; /* medium/master: uso justo, backend aplica limite se necessário */
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
    if (detectSmartJobIntent(content)) {
      setMessages(function (prev) {
        return prev.concat([
          { role: "user", content: content, timestamp: timeLabel() },
          {
            role: "assistant",
            content: "A gerar ficheiros reais (Excel, PDF, …)…",
            timestamp: timeLabel(),
          },
        ]);
      });
      setInput("");
      setLoading(true);
      try {
        var r = await multimodalSmartExport(content, token, true);
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

    var structuredExportKind = detectStructuredFileExportIntent(content);
    if (structuredExportKind) {
      var lastAsst2 = "";
      for (var ai2 = messages.length - 1; ai2 >= 0; ai2--) {
        var am2 = messages[ai2];
        if (
          am2 &&
          am2.role === "assistant" &&
          am2.content &&
          !/^Gerando\s/i.test(String(am2.content))
        ) {
          lastAsst2 = am2.content;
          break;
        }
      }
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
        "A gerar " + (exportLabels[structuredExportKind] || "ficheiro") + "…";
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

    // Fluxo especial: texto pedindo mídia chama diretamente o gerador real.
    if (imageCorrectionFollowup) wantsImage = true;
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
    var nextHistory = messages.concat([{ role: "user", content: content, timestamp: timeLabel() }]);
    setMessages(nextHistory);
    setInput("");
    setAttachments([]);
    setLoading(true);
    try {
      var reply;
      var hasMedia = attachments && attachments.length > 0;
      if (token) {
        try {
          if (hasMedia) {
            reply = await chatCompletionWithMedia(token, nextHistory, attachments);
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
                      content: sanitizeChatText(last.content + chunk),
                      timestamp: last.timestamp || timeLabel(),
                    };
                  }
                  return p;
                });
              }, controller.signal);
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
                      content: sanitizeChatText(last.content + chunk),
                      timestamp: last.timestamp || timeLabel(),
                    };
                  }
                  return p;
                });
              }, controller.signal);
            } finally {
              setCanStop(false);
              abortRef.current = null;
            }
          }
        }
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
                    content: sanitizeChatText(last.content + chunk),
                    timestamp: last.timestamp || timeLabel(),
                  };
                }
                return p;
              });
            }, controller.signal);
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
          var fullRec = await chatCompletion(rt, nextHistory);
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
    } finally {
      sendBusyRef.current = false;
    }
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
        content: "Olá, aqui é a Syntexa. Em que posso te ajudar?",
        timestamp: timeLabel(),
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

  function toggleVoice() {
    if (!recognition) return;
    if (listening) {
      recognition.stop();
      setListening(false);
      return;
    }
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "pt-BR";
    recognition.onresult = function (e) {
      var t = (e.results[0] && e.results[0][0]) ? e.results[0][0].transcript : "";
      if (t) setInput(function (prev) { return (prev ? prev + " " : "") + t; });
    };
    recognition.onend = function () { setListening(false); };
    recognition.start();
    setListening(true);
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
  var lastIsMediaPlaceholder =
    lastVisible &&
    lastVisible.role === "assistant" &&
    /^Gerando\s/i.test(String(lastVisible.content || ""));
  var showTyping =
    loading &&
    !fileExportBusy &&
    visible.length > 0 &&
    !lastIsMediaPlaceholder &&
    lastVisible &&
    lastVisible.role === "user";

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
      React.createElement("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto overflow-x-hidden overscroll-contain px-3 py-4 sm:px-8 sm:py-5" },
        React.createElement("div", { className: "mx-auto flex w-full max-w-3xl flex-col gap-4" },
          visible.map((m, idx) => {
            var safeContent = sanitizeChatText(m.content || "");
            var globalIdx = messages.indexOf(m);
            var cn = m.role === "user" ? "syntexa-bubble-user ml-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed break-words" : "syntexa-bubble-assistant mr-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed break-words";
            return React.createElement(motion.div, { key: idx, initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0.3, delay: idx * 0.03 },
              className: cn + " rounded-2xl mb-3 px-3 py-2 sm:px-5 sm:py-4 max-w-[98vw] sm:max-w-[70%] font-[system-ui,-apple-system,'SF Pro Display','Segoe UI',sans-serif] text-[15px] leading-relaxed" },
              React.createElement("div", { className: "flex items-center justify-between mb-1.5" },
                React.createElement("span", { className: "text-[12px] font-semibold text-zinc-400" }, m.role === "user" ? "Você" : "Syntexa"),
                m.timestamp && React.createElement("span", { className: "text-[11px] text-zinc-400 ml-2" }, m.timestamp)
              ),
              (m.role === "assistant" && /^Gerando\s/i.test(String(safeContent || "")))
                ? React.createElement(
                    "div",
                    { className: "flex items-center gap-2 whitespace-pre-wrap" },
                    React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true }),
                    React.createElement("span", null, safeContent)
                  )
                : React.createElement("p", { className: "whitespace-pre-wrap" }, safeContent),
              m.role === "assistant" &&
                m.smartFiles &&
                m.smartFiles.length > 0 &&
                React.createElement(
                  "div",
                  { className: "mt-2 flex flex-wrap gap-1.5" },
                  m.smartFiles.map(function (f, fi) {
                    return React.createElement(
                      "button",
                      {
                        type: "button",
                        key: "sf-" + fi,
                        className:
                          "rounded-lg border border-emerald-600/80 bg-emerald-50 px-2 py-1 text-[10px] font-medium text-emerald-950 hover:bg-emerald-100",
                        onClick: function () {
                          try {
                            var raw = atob(String(f.data_base64 || ""));
                            var arr = new Uint8Array(raw.length);
                            for (var bi = 0; bi < raw.length; bi++) arr[bi] = raw.charCodeAt(bi);
                            var blob = new Blob([arr], {
                              type: f.mime || "application/octet-stream",
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
                          } catch (err) {}
                        },
                      },
                      "Baixar " + String(f.kind || "ficheiro").toUpperCase()
                    );
                  })
                ),
              m.role === "assistant" &&
                !/^Gerando\s/i.test(String(safeContent || "")) &&
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
                        exportAssistantFileForMessage("pdf", m.content || "");
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
                        exportAssistantFileForMessage("xlsx", m.content || "");
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
                        exportAssistantFileForMessage("docx", m.content || "");
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
                        exportAssistantFileForMessage("csv", m.content || "");
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
                        exportAssistantFileForMessage("txt", m.content || "");
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
            "shrink-0 z-30 border-t border-zinc-200 bg-[#f7f7fa] px-3 py-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] sm:px-8 sm:py-4" +
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
            { className: "flex flex-wrap items-center gap-2 text-[11px] text-zinc-500" },
            React.createElement(FileExportMenu, {
              token: authToken,
              className: "flex flex-wrap gap-2",
              getExportText: function () {
                for (var gi = messages.length - 1; gi >= 0; gi--) {
                  var mm = messages[gi];
                  if (
                    mm &&
                    mm.role === "assistant" &&
                    mm.content &&
                    !/^Gerando\s/i.test(String(mm.content))
                  )
                    return mm.content;
                }
                return "";
              },
            }),
            React.createElement(AudioRecorder, {
              token: authToken,
              mode: "transcribe",
              onTranscript: function (t) {
                setInput(function (prev) {
                  return (prev ? prev + " " : "") + t;
                });
              },
              onError: function () {
                setMessages(function (prev) {
                  return prev.concat([
                    {
                      role: "assistant",
                      content:
                        "Não consegui transcrever o áudio. Confirme microfone, tente de novo e verifique no servidor: AZURE_SPEECH_KEY + AZURE_SPEECH_REGION e ffmpeg para WebM.",
                      timestamp: timeLabel(),
                    },
                  ]);
                });
              },
              className: "inline-flex",
            }),
            React.createElement(AudioRecorder, {
              token: authToken,
              mode: "pipeline",
              onVoicePipelineResult: function (data) {
                var tr = (data && data.transcript) || "";
                var reply = (data && data.reply) || "";
                var tts = data && data.tts;
                var url = tts && tts.audio_url;
                setMessages(function (prev) {
                  return prev.concat([
                    { role: "user", content: tr || "(áudio)", timestamp: timeLabel() },
                    {
                      role: "assistant",
                      content: sanitizeChatText(reply),
                      timestamp: timeLabel(),
                      ttsAudioUrl: url || undefined,
                    },
                  ]);
                });
              },
              onError: function (err) {
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
              className: "inline-flex",
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
            React.createElement(
              "div",
              { className: "flex gap-2 overflow-x-auto pb-1" },
                React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () { handleGenerateMedia("image"); },
                  disabled: loading || mediaBusy || multimodalBusy || !input.trim(),
                  className:
                    "shrink-0 h-9 rounded-xl border border-zinc-200 bg-white px-3 text-xs text-zinc-700 hover:bg-zinc-50 disabled:opacity-40 inline-flex items-center gap-1.5",
                },
                React.createElement(IconImage, null),
                "Imagem"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () { handleGenerateMedia("audio"); },
                  disabled: loading || mediaBusy || multimodalBusy || !input.trim(),
                  className:
                    "shrink-0 h-9 rounded-xl border border-zinc-200 bg-white px-3 text-xs text-zinc-700 hover:bg-zinc-50 disabled:opacity-40 inline-flex items-center gap-1.5",
                },
                React.createElement(IconAudio, null),
                "Áudio"
              )
            ),
            React.createElement(
              "div",
              { className: "flex gap-2 items-end" },
              React.createElement("input", {
                id: "syntexa-file-input",
                type: "file",
                multiple: true,
                accept:
                  "image/*,video/*,audio/*,application/pdf,.pdf,.txt,.md,.json,.csv,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,.xlsx",
                className: "hidden",
                onChange: handleFilesChange,
              }),
              React.createElement(
                "button",
                {
                  type: "button",
                  "aria-label": "Anexar arquivo",
                  onClick: function () {
                    var inputEl = document.getElementById("syntexa-file-input");
                    if (inputEl) inputEl.click();
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
                placeholder: "Digite ou fale sua mensagem...",
                className:
                  "syntexa-input min-h-[44px] max-h-28 flex-1 resize-none rounded-2xl px-4 py-3 text-sm shadow-sm",
              }),
              recognition && React.createElement(
                "button",
                {
                  type: "button",
                  "aria-label": "Falar",
                  onClick: toggleVoice,
                  className:
                    (listening ? "syntexa-mic-btn-listening" : "syntexa-mic-btn") + " shrink-0 flex items-center justify-center w-10 h-10 rounded-xl",
                },
                listening
                  ? React.createElement(
                      "svg",
                      { viewBox: "0 0 24 24", className: "h-4 w-4 text-red-600", fill: "currentColor", "aria-hidden": true },
                      React.createElement("rect", { x: "7", y: "7", width: "10", height: "10", rx: "1.5" })
                    )
                  : React.createElement(IconMic, null)
              ),
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
