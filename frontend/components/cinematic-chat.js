"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

/*
 * CinematicChat — UI premium para chat com streaming real
 * Tema escuro, glassmorphism, animações suaves
 */

import { getApiBase } from "../lib/api";
var API_BASE = getApiBase();

function SendIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function UserIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function AIIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  );
}

function StopIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  );
}

export default function CinematicChat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Olá. Sou a Syntexa AI. Infraestrutura cognitiva soberana à sua disposição. Como posso assistir?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const abortRef = useRef(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll para o fim
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
    }
  }, [input]);

  const handleSubmit = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);
    setStreamingText("");

    const allMessages = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const controller = new AbortController();
      abortRef.current = controller;

      const res = await fetch(`${API_BASE}/v1/public-chat/stream`, {
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
            const chunk = parsed.content || "";
            fullText += chunk;
            setStreamingText(fullText);
          } catch {
            // ignora linhas malformadas
          }
        }
      }

      setMessages((prev) => [...prev, { role: "assistant", content: fullText }]);
      setStreamingText("");
    } catch (err) {
      if (err.name === "AbortError") {
        setMessages((prev) => [...prev, { role: "assistant", content: streamingText || "Geração interrompida." }]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Erro: ${err.message}. Serviço pode estar temporariamente indisponível.` },
        ]);
      }
      setStreamingText("");
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [input, isLoading, messages, streamingText]);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex h-[100dvh] w-full flex-col bg-[#0a0a0b]">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-[rgba(255,255,255,0.05)] px-5 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#5A7A96]">
            <AIIcon className="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-[13px] font-medium tracking-[0.1em] text-[#e8e8ec]">SYNTEXA AI</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-[5px] w-[5px] rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.4)]" />
          <span className="text-[10px] font-medium tracking-wide text-emerald-400">SOBERANA</span>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <div
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                    msg.role === "user"
                      ? "bg-[rgba(99,102,241,0.15)] text-[#818cf8]"
                      : "bg-[rgba(255,255,255,0.05)] text-[#9a9aa0]"
                  }`}
                >
                  {msg.role === "user" ? (
                    <UserIcon className="h-3.5 w-3.5" />
                  ) : (
                    <AIIcon className="h-3.5 w-3.5" />
                  )}
                </div>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[rgba(99,102,241,0.12)] text-[#e8e8ec]"
                      : "bg-[rgba(255,255,255,0.03)] text-[#d0d0d5] border border-[rgba(255,255,255,0.04)]"
                  }`}
                >
                  {msg.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Streaming text */}
          {isLoading && streamingText && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3"
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[rgba(255,255,255,0.05)] text-[#9a9aa0]">
                <AIIcon className="h-3.5 w-3.5" />
              </div>
              <div className="max-w-[85%] rounded-2xl border border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-[14px] leading-relaxed text-[#d0d0d5]">
                {streamingText}
                <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-[#6366f1] align-middle" />
              </div>
            </motion.div>
          )}

          {/* Loading indicator (no streaming text yet) */}
          {isLoading && !streamingText && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-3"
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[rgba(255,255,255,0.05)] text-[#9a9aa0]">
                <AIIcon className="h-3.5 w-3.5" />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl border border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.03)] px-4 py-3">
                <span className="h-1.5 w-1.5 rounded-full bg-[#6366f1] animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="h-1.5 w-1.5 rounded-full bg-[#6366f1] animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="h-1.5 w-1.5 rounded-full bg-[#6366f1] animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </motion.div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-[rgba(255,255,255,0.05)] px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.02)] px-4 py-3">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Mensagem Syntexa AI..."
            className="max-h-[200px] w-full resize-none bg-transparent text-[14px] text-[#e8e8ec] placeholder-[#5a5a60] outline-none"
            disabled={isLoading}
          />
          {isLoading ? (
            <button
              onClick={handleStop}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[rgba(239,68,68,0.15)] text-red-400 transition-colors hover:bg-[rgba(239,68,68,0.25)]"
            >
              <StopIcon className="h-3.5 w-3.5" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-[#6366f1] to-[#4f46e5] text-white shadow-[0_0_12px_rgba(99,102,241,0.2)] transition-all hover:shadow-[0_0_20px_rgba(99,102,241,0.3)] disabled:opacity-30 disabled:shadow-none"
            >
              <SendIcon className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <p className="mt-2 text-center text-[10px] text-[#4a4a50]">
          Infraestrutura Cognitiva Soberana — Runtime Neural Distribuído
        </p>
      </div>
    </div>
  );
}
