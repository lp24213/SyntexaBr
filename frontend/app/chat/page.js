"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ChatLayout } from "../../components/chat-layout";
import { Button } from "../../components/ui/button";
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
      className: "mt-3 h-[min(420px,40vh)] w-full rounded-xl border border-white/10 bg-white/5",
      "aria-hidden": true,
    });
  }
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
    className: "mt-3 max-h-[420px] w-full rounded-xl border border-white/15 object-contain",
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
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Olá, aqui é a SyntexaBR - interface atualizada. Em que posso te ajudar agora?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [plan, setPlan] = useState("anon");
  const [listening, setListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [canStop, setCanStop] = useState(false);
  const abortRef = useRef(null);
  var messagesEndRef = useRef(null);

  useEffect(function () {
    try {
      var el = messagesEndRef.current;
      if (el) el.scrollIntoView({ behavior: "smooth", block: "end" });
    } catch (e) {}
  }, [messages, loading]);

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

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const token = window.localStorage.getItem("syntexa_token");
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
    var content = input.trim();
    if (!content || loading) return;
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
      var label =
        kind === "image"
          ? "imagem"
          : kind === "video"
            ? "video"
            : kind === "speech"
              ? "voz"
              : "audio";
      var userMsg = { role: "user", content: content };
      setMessages((prev) =>
        prev.concat([
          userMsg,
          {
            role: "assistant",
            content: "Gerando " + label + " no provedor real...",
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
              content: "Imagem gerada.",
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
            content:
              "Resposta do provedor real recebida, mas sem arquivo final ainda: " +
              JSON.stringify(result || {}),
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
          var fallback =
            kind === "image"
              ? "Não consegui gerar a imagem agora. Tente novamente em alguns instantes."
              : kind === "video"
                ? "Não consegui gerar o vídeo agora. Tente novamente em alguns instantes."
                : kind === "speech"
                  ? "Não consegui gerar a voz agora. Tente novamente em alguns instantes."
                  : "Não consegui gerar o áudio agora. Tente novamente em alguns instantes.";
          var out = netDown
            ? "API indisponível (não conectou em api.syntexabr.com.br). Verifique o servidor no Hetzner e nginx na porta 443."
            : msg && String(msg).trim().length > 0
              ? String(msg).trim()
              : fallback;
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

    // Fluxo padrão: chat textual (público ou autenticado).
    var nextHistory = messages.concat([{ role: "user", content: content }]);
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
            setMessages((prev) => prev.concat([{ role: "assistant", content: reply }]));
          } else {
            setMessages((prev) => prev.concat([{ role: "assistant", content: "" }]));
            const controller = new AbortController();
            abortRef.current = controller;
            setCanStop(true);
            try {
              await chatCompletionStream(token, nextHistory, function (chunk) {
                setMessages((prev) => {
                  var p = prev.slice();
                  var last = p[p.length - 1];
                  if (last && last.role === "assistant") {
                    p[p.length - 1] = { ...last, content: last.content + chunk };
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
            setMessages((prev) => prev.concat([{ role: "assistant", content: reply }]));
          } else {
            setMessages((prev) => prev.concat([{ role: "assistant", content: "" }]));
            const controller = new AbortController();
            abortRef.current = controller;
            setCanStop(true);
            try {
              await publicChatStream(nextHistory, function (chunk) {
                setMessages((prev) => {
                  var p = prev.slice();
                  var last = p[p.length - 1];
                  if (last && last.role === "assistant") {
                    p[p.length - 1] = { ...last, content: last.content + chunk };
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
          setMessages((prev) => prev.concat([{ role: "assistant", content: reply }]));
        } else {
          setMessages((prev) => prev.concat([{ role: "assistant", content: "" }]));
          const controller = new AbortController();
          abortRef.current = controller;
          setCanStop(true);
          try {
            await publicChatStream(nextHistory, function (chunk) {
              setMessages((prev) => {
                var p = prev.slice();
                var last = p[p.length - 1];
                if (last && last.role === "assistant") {
                  p[p.length - 1] = { ...last, content: last.content + chunk };
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
      var msg = err instanceof Error ? err.message : String(err);
      if (
        msg === "Failed to fetch" ||
        msg.indexOf("NetworkError") !== -1 ||
        msg.indexOf("Load failed") !== -1
      ) {
        msg =
          "não foi possível conectar à API (api.syntexabr.com.br). O servidor pode estar offline ou inacessível — verifique nginx/uvicorn no Hetzner e o DNS.";
      }
      setMessages((prev) => prev.concat([{ role: "assistant", content: "Erro: " + msg }]));
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  function handleNewConversation() {
    setMessages((prev) => prev.slice(0, 2));
    setAttachments([]);
    setCurrentSessionId(null);
  }

  function handleFilesChange(e) {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setAttachments(files);
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
              content: "Imagem gerada.",
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
              content: "Imagem gerada.",
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
                  ? "Vídeo gerado."
                  : kind === "speech"
                    ? "Fala gerada."
                    : "Áudio gerado.",
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
            content:
              "Não consegui gerar o arquivo de mídia agora. Tente novamente em alguns instantes.",
          },
        ])
      );
    } catch (err) {
      var raw = err instanceof Error ? err.message : String(err);
      var netDown =
        raw === "Failed to fetch" ||
        raw.indexOf("NetworkError") !== -1 ||
        raw.indexOf("Load failed") !== -1;
      var fallback =
        kind === "image"
          ? "Não consegui gerar a imagem agora. Tente novamente em alguns instantes."
          : kind === "video"
            ? "Não consegui gerar o vídeo agora. Tente novamente em alguns instantes."
            : kind === "speech"
              ? "Não consegui gerar a voz agora. Tente novamente em alguns instantes."
              : "Não consegui gerar o áudio agora. Tente novamente em alguns instantes.";
      var userMsg =
        netDown
          ? "API indisponível (não conectou em api.syntexabr.com.br). Verifique o servidor no Hetzner e nginx na porta 443."
          : raw && String(raw).trim().length > 0
            ? String(raw).trim()
            : fallback;
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
    React.createElement("div", { className: "flex min-h-0 w-full max-w-full flex-1 flex-col overflow-hidden" },
      React.createElement("div", { className: "flex min-h-0 flex-1 flex-col overflow-y-auto overflow-x-hidden overscroll-contain px-3 py-4 sm:px-8 sm:py-5" },
        React.createElement("div", { className: "mx-auto flex w-full max-w-3xl flex-col gap-4" },
          visible.map((m, idx) => {
            var cn = m.role === "user" ? "syntexa-bubble-user ml-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed break-words" : "syntexa-bubble-assistant mr-auto max-w-[85%] sm:max-w-[80%] px-4 py-3 sm:px-5 sm:py-4 text-sm leading-relaxed text-[var(--text-primary)] break-words";
            return React.createElement(motion.div, { key: idx, initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0.3, delay: idx * 0.03 }, className: cn },
              React.createElement("div", { className: "mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-white/50" }, m.role === "user" ? "Você" : "Syntexa"),
              (m.role === "assistant" && /^Gerando\s/i.test(String(m.content || "")))
                ? React.createElement(
                    "div",
                    { className: "flex items-center gap-2 whitespace-pre-wrap" },
                    React.createElement("span", { className: "syntexa-spinner", "aria-hidden": true }),
                    React.createElement("span", null, m.content)
                  )
                : React.createElement("p", { className: "whitespace-pre-wrap" }, m.content),
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
                      "mt-2 inline-flex items-center text-xs font-medium text-emerald-300 hover:text-emerald-200 underline decoration-emerald-400/70",
                  },
                  "Baixar imagem"
                ),
              m.media && m.media.type === "video" &&
                (String(m.media.url || "").startsWith("data:image/")
                  ? React.createElement("img", {
                      src: m.media.url,
                      alt: "Video gerado",
                      className: "mt-3 max-h-[420px] w-full rounded-xl border border-white/15 object-contain",
                    })
                  : React.createElement("video", {
                      src: m.media.url,
                      controls: true,
                      className: "mt-3 max-h-[420px] w-full rounded-xl border border-white/15",
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
                      "mt-2 inline-flex items-center text-xs font-medium text-emerald-300 hover:text-emerald-200 underline decoration-emerald-400/70",
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
                      "mt-2 inline-flex items-center text-xs font-medium text-emerald-300 hover:text-emerald-200 underline decoration-emerald-400/70",
                  },
                  "Baixar áudio"
                ));
          }),
          showTyping && React.createElement(motion.div, { initial: false, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25 }, className: "syntexa-bubble-assistant mr-auto max-w-[85%] sm:max-w-[80%] rounded-[18px] px-4 py-3 sm:px-5 sm:py-4" },
            React.createElement("div", { className: "mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-white/50" }, "Syntexa"),
            React.createElement("div", { className: "flex items-center gap-2 text-sm text-white/75" },
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
            "shrink-0 border-t border-white/10 bg-black/85 px-3 py-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] backdrop-blur-xl sm:px-8 sm:py-4",
        },
        React.createElement(
          "div",
          { className: "mx-auto flex w-full max-w-3xl flex-col gap-3" },
          attachments.length > 0 &&
            React.createElement(
              "div",
              { className: "flex flex-wrap items-center gap-2 text-xs text-white/80" },
              attachments.map((file) =>
                React.createElement(
                  "span",
                  {
                    key: file.name + file.size,
                    className:
                      "inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1.5",
                  },
                  React.createElement("span", { className: "h-2 w-2 rounded-full bg-emerald-400" }),
                  React.createElement("span", null, file.name)
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
                  disabled: loading || !input.trim(),
                  className:
                    "shrink-0 h-9 rounded-xl border border-white/20 bg-white/5 px-3 text-xs text-white/85 hover:bg-white/10 disabled:opacity-40 inline-flex items-center gap-1.5",
                },
                React.createElement(IconImage, null),
                "Imagem"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () { handleGenerateMedia("audio"); },
                  disabled: loading || !input.trim(),
                  className:
                    "shrink-0 h-9 rounded-xl border border-white/20 bg-white/5 px-3 text-xs text-white/85 hover:bg-white/10 disabled:opacity-40 inline-flex items-center gap-1.5",
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
                    "shrink-0 flex items-center justify-center w-10 h-10 rounded-xl border border-white/20 bg-white/5 hover:bg-white/10 text-white/80",
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
                  "syntexa-input min-h-[44px] max-h-28 flex-1 resize-none rounded-xl px-4 py-2.5 text-sm",
              }),
              recognition && React.createElement(
                "button",
                {
                  type: "button",
                  "aria-label": "Falar",
                  onClick: toggleVoice,
                  className:
                    "shrink-0 flex items-center justify-center w-10 h-10 rounded-xl border " +
                    (listening ? "border-red-400 bg-red-500/20 text-red-300" : "border-white/20 bg-white/5 hover:bg-white/10 text-white/80"),
                },
                listening
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
