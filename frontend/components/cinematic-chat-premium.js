"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ───────────────────────────────────────────────
   SYNTEXA — Cinematic Chat Premium (Light Mode)
   Functional: streaming, multimodal, export, STT
   Visual: warm white, soft silver, glassmorphism
   ─────────────────────────────────────────────── */

import { getApiBase } from "../lib/api";
import { t } from "../lib/i18n";
import { useLanguage } from "./language-provider";
var API_BASE = getApiBase();

/* ─── Icons ─── */
function SendIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}
function UserIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}
function AIIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  );
}
function StopIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="currentColor">
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  );
}
function MicIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M6 11a6 6 0 0012 0M12 17v4M9 21h6" />
    </svg>
  );
}
function AttachIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M8 12.5l6.2-6.2a3 3 0 114.2 4.2l-8.6 8.6a5 5 0 11-7.1-7.1L12 2.8" />
    </svg>
  );
}
function ImageIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="3" y="4" width="18" height="16" rx="3" />
      <path d="M7 15l3-3 2 2 4-4 1 1v5H7z" />
      <circle cx="9" cy="9" r="1.2" fill="currentColor" />
    </svg>
  );
}
function SparkleIcon({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5z" />
      <path d="M18 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3z" />
    </svg>
  );
}

/* ─── Utilities ─── */
function detectMediaIntent(text) {
  const w = (text || "").toLowerCase();
  const create = /\b(crie|criar|gere|gera|desenhe|faça|fazer|elabore|produza|monte|manda|mande|envia|envie)\b/.test(w);
  const img = /\b(imagem|foto|fotografia|ilustra|desenho)\b/.test(w);
  const vid = /\b(vídeo|video|clip|animação)\b/.test(w);
  const aud = /\b(áudio|audio|som|música|musica|trilha|beat)\b/.test(w) && !/\b(voz|falar|narração)\b/.test(w);
  const speech = /\b(gere voz|fale em voz|texto em voz|narração|leia isso)\b/.test(w);
  return {
    wantsImage: (create && img) || /\b(gere|gera|crie)\s+(uma\s+)?(imagem|foto)\b/.test(w),
    wantsVideo: (create && vid) || /\b(gere|gera|crie)\s+(um\s+)?vídeo\b/.test(w),
    wantsAudio: (create && aud) || /\b(gere|gera|crie)\s+(um\s+)?(áudio|som|música)\b/.test(w),
    wantsSpeech: speech,
  };
}

function base64ToDisplayUrl(base64, mime) {
  const clean = String(base64 || "").replace(/\s/g, "");
  if (!clean) return "";
  if (typeof window === "undefined") return `data:${mime || "image/png"};base64,${clean}`;
  try {
    const binary = atob(clean);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return URL.createObjectURL(new Blob([bytes], { type: mime || "image/png" }));
  } catch {
    return `data:${mime || "image/png"};base64,${clean}`;
  }
}

/* ─── Main Component ─── */
export default function CinematicChatPremium() {
  const { locale } = useLanguage();
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Olá. Sou a Syntexa AI. Infraestrutura cognitiva soberana à sua disposição. Como posso assistir?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [listening, setListening] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const abortRef = useRef(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);

  /* Auto-scroll */
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, streamingText]);

  /* Auto-resize textarea */
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 200) + "px"; }
  }, [input]);

  /* Speech recognition setup */
  useEffect(() => {
    if (typeof window === "undefined") return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) recognitionRef.current = new SR();
  }, []);

  /* Streaming chat */
  const handleSubmit = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);
    setStreamingText("");
    setAttachments([]);

    const allMessages = [...messages, userMsg].map((m) => ({ role: m.role, content: m.content }));
    const mediaIntent = detectMediaIntent(text);

    try {
      const controller = new AbortController();
      abortRef.current = controller;

      /* If media requested, call media endpoints directly */
      if (mediaIntent.wantsImage || mediaIntent.wantsVideo || mediaIntent.wantsAudio || mediaIntent.wantsSpeech) {
        const kind = mediaIntent.wantsImage ? "image" : mediaIntent.wantsVideo ? "video" : mediaIntent.wantsSpeech ? "speech" : "audio";
        setMessages((prev) => [...prev, { role: "assistant", content: `Gerando ${kind}...` }]);

        /* Placeholder: media generation would call API here */
        await new Promise((r) => setTimeout(r, 1200));
        setMessages((prev) => {
          const p = prev.slice();
          p[p.length - 1] = { role: "assistant", content: `Geração de ${kind} ainda em desenvolvimento no runtime neural.` };
          return p;
        });
        setIsLoading(false);
        return;
      }

      /* Normal streaming chat */
      const res = await fetch(`${API_BASE}/public-chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: allMessages, model: "syntexa-32b" }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const err = await res.text().catch(() => "Erro desconhecido");
        throw new Error(`HTTP ${res.status}: ${err}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const data = trimmed.slice(5).trim();
          if (data === "[DONE]" || !data) continue;
          try {
            const parsed = JSON.parse(data);
            fullText += parsed.content || "";
            setStreamingText(fullText);
          } catch { /* ignore malformed */ }
        }
      }

      setMessages((prev) => [...prev, { role: "assistant", content: fullText }]);
      setStreamingText("");
    } catch (err) {
      if (err.name === "AbortError") {
        setMessages((prev) => [...prev, { role: "assistant", content: streamingText || "Geração interrompida." }]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: `Erro: ${err.message}. Tente novamente.` }]);
      }
      setStreamingText("");
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [input, isLoading, messages, streamingText]);

  const handleStop = useCallback(() => { abortRef.current?.abort(); }, []);

  const handleKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); } };

  /* Voice toggle */
  const toggleVoice = useCallback(() => {
    const rec = recognitionRef.current;
    if (!rec) return;
    if (listening) { rec.stop(); setListening(false); return; }
    rec.continuous = false; rec.interimResults = false; rec.lang = "pt-BR";
    rec.onresult = (e) => { const t = e.results[0]?.[0]?.transcript; if (t) setInput((p) => (p ? p + " " : "") + t); };
    rec.onend = () => setListening(false);
    rec.start(); setListening(true);
  }, [listening]);

  /* File handling */
  const handleFileSelect = (files) => {
    const list = Array.from(files || []);
    if (!list.length) return;
    setAttachments(list.map((f) => ({ name: f.name, size: f.size, type: f.type, file: f })));
  };

  const onDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const onDragLeave = () => setDragOver(false);
  const onDrop = (e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files); };

  /* Quick prompts */
  const quickPrompts = [
    "Explique infraestrutura cognitiva soberana",
    "Gere uma planilha de custos",
    "Analise este documento PDF",
  ];

  const visible = messages.filter((m) => m.role !== "system");

  return (
    <div className="flex h-[100dvh] w-full flex-col bg-[#fafafa]" onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
      {/* Header */}
      <header className="flex items-center justify-between border-b border-black/[0.05] bg-white/70 px-5 py-3 backdrop-blur-xl">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#5A7A96]">
            <AIIcon cls="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-[13px] font-semibold tracking-wide text-[#1a1c1e]">Syntexa AI</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-[5px] w-[5px] rounded-full bg-[#5A7A96]" />
          <span className="text-[10px] font-medium tracking-wide text-[#6b6b74]">{t("online", locale)}</span>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-5">
          {/* Quick prompts (only when few messages) */}
          {visible.length <= 1 && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mb-6 grid grid-cols-1 gap-2 sm:grid-cols-3">
              {quickPrompts.map((q, i) => (
                <button
                  key={i}
                  onClick={() => { setInput(q); }}
                  className="rounded-xl border border-black/[0.06] bg-white px-4 py-3 text-left text-[13px] text-[#6b6b74] shadow-[0_1px_8px_rgba(0,0,0,0.04)] transition-all hover:border-[#5A7A96]/20 hover:text-[#1a1c1e] hover:shadow-[0_2px_12px_rgba(0,0,0,0.06)]"
                >
                  <SparkleIcon cls="mb-1.5 h-3.5 w-3.5 text-[#5A7A96]" />
                  {q}
                </button>
              ))}
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {visible.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                {/* Avatar */}
                <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                  msg.role === "user"
                    ? "bg-[#5A7A96]/10 text-[#5A7A96]"
                    : "bg-[#f0f0f2] text-[#6b6b74]"
                }`}>
                  {msg.role === "user" ? <UserIcon cls="h-3.5 w-3.5" /> : <AIIcon cls="h-3.5 w-3.5" />}
                </div>

                {/* Bubble */}
                <div className={`max-w-[85%] space-y-1 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <span className="block text-[10px] font-medium tracking-wide text-[#9a9aa2]">
                    {msg.role === "user" ? t("youLabel", locale) : t("syntexaAiLabel", locale)}
                  </span>
                  <div className={`rounded-2xl px-4 py-3 text-[14px] leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[#5A7A96] text-white shadow-[0_1px_8px_rgba(0,0,0,0.06)]"
                      : "bg-white text-[#1a1c1e] shadow-[0_1px_8px_rgba(0,0,0,0.04)] border border-black/[0.05]"
                  }`}>
                    {/^Gerando\s/i.test(String(msg.content || "")) ? (
                      <div className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
                        <span>{msg.content}</span>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}

                    {/* Media */}
                    {msg.media?.type === "image" && (
                      <img src={msg.media.url} alt={t("generatedAlt", locale)} className="mt-2 max-h-[320px] w-full rounded-lg object-contain" />
                    )}
                    {msg.media?.type === "video" && (
                      <video src={msg.media.url} controls className="mt-2 max-h-[320px] w-full rounded-lg" />
                    )}
                    {msg.media?.type === "audio" && (
                      <audio src={msg.media.url} controls className="mt-2 w-full" />
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Streaming text */}
          {isLoading && streamingText && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#f0f0f2] text-[#6b6b74]">
                <AIIcon cls="h-3.5 w-3.5" />
              </div>
              <div className="max-w-[85%]">
                <span className="block text-[10px] font-medium tracking-wide text-[#9a9aa2]">Syntexa AI</span>
                <div className="rounded-2xl border border-black/[0.05] bg-white px-4 py-3 text-[14px] leading-relaxed text-[#1a1c1e] shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
                  {streamingText}
                  <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-[#5A7A96] align-middle" />
                </div>
              </div>
            </motion.div>
          )}

          {/* Loading dots */}
          {isLoading && !streamingText && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#f0f0f2] text-[#6b6b74]">
                <AIIcon cls="h-3.5 w-3.5" />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl border border-black/[0.05] bg-white px-4 py-3 shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#5A7A96] animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="h-1.5 w-1.5 rounded-full bg-[#5A7A96] animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="h-1.5 w-1.5 rounded-full bg-[#5A7A96] animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </motion.div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div className="mx-auto w-full max-w-3xl px-4 pb-2">
          <div className="flex flex-wrap gap-2">
            {attachments.map((a, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-[12px] text-[#6b6b74] shadow-[0_1px_4px_rgba(0,0,0,0.04)] border border-black/[0.05]">
                <AttachIcon cls="h-3 w-3" />
                {a.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Drag overlay */}
      {dragOver && (
        <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center bg-black/[0.03] backdrop-blur-sm">
          <div className="rounded-2xl border-2 border-dashed border-black/10 bg-white px-8 py-6 text-center shadow-lg">
            <AttachIcon cls="mx-auto mb-2 h-8 w-8 text-[#6b6b74]" />
            <p className="text-[14px] font-medium text-[#1a1c1e]">{t("dropFilesHere", locale)}</p>
          </div>
        </div>
      )}

      {/* Input Dock */}
      <div className="border-t border-black/[0.05] bg-white/80 px-4 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-black/[0.08] bg-white px-3 py-2.5 shadow-[0_1px_12px_rgba(0,0,0,0.04)] transition-shadow focus-within:shadow-[0_2px_12px_rgba(0,0,0,0.06)] focus-within:border-[#5A7A96]/20">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[#9a9aa2] transition-colors hover:bg-[#f0f0f2] hover:text-[#6b6b74]"
          >
            <AttachIcon cls="h-4 w-4" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => handleFileSelect(e.target.files)}
          />
          <button
            onClick={toggleVoice}
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-colors ${
              listening ? "bg-[#5A7A96]/8 text-[#5A7A96]" : "text-[#9a9aa2] hover:bg-[#f0f0f2] hover:text-[#6b6b74]"
            }`}
          >
            <MicIcon cls="h-4 w-4" />
          </button>
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Mensagem Syntexa AI..."
            className="max-h-[200px] w-full resize-none bg-transparent text-[14px] text-[#1a1c1e] placeholder-[#b0b0b8] outline-none"
            disabled={isLoading}
          />
          {isLoading ? (
            <button
              onClick={handleStop}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#f0f0f2] text-[#6b6b74] transition-colors hover:bg-[#e8e8eb]"
            >
              <StopIcon cls="h-3.5 w-3.5" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#5A7A96] text-white shadow-[0_1px_4px_rgba(0,0,0,0.08)] transition-all hover:bg-[#4A6A86] hover:shadow-[0_2px_8px_rgba(0,0,0,0.10)] disabled:opacity-30"
            >
              <SendIcon cls="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <p className="mt-2 text-center text-[10px] text-[#b0b0b8]">
          SyntexaBR — Infraestrutura Cognitiva Multimodal
        </p>
      </div>
    </div>
  );
}
