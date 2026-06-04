"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { ChatLayout } from "../../components/chat-layout";
import { Button } from "../../components/ui/button";
import { FileExportMenu } from "../../components/FileExportMenu";
import {
  chatCompletionStream,
  chatCompletionWithMedia,
  generateImage,
  generateMusic,
  generateSpeech,
  generateVideo,
  getProfile,
  publicChatStream,
  publicChatWithMedia,
  getChatSessionMessages,
} from "../../lib/api";
import {
  isDesktopMode,
  desktopChatCompletion,
  desktopChatStream,
  desktopHealthCheck,
  desktopBootDiagnostic,
} from "../../lib/desktop-api";
import { t } from "../../lib/i18n";
import { useLanguage } from "../../components/language-provider";
import { sanitizeOutput, sanitizeStreamChunk } from "../../lib/sanitizeOutput";
import { normalizeContent, normalizeStreamChunk } from "../../lib/normalizeContent";
import { setXenovaSttProgressCallback } from "../../lib/xenova-stt";
import { MarkdownMessage } from "../../components/MarkdownMessage";

/**
 * V46 — Limpa marcações de Markdown que ficam visíveis como caracteres
 * "sujos" no balão (`**`, `##`, `__`, `~~`, `[texto](url)`, `` ` ``).
 * Aplica-se só ao conteúdo do assistente; o que o usuário digita é mantido.
 * Preserva quebras de linha e listas com `- ` (vira `• `).
 */
function cleanAssistantText(input) {
  var s = sanitizeOutput(String(input == null ? "" : input));
  if (!s) return s;
  // Code fences ```lang ... ```  → mantém só o miolo
  s = s.replace(/```[a-zA-Z0-9_-]*\n?([\s\S]*?)```/g, function (_m, body) {
    return String(body || "").trim();
  });
  // Links [texto](url)  → texto (url)
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, "$1 ($2)");
  // Imagens ![alt](url) → alt
  s = s.replace(/!\[([^\]]*)\]\([^)\s]+\)/g, "$1");
  // Headings ###/##/# no começo de linha
  s = s.replace(/^[ \t]{0,3}#{1,6}[ \t]+/gm, "");
  // Bold/italic emphasis: **x**, __x__, *x*, _x_
  s = s.replace(/\*\*([^*]+?)\*\*/g, "$1");
  s = s.replace(/__([^_]+?)__/g, "$1");
  s = s.replace(/(^|[\s(])\*([^\s*][^*]*?)\*(?=[\s)\.,;:!?]|$)/g, "$1$2");
  s = s.replace(/(^|[\s(])_([^\s_][^_]*?)_(?=[\s)\.,;:!?]|$)/g, "$1$2");
  // Strikethrough ~~x~~
  s = s.replace(/~~([^~]+?)~~/g, "$1");
  // Inline code `x`
  s = s.replace(/`([^`]+?)`/g, "$1");
  // Blockquote leader "> "
  s = s.replace(/^[ \t]{0,3}>\s?/gm, "");
  // Lista "-/* " → "• "
  s = s.replace(/^[ \t]{0,6}[*\-+][ \t]+/gm, "• ");
  // Lista numerada "1. " continua igual (legível)
  // Markdown table separator rows (| --- | --- |) → empty
  s = s.replace(/^\s*\|[\s\-:|]+\|\s*$/gm, "");
  // Pipe table rows: | A | B | C | → "A  B  C"
  s = s.replace(/^\s*\|(.+)\|\s*$/gm, function (_m, inner) {
    return inner.split("|").map(function (c) { return c.trim(); }).filter(Boolean).join("  ");
  });
  // Residual lone pipe chars (e.g. table artifacts not caught above)
  s = s.replace(/\s\|\s/g, "  ");
  s = s.replace(/^\||\|$/gm, "");
  // Colapsa 3+ quebras de linha em 2
  s = s.replace(/\n{3,}/g, "\n\n");
  return s.trim();
}

/**
 * BLOQUEIO TOTAL DE OBJETOS — Garante que QUALQUER valor é convertido para string pura.
 * Usado para prevenir [object Object] em Safari mobile (que envia InputEvent/SyntheticEvent).
 */
function ensureString(value) {
  if (typeof value === "string") {
    return value;
  }

  if (value?.target?.value) {
    return String(value.target.value);
  }

  if (value?.content) {
    return String(value.content);
  }

  if (value?.message) {
    return String(value.message);
  }

  return "";
}

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
  var mounted = React.useState(false);
  var setMounted = mounted[1];
  var failed = React.useState(false);
  var setFailed = failed[1];
  React.useEffect(function () {
    setMounted(true);
  }, []);
  if (!mounted[0]) {
    return React.createElement("div", {
      className: "mt-3 h-[min(420px,40vh)] w-full rounded-xl border border-[rgba(15,23,42,0.06)] bg-[rgba(15,23,42,0.02)]",
      "aria-hidden": true,
    });
  }
  if (failed[0]) {
    return React.createElement("p", { className: "mt-3 text-sm text-[#b45309]" },
      t("chatImageError", locale)
    );
  }
  return React.createElement("img", {
    src: src,
    alt: props.alt || t("imageGenerated", locale),
    className: "mt-3 max-h-[420px] w-full rounded-xl border border-[rgba(15,23,42,0.08)] object-contain",
    loading: "lazy",
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

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [plan, setPlan] = useState("anon");
  const [listening, setListening] = useState(false);
  const [voiceTranscribing, setVoiceTranscribing] = useState(false);
  const [voiceProgress, setVoiceProgress] = useState("");
  const [voiceError, setVoiceError] = useState("");
  const micRecorderRef = useRef(null);
  const micStreamRef = useRef(null);
  const micChunksRef = useRef([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [canStop, setCanStop] = useState(false);
  const [desktopMode, setDesktopMode] = useState(false);
  const [desktopReady, setDesktopReady] = useState(false);
  const [bootDiagnostic, setBootDiagnostic] = useState(null);
  const [bootFailures, setBootFailures] = useState([]);
  const [authToken, setAuthToken] = useState(null);
  const abortRef = useRef(null);
  var messagesEndRef = useRef(null);
  var textareaRef = useRef(null);
  const { locale } = useLanguage();
  const speechRef = useRef(null);

  // Detecção de modo desktop + boot validation obrigatória
  useEffect(function () {
    if (typeof window === "undefined") return;
    var isDesktop = isDesktopMode();
    setDesktopMode(isDesktop);
    if (isDesktop) {
      desktopHealthCheck().then(function (r) {
        setDesktopReady(r.ok && r.runtime_ready);
      }).catch(function () {
        setDesktopReady(false);
      });
      // BOOT DIAGNOSTIC REAL — fail fast absoluto
      desktopBootDiagnostic().then(function (diag) {
        setBootDiagnostic(diag);
        if (diag && diag.failures && diag.failures.length > 0) {
          setBootFailures(diag.failures);
          setDesktopReady(false);
        }
      }).catch(function (err) {
        setBootDiagnostic({ boot_passed: false, error: String(err) });
        setBootFailures([{ component: "boot_diagnostic_request", error: String(err) }]);
        setDesktopReady(false);
      });
      // Listener IPC para boot failure vindo do main process
      if (window.desktopAPI && window.desktopAPI.onBootFailure) {
        var unsub = window.desktopAPI.onBootFailure(function (payload) {
          if (payload && payload.failures) {
            setBootFailures(payload.failures);
            setDesktopReady(false);
          }
        });
        return function () { if (unsub) unsub(); };
      }
    }
  }, []);

  useEffect(function () {
    try {
      var el = messagesEndRef.current;
      if (el) el.scrollIntoView({ behavior: "smooth", block: "end" });
    } catch (e) {}
  }, [messages, loading]);

  useEffect(function () {
    setXenovaSttProgressCallback(function (msg) {
      setVoiceProgress(msg || "");
    });
    return function () {
      setXenovaSttProgressCallback(null);
      // Limpa SpeechRecognition se estiver ativo
      try {
        if (speechRef.current) {
          speechRef.current.abort();
          speechRef.current = null;
        }
      } catch (_) {}
    };
  }, []);

  function stopMicStream() {
    try {
      var stream = micStreamRef.current;
      if (stream && stream.getTracks) {
        stream.getTracks().forEach(function (t) {
          try {
            t.stop();
          } catch (_) {}
        });
      }
    } catch (_) {}
    micStreamRef.current = null;
  }

  function pickMicMimeType() {
    if (typeof MediaRecorder === "undefined") return "";
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) return "audio/webm;codecs=opus";
    if (MediaRecorder.isTypeSupported("audio/webm")) return "audio/webm";
    if (MediaRecorder.isTypeSupported("audio/mp4")) return "audio/mp4";
    return "";
  }

  async function finishMicRecording(blob) {
    setVoiceTranscribing(true);
    setVoiceError("");
    setVoiceProgress("A transcrever…");
    try {
      // Usa backend API para STT (não precisa baixar modelo no browser)
      var fd = new FormData();
      fd.append("file", blob, "audio.webm");
      var resp = await fetch("https://api.syntexabr.com.br/v1/voice/stt", {
        method: "POST",
        body: fd,
      });
      if (!resp.ok) throw new Error("STT failed: " + resp.status);
      var data = await resp.json();
      var text = data.text || data.transcript || "";
      if (!text) throw new Error("Transcrição vazia");
      setVoiceProgress("");
      setInput(text);
      setTimeout(function () { autoGrowTextarea(); }, 0);
      setVoiceTranscribing(false);
      await sendMessage(text);
    } catch (e) {
      setVoiceProgress("");
      setVoiceError("Erro na transcrição. Tente novamente.");
      setVoiceTranscribing(false);
    }
  }

  function isAuthErrorMessage(msg) {
    var txt = String(msg || "").toLowerCase();
    return (
      txt.indexOf("não foi possível validar as credenciais") >= 0 ||
      txt.indexOf("not authenticated") >= 0 ||
      txt.indexOf("401") >= 0
    );
  }

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const token = window.localStorage.getItem("syntexa_token");
      setAuthToken(token || null);
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

  async function sendMessage(overrideContent) {
    var content =
      overrideContent != null && String(overrideContent).trim()
        ? String(overrideContent).trim()
        : input.trim();
    if (!content || loading || voiceTranscribing) return;
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
          },
        ])
      );
      return;
    }

    var mediaIntent = detectMediaIntent(content);
    var wantsImage = mediaIntent.wantsImage;
    var wantsVideo = mediaIntent.wantsVideo;
    var wantsAudio = mediaIntent.wantsAudio;
    var wantsSpeech = mediaIntent.wantsSpeech;

    // Fluxo especial: texto pedindo mídia chama diretamente o gerador real.
    if (wantsImage || wantsVideo || wantsAudio || wantsSpeech) {
      var kind = wantsImage
        ? "image"
        : wantsVideo
          ? "video"
          : wantsSpeech
            ? "speech"
            : "audio";
      var labelKey =
        kind === "image"
          ? "image"
          : kind === "video"
            ? "video"
            : kind === "speech"
              ? "speech"
              : "audio";
      var label = t(labelKey, locale).toLowerCase();
      var userMsg = { role: "user", content: content };
      setMessages((prev) =>
        prev.concat([
          userMsg,
          {
            role: "assistant",
            content: t("generating", locale) + " " + label + " " + t("providerReal", locale) + "...",
          },
        ])
      );
      setInput("");
      setAttachments([]);
      setLoading(true);
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
              content: t("imageGenerated", locale) + ".",
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
              content: t("imageGenerated", locale) + ".",
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
          setMessages((prev) =>
            prev.concat([
              {
                role: "assistant",
                content:
                kind === "video"
                  ? t("videoGenerated", locale) + "."
                  : kind === "speech"
                    ? t("speechGenerated", locale) + "."
                    : t("audioGenerated", locale) + ".",
                media: {
                  type: kind === "video" ? "video" : "audio",
                  url: mediaUrl,
                },
              },
            ])
          );
          return;
        }

        setMessages((prev) =>
          prev.concat([
            {
              role: "assistant",
              content:
                "[MÍDIA V45] Provedor retornou resposta sem URL de arquivo: " +
                JSON.stringify(result || {}),
            },
          ])
        );
      } catch (err) {
        var msg = err instanceof Error ? err.message : String(err);
        // FAIL FAST ABSOLUTO
        setMessages((prev) => {
          var p = prev.slice();
          var out = msg && String(msg).trim().length > 0
            ? "[MÍDIA FALHA — V45] " + String(msg).trim()
            : "[MÍDIA FALHA — V45] Erro desconhecido no gerador.";
          p[p.length - 1] = {
            role: "assistant",
            content: out,
          };
          return p;
        });
      } finally {
        setLoading(false);
      }
      return;
    }

    // Fluxo padrão: chat textual (público, autenticado, ou DESKTOP OFFLINE).
    var nextHistory = messages.concat([{ role: "user", content: content }]);
    setMessages(nextHistory);
    setInput("");
    setAttachments([]);
    setLoading(true);
    try {
      var reply;
      var hasMedia = attachments && attachments.length > 0;

      // ── MODO DESKTOP SOBERANO (offline) — só sem arquivos e desktop pronto ─────────────────────
      if (desktopMode && desktopReady && !hasMedia) {
        setMessages((prev) => prev.concat([{ role: "assistant", content: "" }]));
        const controller = new AbortController();
        abortRef.current = controller;
        setCanStop(true);
        try {
          await desktopChatStream(nextHistory, function (chunk) {
            var safeChunk = sanitizeStreamChunk(chunk);
            setMessages((prev) => {
              var p = prev.slice();
              var last = p[p.length - 1];
              if (last && last.role === "assistant") {
                p[p.length - 1] = { ...last, content: last.content + safeChunk };
              }
              return p;
            });
          }, { signal: controller.signal, max_tokens: 2048 });
        } catch (desktopErr) {
          var dmsg = desktopErr instanceof Error ? desktopErr.message : String(desktopErr);
          setMessages((prev) => {
            var p = prev.slice();
            var last = p[p.length - 1];
            if (last && last.role === "assistant") {
              p[p.length - 1] = { ...last, content: "[Runtime Local] " + dmsg };
            }
            return p;
          });
        } finally {
          setCanStop(false);
          abortRef.current = null;
          setMessages(function (prev) {
            var p = prev.slice();
            var last = p[p.length - 1];
            if (last && last.role === "assistant" && last.content) {
              p[p.length - 1] = { ...last, content: sanitizeOutput(last.content) };
            }
            return p;
          });
        }
      }
      // ── MODO DESKTOP SEM RUNTIME — só bloqueia se não tiver arquivos ─────────────────────────────
      else if (desktopMode && !desktopReady && !hasMedia) {
        var diagParts = ["[Syntexa Desktop V45] BOOT BLOQUEADO — Foundation Model não operacional."];
        if (bootFailures.length > 0) {
          diagParts.push("Falhas detectadas:");
          bootFailures.forEach(function (f) {
            diagParts.push("• " + (f.component || "unknown") + ": " + (f.error || "sem detalhe"));
          });
        } else if (bootDiagnostic && bootDiagnostic.error) {
          diagParts.push(t("error", locale) + ": " + bootDiagnostic.error);
        } else {
          diagParts.push("Checkpoint 70B inexistente ou não treinado.");
          diagParts.push("Verifique: checkpoints/foundation/ deve conter manifest.json + syntexa_foundation_weights.pt + tokenizer/");
        }
        diagParts.push("\nLogs: logs/runtime.log | logs/inference.log | logs/boot_validation.log");
        setMessages((prev) => prev.concat([{
          role: "assistant",
          content: diagParts.join("\n")
        }]));
      }
      // ── MODO ONLINE (API remota) — sempre quando tem arquivos ou desktop não disponível ─────────────────────────────
      else if (token) {
        try {
          if (hasMedia) {
            reply = await chatCompletionWithMedia(token, nextHistory, attachments);
            setMessages((prev) => prev.concat([{ role: "assistant", content: sanitizeOutput(reply) }]));
          } else {
            setMessages((prev) => prev.concat([{ role: "assistant", content: "" }]));
            const controller = new AbortController();
            abortRef.current = controller;
            setCanStop(true);
            
            // Gera session_id na primeira mensagem
            var sessionId = currentSessionId;
            if (!sessionId) {
              sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
              setCurrentSessionId(sessionId);
            }
            
            try {
              await chatCompletionStream(token, nextHistory, function (chunk) {
                var safeChunk = sanitizeStreamChunk(chunk);
                setMessages((prev) => {
                  var p = prev.slice();
                  var last = p[p.length - 1];
                  if (last && last.role === "assistant") {
                    p[p.length - 1] = { ...last, content: last.content + safeChunk };
                  }
                  return p;
                });
              }, controller.signal, sessionId);
            } finally {
              setCanStop(false);
              abortRef.current = null;
              setMessages(function (prev) {
                var p = prev.slice();
                var last = p[p.length - 1];
                if (last && last.role === "assistant" && last.content) {
                  p[p.length - 1] = { ...last, content: sanitizeOutput(last.content) };
                }
                return p;
              });
            }
          }
        } catch (authErr) {
          var authMsg = authErr instanceof Error ? authErr.message : String(authErr);
          if (isAuthErrorMessage(authMsg)) {
            try {
              window.localStorage.removeItem("syntexa_token");
            } catch (_) {}
            setPlan("anon");
            setMessages(function (prev) {
              var p = prev.slice();
              var last = p[p.length - 1];
              if (last && last.role === "assistant" && !String(last.content || "").trim()) {
                p.pop();
              }
              return p.concat([
                {
                  role: "assistant",
                  content: "Sessão expirada. Faça login novamente para continuar o chat.",
                },
              ]);
            });
            return;
          }
          throw authErr;
        }
      } else {
        if (hasMedia) {
          reply = await publicChatWithMedia(nextHistory, attachments);
          setMessages((prev) => prev.concat([{ role: "assistant", content: sanitizeOutput(reply) }]));
        } else {
          setMessages((prev) => prev.concat([{ role: "assistant", content: "" }]));
          const controller = new AbortController();
          abortRef.current = controller;
          setCanStop(true);
          try {
            await publicChatStream(nextHistory, function (chunk) {
              var safeChunk = sanitizeStreamChunk(chunk);
              setMessages((prev) => {
                var p = prev.slice();
                var last = p[p.length - 1];
                if (last && last.role === "assistant") {
                  p[p.length - 1] = { ...last, content: last.content + safeChunk };
                }
                return p;
              });
            }, controller.signal);
          } finally {
            setCanStop(false);
            abortRef.current = null;
            setMessages(function (prev) {
              var p = prev.slice();
              var last = p[p.length - 1];
              if (last && last.role === "assistant" && last.content) {
                p[p.length - 1] = { ...last, content: sanitizeOutput(last.content) };
              }
              return p;
            });
          }
        }
      }
    } catch (err) {
      var rawMsg = err instanceof Error ? err.message : String(err);
      var detail = err instanceof Error && err.cause ? String(err.cause) : "";
      var stack = err instanceof Error && err.stack ? err.stack : "";
      // Detecta indisponibilidade do motor de IA (503 / runtime offline) e mostra mensagem clara.
      var lower = String(rawMsg + " " + detail).toLowerCase();
      var isRuntimeOutage =
        /503|runtime|inference|gateway|ai worker|provider configurado|nao foi possivel concluir|não foi possível concluir/i.test(lower);
      var isLimitError = /403|forbidden|limite|limit/i.test(lower);
      var displayMsg;
      if (isLimitError) {
        displayMsg = t("limitUsage", locale);
      } else if (desktopMode && !desktopReady) {
        displayMsg = t("desktopNotReady", locale);
      } else if (isRuntimeOutage) {
        displayMsg = t("aiEngineUnavailable", locale);
      } else {
        displayMsg = rawMsg || t("genericError", locale);
      }
      // Em desenvolvimento, exibe detalhes técnicos abaixo da mensagem amigável.
      var isDev = typeof window !== "undefined" && /^(localhost|127\.|192\.168\.)/i.test(window.location.hostname);
      if (isDev && (detail || stack)) {
        displayMsg += "\n\n— debug —\n" + (detail ? detail + "\n" : "") + (stack ? stack.split("\n").slice(0, 3).join("\n") : "");
      }
      setMessages(function (prev) {
        var p = prev.slice();
        var last = p[p.length - 1];
        if (last && last.role === "assistant" && !String(last.content || "").trim()) {
          p[p.length - 1] = { ...last, content: displayMsg };
          return p;
        }
        return p.concat([{ role: "assistant", content: displayMsg }]);
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  function autoGrowTextarea() {
    var el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    var newHeight = Math.min(Math.max(el.scrollHeight, 44), 112);
    el.style.height = newHeight + "px";
  }

  function handleNewConversation() {
    setMessages((prev) => prev.slice(0, 2));
    setAttachments([]);
    setCurrentSessionId(null);
  }

  function handleFilesChange(e) {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setAttachments(prev => [...prev, ...files]);
    e.target.value = "";
  }

  function removeAttachment(index) {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  }

  function clearAttachments() {
    setAttachments([]);
  }

  async function handleGenerateMedia(kind) {
    var prompt = input.trim();
    if (!prompt || loading) return;
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
    setMessages((prev) => prev.concat([{ role: "user", content: "Gerar " + label + ": " + prompt }]));
    setInput("");
    setLoading(true);
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
        setMessages((prev) =>
          prev.concat([
            {
              role: "assistant",
              content: t("imageGenerated", locale) + ".",
              media: { type: "image", url: imageUrl2 },
            },
          ])
        );
        return;
      }

      if (kind === "image" && result && (result.url || result.image_url)) {
        var imgU2 = result.url || result.image_url;
        setMessages((prev) =>
          prev.concat([
            {
              role: "assistant",
              content: t("imageGenerated", locale) + ".",
              media: { type: "image", url: imgU2 },
            },
          ])
        );
        return;
      }

      var mediaUrl =
        (result && (result.url || result.video_url || result.audio_url || result.file_url || result.output_url)) ||
        "";
      if (mediaUrl) {
        setMessages((prev) =>
          prev.concat([
            {
              role: "assistant",
              content:
                kind === "video"
                  ? t("videoGenerated", locale) + "."
                  : kind === "speech"
                    ? t("speechGenerated", locale) + "."
                    : t("audioGenerated", locale) + ".",
              media: { type: kind === "video" ? "video" : "audio", url: mediaUrl },
            },
          ])
        );
        return;
      }

      setMessages((prev) =>
        prev.concat([
          {
            role: "assistant",
            content: "[MÍDIA V45] Provedor retornou resposta vazia ou sem URL. Nenhum fallback disponível."
          },
        ])
      );
    } catch (err) {
      var raw = err instanceof Error ? err.message : String(err);
      // FAIL FAST ABSOLUTO: nunca usar "tente novamente"
      var userMsg = raw && String(raw).trim().length > 0
        ? "[MÍDIA FALHA — V45] " + String(raw).trim()
        : "[MÍDIA FALHA — V45] Erro desconhecido no gerador de mídia.";
      setMessages((prev) =>
        prev.concat([
          {
            role: "assistant",
            content: userMsg,
          },
        ])
      );
    } finally {
      setLoading(false);
    }
  }

  async function toggleVoice() {
    if (voiceTranscribing || loading) return;

    var mr = micRecorderRef.current;
    if (mr && mr.state === "recording") {
      mr.stop();
      setListening(false);
      return;
    }

    if (typeof navigator === "undefined" || !navigator.mediaDevices) {
      setVoiceError("Navegador não suporta microfone");
      return;
    }

    setVoiceError("");
    setVoiceProgress("Iniciando microfone…");

    try {
      var stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;
      micChunksRef.current = [];
      
      var mime = "audio/webm";
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) mime = "audio/webm;codecs=opus";
      else if (!MediaRecorder.isTypeSupported("audio/webm")) mime = "audio/mp4";
      
      var recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      
      recorder.ondataavailable = function (e) {
        if (e.data && e.data.size) micChunksRef.current.push(e.data);
      };
      
      recorder.onstop = async function () {
        setListening(false);
        stopMicStream();
        micRecorderRef.current = null;
        
        var blob = new Blob(micChunksRef.current, { type: mime || "audio/webm" });
        micChunksRef.current = [];
        
        if (blob.size === 0) {
          setVoiceError("Nenhum áudio gravado");
          return;
        }
        
        setVoiceTranscribing(true);
        setVoiceProgress("Transcrevendo…");
        
        try {
          var fd = new FormData();
          fd.append("file", blob, "audio.webm");
          
          var resp = await fetch("https://api.syntexabr.com.br/v1/voice/stt", {
            method: "POST",
            body: fd,
          });
          
          if (!resp.ok) throw new Error("STT " + resp.status);
          
          var data = await resp.json();
          var text = data.text || data.transcript || "";
          
          if (!text) throw new Error("Transcrição vazia");
          
          setInput(text);
          setVoiceProgress("");
          setVoiceTranscribing(false);
          autoGrowTextarea();
        } catch (err) {
          setVoiceTranscribing(false);
          setVoiceProgress("");
          setVoiceError("Falha na transcrição: " + (err.message || "erro"));
        }
      };
      
      micRecorderRef.current = recorder;
      recorder.start(100);
      setListening(true);
      setVoiceProgress("");
      
    } catch (e) {
      setVoiceProgress("");
      var errName = e && e.name ? e.name : "";
      
      if (errName === "NotAllowedError" || errName === "PermissionDeniedError") {
        setVoiceError("Microfone bloqueado. Clique no ícone de cadeado na barra de endereço → Microfone → Permitir → Recarregue a página.");
      } else if (errName === "NotFoundError") {
        setVoiceError("Nenhum microfone detectado. Verifique se está conectado.");
      } else if (errName === "NotReadableError") {
        setVoiceError("Microfone em uso por outro aplicativo. Feche outros programas e tente novamente.");
      } else {
        setVoiceError("Erro ao acessar microfone: " + (e.message || "desconhecido"));
      }
    }
  }

  var visible = messages.filter((m) => m.role !== "system");
  var showTyping = loading && visible.length > 0;

  function handleStop() {
    try {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    } catch (e) {}
    setCanStop(false);
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
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
              content: m.content,
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
    React.createElement("div", { className: "relative flex min-h-0 w-full min-w-0 max-w-full flex-1 flex-col overflow-hidden" },
      // Badge modo desktop (canvas quântico vem do ChatLayout, atrás de tudo, pointer-events-none)
      desktopMode && React.createElement(
        "div",
        {
          className: "absolute top-2 right-2 z-20 flex items-center gap-1.5 rounded-full border border-[rgba(15,23,42,0.06)] bg-white/90 px-2.5 py-1 text-[10px] font-medium text-[#64748b] backdrop-blur-md",
        },
        React.createElement("span", {
          className: "h-1.5 w-1.5 rounded-full " + (desktopReady ? "bg-[#059669]" : "bg-amber-500")
        }),
        desktopReady
          ? t("runtimeSovereignOffline", locale)
          : t("desktopRuntimeNotLoaded", locale)
      ),
      React.createElement("div", { className: "flex-1 overflow-y-auto overflow-x-hidden overscroll-contain px-3 pb-32 pt-3 sm:px-8 sm:pt-5 min-w-0" },
        React.createElement("div", { className: "mx-auto flex w-full max-w-3xl flex-col gap-4" },
          visible.map((m, idx) => {
            var cn = m.role === "user" ? "syntexa-bubble-user ml-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed break-words" : "syntexa-bubble-assistant mr-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed text-[var(--text-primary)] break-words";
            var msgTime = m.timestamp ? new Date(m.timestamp).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
            var safeContent = typeof m.content === "string" ? m.content : normalizeContent(m.content);
            return React.createElement(motion.div, { key: idx, initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25 }, className: cn },
              React.createElement("div", { className: "mb-1.5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-[#94a3b8]" },
                React.createElement("span", null, m.role === "user" ? t("you", locale) : t("syntexa", locale)),
                React.createElement("span", { className: "text-[10px] font-normal normal-case tracking-normal text-[#cbd5e1]" }, msgTime)
              ),
              (m.role === "assistant" && new RegExp("^" + t("generating", locale) + "\\s", "i").test(String(safeContent || "")))
                ? React.createElement(
                    "div",
                    { className: "flex items-center gap-2 whitespace-pre-wrap" },
                    React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true }),
                    React.createElement("span", null, safeContent)
                  )
                : m.role === "assistant"
                  ? React.createElement(MarkdownMessage, { content: safeContent })
                  : React.createElement("p", { className: "whitespace-pre-wrap" }, safeContent),
              m.media && m.media.type === "image" &&
                React.createElement(ChatImage, {
                  src: m.media.url,
                  alt: t("imageGenerated", locale),
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
                      "mt-2 inline-flex items-center text-xs font-medium text-[#64748b] hover:text-[#475569] underline decoration-[#64748b]/40",
                  },
                  t('chatDownloadImage', locale)
                ),
              m.media && m.media.type === "video" &&
                (String(m.media.url || "").startsWith("data:image/")
                  ? React.createElement("img", {
                      src: m.media.url,
                      alt: "Video gerado",
                      className: "mt-3 max-h-[420px] w-full rounded-xl border border-[#e2e8f0] object-contain",
                    })
                  : React.createElement("video", {
                      src: m.media.url,
                      controls: true,
                      className: "mt-3 max-h-[420px] w-full rounded-xl border border-[#e2e8f0]",
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
                      "mt-2 inline-flex items-center text-xs font-medium text-[#64748b] hover:text-[#475569] underline decoration-[#64748b]/40",
                  },
                  t('chatDownloadVideo', locale)
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
                      "mt-2 inline-flex items-center text-xs font-medium text-[#64748b] hover:text-[#475569] underline decoration-[#64748b]/40",
                  },
                  t('chatDownloadAudio', locale)
                ),
              m.role === "assistant" && m.content && !new RegExp("^(" + t("generating", locale) + "\\s|" + t("error", locale) + ":)", "i").test(String(m.content || "")) &&
                React.createElement("div", { className: "mt-2 flex items-center gap-3" },
                  React.createElement("button", {
                    type: "button",
                    onClick: async function () {
                      try { await navigator.clipboard.writeText(m.content); } catch (e) {}
                    },
                    className: "inline-flex items-center gap-1 text-[10px] font-medium text-[#64748b] hover:text-[#475569] transition-colors",
                    title: t("copyAnswer", locale),
                  },
                    React.createElement("svg", { className: "h-3 w-3", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.5" },
                      React.createElement("rect", { x: "9", y: "9", width: "13", height: "13", rx: "2", ry: "2" }),
                      React.createElement("path", { d: "M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" })
                    ),
                    t("copy", locale)
                  ),
                  React.createElement("button", {
                    type: "button",
                    onClick: function () {
                      try {
                        var utter = new window.SpeechSynthesisUtterance(m.content);
                        utter.lang = locale;
                        utter.rate = 1.1;
                        window.speechSynthesis.cancel();
                        window.speechSynthesis.speak(utter);
                      } catch (e) {}
                    },
                    className: "inline-flex items-center gap-1 text-[10px] font-medium text-[#64748b] hover:text-[#475569] transition-colors",
                    title: t("listenAnswer", locale),
                  },
                    React.createElement("svg", { className: "h-3 w-3", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.5" },
                      React.createElement("path", { d: "M11 5L6 9H2v6h4l5 4V5z" }),
                      React.createElement("path", { d: "M15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" })
                    ),
                    t("listen", locale)
                  )
                )
              );
          }),
          showTyping && React.createElement(motion.div, { initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25 }, className: "syntexa-bubble-assistant mr-auto max-w-[85%] sm:max-w-[80%] rounded-[18px] px-4 py-3 sm:px-5 sm:py-4 bg-[#f8fafc]" },
            React.createElement("div", { className: "mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#475569]" }, t("syntexa", locale)),
            React.createElement("div", { className: "flex items-center gap-2 text-sm text-[#475569]" },
              React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true }),
              React.createElement("span", null, t("processingResponse", locale)))),
          visible.length === 0 &&
            React.createElement(
              motion.div,
              {
                initial: { opacity: 0, y: 12 },
                animate: { opacity: 1, y: 0 },
                transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
                className: "mx-auto flex w-full max-w-2xl flex-col items-center px-4 pt-12 sm:pt-20 text-center",
              },
              React.createElement(
                motion.div,
                {
                  initial: { scale: 0.92, opacity: 0 },
                  animate: { scale: 1, opacity: 1 },
                  transition: { duration: 0.6, delay: 0.05, ease: [0.22, 1, 0.36, 1] },
                  className: "mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#eef2ff] to-[#f5f3ff] shadow-[0_8px_24px_rgba(99,102,241,0.10)]",
                  "aria-hidden": "true",
                },
                React.createElement(
                  "svg",
                  { viewBox: "0 0 24 24", className: "h-5 w-5 text-[#6366f1]", fill: "none", stroke: "currentColor", strokeWidth: "1.7", strokeLinecap: "round", strokeLinejoin: "round" },
                  React.createElement("path", { d: "M12 3l1.6 4.2 4.4 1.4-3.4 3 .8 4.4-3.4-2.2-3.4 2.2.8-4.4-3.4-3 4.4-1.4z" })
                )
              ),
              React.createElement("h2", { className: "text-[22px] sm:text-[26px] font-semibold tracking-tight text-[#0f172a]" }, t("askAnything", locale)),
              React.createElement("p", { className: "mt-2 text-sm text-[#64748b]" }, t('chatQuickStartTitle', locale)),
              React.createElement(
                "div",
                { className: "mt-7 grid w-full grid-cols-1 gap-2 sm:grid-cols-2" },
                [
                  { k: 'chatQuickSummarize', i: "M4 6h16M4 12h16M4 18h10" },
                  { k: 'chatQuickExplain', i: "M12 3v18M3 12h18" },
                  { k: 'chatQuickPlan', i: "M3 4h18v4H3zM3 12h18v4H3zM3 20h12" },
                  { k: 'chatQuickEmail', i: "M3 7l9 6 9-6M3 7v10h18V7" },
                ].map(function (it, idx) {
                  return React.createElement(
                    motion.button,
                    {
                      key: idx,
                      type: "button",
                      initial: { opacity: 0, y: 8 },
                      animate: { opacity: 1, y: 0 },
                      transition: { duration: 0.35, delay: 0.15 + idx * 0.06, ease: [0.22, 1, 0.36, 1] },
                      whileHover: { y: -2 },
                      whileTap: { scale: 0.98 },
                      onClick: function () { setInput(t(it.k, locale)); try { textareaRef.current && textareaRef.current.focus(); } catch (_) {} },
                      className: "group flex items-center gap-3 rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white/70 px-4 py-3 text-left text-[13px] text-[#334155] transition-colors hover:border-[rgba(15,23,42,0.12)] hover:bg-white",
                    },
                    React.createElement(
                      "span",
                      { className: "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#f1f5f9] text-[#64748b] transition-colors group-hover:bg-[#eef2ff] group-hover:text-[#6366f1]", "aria-hidden": "true" },
                      React.createElement("svg", { viewBox: "0 0 24 24", className: "h-3.5 w-3.5", fill: "none", stroke: "currentColor", strokeWidth: "1.6", strokeLinecap: "round", strokeLinejoin: "round" },
                        React.createElement("path", { d: it.i })
                      )
                    ),
                    React.createElement("span", { className: "flex-1" }, t(it.k, locale))
                  );
                })
              )
            ),
          React.createElement("div", { ref: messagesEndRef, "aria-hidden": true }))
        ),
      React.createElement(
        "div",
        {
          className:
            "chat-input-wrapper relative shrink-0 sticky bottom-0 z-[70] border-t border-[#e2e8f0] bg-[#f8fafc] px-3 py-2 pb-[max(0.75rem,env(safe-area-inset-bottom))] shadow-[0_-4px_20px_rgba(15,23,42,0.06)] sm:px-8 sm:py-4",
        },
        React.createElement(
          "div",
          { className: "mx-auto flex w-full max-w-3xl flex-col gap-3" },
          attachments.length > 0 &&
            React.createElement(
              "div",
              { className: "flex flex-wrap items-center gap-2 text-xs text-[#475569]" },
              attachments.map((file, idx) =>
                React.createElement(
                  "span",
                  {
                    key: file.name + file.size + idx,
                    className:
                      "inline-flex items-center gap-1.5 rounded-full border border-[#e2e8f0] bg-[#f8fafc] px-3 py-1.5",
                  },
                  React.createElement("span", { className: "h-2 w-2 rounded-full bg-[#94a3b8]" }),
                  React.createElement("span", null, file.name),
                  React.createElement(
                    "button",
                    {
                      type: "button",
                      onClick: function() { removeAttachment(idx); },
                      className: "ml-1 text-[#94a3b8] hover:text-red-500",
                      title: "Remover arquivo"
                    },
                    "×"
                  )
                )
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: clearAttachments,
                  className: "text-[10px] text-red-500 hover:text-red-700 underline"
                },
                "Limpar todos"
              )
            ),
          React.createElement(
            "div",
            { className: "flex flex-col gap-1.5" },
            React.createElement(
              "div",
              { className: "flex flex-wrap gap-1.5 overflow-x-auto pb-0.5 [scrollbar-width:none]" },
              // ── Geração de mídia ──
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () { handleGenerateMedia("image"); },
                  disabled: loading || !input.trim(),
                  className: "shrink-0 h-9 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-3 text-xs text-[#475569] hover:bg-[#f1f5f9] disabled:opacity-40 inline-flex items-center gap-1.5 transition-colors",
                },
                React.createElement(IconImage, null),
                t("image", locale)
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () { handleGenerateMedia("audio"); },
                  disabled: loading || !input.trim(),
                  className: "shrink-0 h-9 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-3 text-xs text-[#475569] hover:bg-[#f1f5f9] disabled:opacity-40 inline-flex items-center gap-1.5 transition-colors",
                },
                React.createElement(IconAudio, null),
                t("audio", locale)
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () { handleGenerateMedia("video"); },
                  disabled: loading || !input.trim(),
                  className: "shrink-0 h-9 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-3 text-xs text-[#475569] hover:bg-[#f1f5f9] disabled:opacity-40 inline-flex items-center gap-1.5 transition-colors",
                },
                React.createElement(IconVideo, null),
                t("video", locale)
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () { handleGenerateMedia("speech"); },
                  disabled: loading || !input.trim(),
                  className: "shrink-0 h-9 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-3 text-xs text-[#475569] hover:bg-[#f1f5f9] disabled:opacity-40 inline-flex items-center gap-1.5 transition-colors",
                },
                React.createElement(IconAudio, null),
                t("speech", locale)
              ),
              // ── Separador + export (só aparece quando há mensagens) ──
              visible.length > 0 && React.createElement("div", { className: "h-9 w-px bg-[#e2e8f0] shrink-0 self-center" }),
              visible.length > 0 && React.createElement(FileExportMenu, {
                token: authToken,
                getExportText: function () {
                  var fullChat = [];
                  messages.forEach(function (mm) {
                    if (!mm || !mm.content) return;
                    var role = mm.role === "user" ? t("roleUser", locale) : t("roleAssistant", locale);
                    var content = String(mm.content);
                    if (new RegExp("^" + t("generating", locale) + "\\s", "i").test(content)) return;
                    var lines = [role, content];
                    if (mm.media && mm.media.type) {
                      var mediaLabel = mm.media.type === "image" ? t("imageGenerated", locale) :
                        mm.media.type === "video" ? t("videoGenerated", locale) :
                        mm.media.type === "audio" ? t("audioGenerated", locale) :
                        mm.media.type === "speech" ? t("speechGenerated", locale) : t("mediaGenerated", locale);
                      lines.push("[" + mediaLabel + "]");
                    }
                    fullChat.push(lines.join("\n"));
                  });
                  return fullChat.join("\n\n");
                },
              })
            ),
            React.createElement(
              "div",
              { className: "flex gap-2 items-end" },
              React.createElement("input", {
                id: "syntexa-file-input",
                type: "file",
                multiple: true,
                accept: "image/*,video/*,audio/*",
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
                    "shrink-0 flex items-center justify-center w-10 h-10 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] hover:bg-[#f1f5f9] text-[#475569]",
                },
                React.createElement(IconAttach, null)
              ),
              React.createElement("textarea", {
                ref: textareaRef,
                value: typeof input === "string" ? input : "",
                onChange: function (e) { var value = typeof e?.target?.value === "string" ? e.target.value : ""; setInput(value); autoGrowTextarea(); },
                onKeyDown: handleKeyDown,
                rows: 1,
                placeholder: t("chatPlaceholder", locale),
                className:
                  "chat-input syntexa-input min-h-[44px] max-h-28 flex-1 resize-none rounded-xl px-4 py-2.5 text-sm overflow-y-auto min-w-0 relative z-[1]",
                autoFocus: false,
              }),
              React.createElement(
                "button",
                {
                  type: "button",
                  "aria-label": voiceTranscribing ? "Processando voz" : listening ? "Parar" : "Falar",
                  title: listening
                    ? "Clique para parar"
                    : voiceTranscribing
                      ? "Processando voz…"
                      : "Clique para falar",
                  onClick: function () {
                    void toggleVoice();
                  },
                  disabled: loading || voiceTranscribing,
                  className:
                    "shrink-0 flex items-center justify-center w-10 h-10 rounded-xl border " +
                    (listening || voiceTranscribing
                      ? "border-red-400 bg-red-50 text-red-600"
                      : "border-[#e2e8f0] bg-[#f8fafc] hover:bg-[#f1f5f9] text-[#475569]"),
                },
                listening || voiceTranscribing
                  ? React.createElement(
                      "svg",
                      { viewBox: "0 0 24 24", className: "h-4 w-4", fill: "currentColor", "aria-hidden": true },
                      React.createElement("rect", { x: "7", y: "7", width: "10", height: "10", rx: "1.5" })
                    )
                  : React.createElement(IconMic, null)
              ),
              React.createElement(
                Button,
                { onClick: sendMessage, className: "shrink-0 self-end inline-flex items-center gap-2", disabled: loading },
                loading
                  ? React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true })
                  : React.createElement(IconSend, null),
                React.createElement("span", { className: "hidden sm:inline" }, loading ? t("sending", locale) : t("send", locale))
              ),
              canStop &&
                React.createElement(
                  Button,
                  {
                    type: "button",
                    variant: "outline",
                    onClick: handleStop,
                    className: "shrink-0 self-end ml-2 border-red-400 text-[#475569] hover:bg-red-50",
                  },
                  t("stop", locale)
                )
            ),
            (voiceError || voiceTranscribing || voiceProgress) &&
              React.createElement(
                "p",
                {
                  className: "text-xs " + (voiceError ? "text-red-600" : "text-[#64748b]"),
                  role: voiceError ? "alert" : "status",
                },
                voiceError || voiceProgress || t("listening", locale)
              )
          )
        )
      )
    )
  )
);
}

