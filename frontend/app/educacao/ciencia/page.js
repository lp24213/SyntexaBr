"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppShell } from "@/components/shell";
import { educationScienceStream, educationCompute } from "@/lib/api";
import { MathText } from "@/components/ui/math-renderer";
import { FuturisticIcon } from "@/components/icons/futuristic-icons";

// ─── Science area definitions ─────────────────────────────────────────────────
const SCIENCE_AREAS = [
  {
    id: "astronomia",
    label: "Astronomia & Cosmologia",
    iconName: "telescope",
    color: "from-indigo-500/20 to-purple-500/20",
    border: "border-indigo-500/30",
    badge: "text-indigo-300 border-indigo-500/20 bg-indigo-500/10",
    tags: ["Astrofísica", "Cosmologia", "Buracos Negros", "Exoplanetas", "Big Bang"],
    desc: "Da mecânica celeste à cosmologia moderna — buracos negros, galáxias e o início do universo.",
  },
  {
    id: "inteligencia_artificial",
    label: "Inteligência Artificial & ML",
    iconName: "brain",
    color: "from-cyan-500/20 to-blue-500/20",
    border: "border-cyan-500/30",
    badge: "text-cyan-300 border-cyan-500/20 bg-cyan-500/10",
    tags: ["Deep Learning", "NLP", "Transformers", "RL", "Visão Computacional"],
    desc: "Redes neurais, LLMs, aprendizado por reforço e ética em IA — da teoria à implementação.",
  },
  {
    id: "seguranca_digital",
    label: "Segurança Digital & Criptografia",
    iconName: "lock",
    color: "from-red-500/20 to-orange-500/20",
    border: "border-red-500/30",
    badge: "text-red-300 border-red-500/20 bg-red-500/10",
    tags: ["Criptografia", "Pentest Ético", "LGPD", "OWASP", "Zero Trust"],
    desc: "Criptografia, segurança ofensiva/defensiva, LGPD, GDPR e privacidade digital por design.",
  },
  {
    id: "computacao_quantica",
    label: "Computação Quântica",
    iconName: "quantum",
    color: "from-violet-500/20 to-pink-500/20",
    border: "border-violet-500/30",
    badge: "text-violet-300 border-violet-500/20 bg-violet-500/10",
    tags: ["Qubits", "Qiskit", "Entrelaçamento", "Shor", "Grover"],
    desc: "Superposição, entrelaçamento, algoritmos quânticos e o futuro da computação.",
  },
  {
    id: "bioinformatica",
    label: "Bioinformática & Genômica",
    iconName: "dna",
    color: "from-green-500/20 to-emerald-500/20",
    border: "border-green-500/30",
    badge: "text-green-300 border-green-500/20 bg-green-500/10",
    tags: ["Sequenciamento", "BLAST", "Proteômica", "CRISPR", "Bioconductor"],
    desc: "Análise genômica, sequenciamento NGS, estrutura de proteínas e biologia computacional.",
  },
  {
    id: "neurociencias",
    label: "Neurociências",
    iconName: "brain",
    color: "from-amber-500/20 to-yellow-500/20",
    border: "border-amber-500/30",
    badge: "text-amber-300 border-amber-500/20 bg-amber-500/10",
    tags: ["Neuroimagem", "Plasticidade", "BCI", "fMRI", "Neuropsicologia"],
    desc: "Da sinapse ao pensamento — neuroanatomia, cognição, aprendizado e interfaces cérebro-máquina.",
  },
  {
    id: "ciencias_ambientais",
    label: "Ciências Ambientais & Clima",
    iconName: "globe",
    color: "from-teal-500/20 to-green-500/20",
    border: "border-teal-500/30",
    badge: "text-teal-300 border-teal-500/20 bg-teal-500/10",
    tags: ["Mudança Climática", "IPCC", "Biodiversidade", "Energias Renováveis", "Carbono"],
    desc: "Mudanças climáticas, biodiversidade, ciclos biogeoquímicos e soluções sustentáveis.",
  },
  {
    id: "saude",
    label: "Ciências da Saúde",
    iconName: "cross",
    color: "from-pink-500/20 to-rose-500/20",
    border: "border-pink-500/30",
    badge: "text-pink-300 border-pink-500/20 bg-pink-500/10",
    tags: ["Epidemiologia", "Farmacologia", "Saúde Pública", "Anatomia", "Fisiologia"],
    desc: "Saúde pública, epidemiologia, farmacologia e ciências biomédicas para educação.",
  },
];

const LEVELS = [
  { id: "intermediario", label: "Médio" },
  { id: "avancado", label: "Graduação" },
  { id: "especialista", label: "Especialista" },
];

const LANGUAGES = [
  { id: "pt", label: "PT" },
  { id: "en", label: "EN" },
  { id: "es", label: "ES" },
  { id: "zh", label: "中文" },
];

// ─── Anonymous session ID helper ─────────────────────────────────────────────
function getOrCreateSessionId() {
  if (typeof window === "undefined") return "anon-ssr";
  let sid = sessionStorage.getItem("edu_science_sid");
  if (!sid) {
    sid = "sci-" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
    sessionStorage.setItem("edu_science_sid", sid);
  }
  return sid;
}

function loadHistory(sessionId, areaId) {
  if (typeof window === "undefined") return [];
  try {
    const key = `edu_science_${sessionId}_${areaId}`;
    return JSON.parse(sessionStorage.getItem(key) || "[]");
  } catch { return []; }
}

function saveHistory(sessionId, areaId, history) {
  if (typeof window === "undefined") return;
  const key = `edu_science_${sessionId}_${areaId}`;
  sessionStorage.setItem(key, JSON.stringify(history.slice(-40)));
}

// ─── Markdown-lite renderer ───────────────────────────────────────────────────
function renderText(text) {
  const lines = text.split("\n");
  const elements = [];
  let codeBlock = null;
  let key = 0;

  for (const raw of lines) {
    if (raw.startsWith("```")) {
      if (codeBlock === null) { codeBlock = []; }
      else {
        elements.push(
          React.createElement("pre", {
            key: key++,
            className: "my-2 overflow-x-auto rounded-xl border border-white/8 bg-black/40 p-3 text-xs text-green-300 font-mono",
          }, codeBlock.join("\n"))
        );
        codeBlock = null;
      }
      continue;
    }
    if (codeBlock !== null) { codeBlock.push(raw); continue; }
    if (!raw.trim()) { elements.push(React.createElement("br", { key: key++ })); continue; }
    if (raw.startsWith("### ")) {
      elements.push(React.createElement("p", { key: key++, className: "mt-3 mb-1 font-semibold text-white/90 text-sm" }, raw.slice(4)));
    } else if (raw.startsWith("## ")) {
      elements.push(React.createElement("p", { key: key++, className: "mt-4 mb-1 font-bold text-white text-base" }, raw.slice(3)));
    } else if (raw.startsWith("# ")) {
      elements.push(React.createElement("p", { key: key++, className: "mt-4 mb-2 font-bold text-white text-lg" }, raw.slice(2)));
    } else if (raw.startsWith("- ") || raw.startsWith("* ")) {
      elements.push(
        React.createElement("p", { key: key++, className: "pl-3 text-white/80 text-sm" },
          React.createElement("span", { className: "mr-2 text-white/40" }, "·"),
          raw.slice(2)
        )
      );
    } else if (/^\d+\. /.test(raw)) {
      elements.push(React.createElement("p", { key: key++, className: "pl-3 text-white/80 text-sm" }, raw));
    } else {
      elements.push(React.createElement("p", { key: key++, className: "text-white/80 text-sm leading-relaxed" }, raw));
    }
  }
  return React.createElement("div", { className: "space-y-0.5" }, ...elements);
}

// ─── Chat panel ───────────────────────────────────────────────────────────────
function ScienceChatPanel({ area, level, language, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sessionId] = useState(getOrCreateSessionId);
  const abortRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    const saved = loadHistory(sessionId, area.id);
    setMessages(saved);
  }, [area.id, sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(async () => {
    if (!input.trim() || streaming) return;
    const userMsg = { role: "user", content: input.trim() };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    setStreaming(true);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    const historyForApi = nextMessages.slice(-14).map((m) => ({ role: m.role, content: m.content }));
    let aiText = "";

    setMessages((prev) => [...prev, { role: "assistant", content: "", streaming: true }]);

    try {
      await educationScienceStream(
        area.id, userMsg.content, level, language, historyForApi.slice(0, -1),
        (chunk) => {
          aiText += chunk;
          setMessages((prev) => {
            const copy = [...prev];
            copy[copy.length - 1] = { role: "assistant", content: aiText, streaming: true };
            return copy;
          });
        },
        ctrl.signal
      );
    } catch (e) {
      if (e?.name !== "AbortError") {
        aiText = "Erro ao processar consulta. Verifique a conexão e tente novamente.";
      }
    }

    setMessages((prev) => {
      const copy = [...prev];
      copy[copy.length - 1] = { role: "assistant", content: aiText, streaming: false };
      const toSave = copy;
      saveHistory(sessionId, area.id, toSave);
      return toSave;
    });
    setStreaming(false);
  }, [input, streaming, messages, area.id, level, language, sessionId]);

  const stop = () => { abortRef.current?.abort(); setStreaming(false); };
  const clear = () => {
    setMessages([]);
    saveHistory(sessionId, area.id, []);
  };

  return React.createElement(
    motion.div,
    { initial: { opacity: 0, x: 20 }, animate: { opacity: 1, x: 0 }, className: "flex flex-col h-full" },

    // Header
    React.createElement(
      "div",
      { className: `mb-4 flex items-center justify-between gap-3 rounded-2xl border ${area.border} bg-gradient-to-r ${area.color} p-4` },
      React.createElement(
        "div",
        { className: "flex items-center gap-3" },
        React.createElement("button", {
          onClick: onBack,
          className: "rounded-xl border border-white/10 bg-white/5 p-2 text-white/60 hover:bg-white/10 hover:text-white transition-colors",
        }, "←"),
        React.createElement(FuturisticIcon, { name: area.iconName, className: "h-8 w-8 text-sky-400/85" }),
        React.createElement(
          "div",
          null,
          React.createElement("h2", { className: "font-semibold text-white text-sm" }, area.label),
          React.createElement("p", { className: "text-xs text-white/40 mt-0.5" }, `Sessão anônima · ${sessionId.slice(0, 12)}`)
        )
      ),
      React.createElement(
        "div",
        { className: "flex gap-2" },
        React.createElement("button", {
          onClick: clear,
          className: "rounded-xl border border-white/8 bg-white/4 px-3 py-1.5 text-xs text-white/50 hover:bg-white/8 transition-colors",
        }, "Limpar")
      )
    ),

    // Messages
    React.createElement(
      "div",
      { className: "flex-1 overflow-y-auto space-y-4 pr-1" },
      messages.length === 0 && React.createElement(
        "div",
        { className: "flex flex-col items-center justify-center py-16 text-center gap-3" },
        React.createElement(FuturisticIcon, { name: area.iconName, className: "h-14 w-14 opacity-40 text-white/30" }),
        React.createElement("p", { className: "text-white/30 text-sm max-w-xs" }, area.desc),
        React.createElement(
          "div",
          { className: "flex flex-wrap gap-1.5 justify-center mt-2" },
          area.tags.map((t) =>
            React.createElement(
              "button",
              {
                key: t,
                onClick: () => setInput("Explique " + t),
                className: `rounded-full border px-2.5 py-1 text-xs transition-colors hover:bg-white/8 ${area.badge}`,
              },
              t
            )
          )
        )
      ),
      messages.map((msg, i) =>
        React.createElement(
          motion.div,
          {
            key: i,
            initial: { opacity: 0, y: 6 },
            animate: { opacity: 1, y: 0 },
            className: `flex ${msg.role === "user" ? "justify-end" : "justify-start"}`,
          },
          React.createElement(
            "div",
            {
              className: msg.role === "user"
                ? "max-w-[80%] rounded-2xl rounded-tr-sm bg-white/8 border border-white/10 px-4 py-3 text-sm text-white"
                : "max-w-[88%] rounded-2xl rounded-tl-sm border border-white/8 bg-[rgba(15,23,42,0.6)] px-4 py-3",
            },
            msg.role === "user"
              ? React.createElement("p", { className: "text-sm text-white" }, msg.content)
              : React.createElement(
                  "div",
                  null,
                  React.createElement(MathText, { text: msg.content || "" }),
                  msg.streaming && React.createElement(
                    "span",
                    { className: "inline-block w-1.5 h-3 ml-1 bg-white/40 rounded-sm animate-pulse" }
                  )
                )
          )
        )
      ),
      React.createElement("div", { ref: bottomRef })
    ),

    // Input
    React.createElement(
      "div",
      { className: "mt-4 flex gap-2" },
      React.createElement("textarea", {
        value: input,
        onChange: (e) => setInput(e.target.value),
        onKeyDown: (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } },
        placeholder: `Pergunte sobre ${area.label}… (Enter para enviar)`,
        disabled: streaming,
        rows: 2,
        className: "flex-1 resize-none rounded-2xl border border-white/10 bg-white/4 px-4 py-3 text-sm text-white placeholder-white/30 outline-none focus:border-white/20 transition-colors disabled:opacity-50",
      }),
      React.createElement(
        "button",
        {
          onClick: streaming ? stop : send,
          disabled: !streaming && !input.trim(),
          className: `rounded-2xl px-4 py-2 text-sm font-medium transition-all ${
            streaming
              ? "border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20"
              : "border border-white/10 bg-white/6 text-white hover:bg-white/10 disabled:opacity-30"
          }`,
        },
        streaming ? "Parar" : "Enviar"
      )
    )
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function CienciaPage() {
  const [activeArea, setActiveArea] = useState(null);
  const [level, setLevel] = useState("avancado");
  const [language, setLanguage] = useState("pt");

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto max-w-5xl px-4 py-10" },

      // ── Hero ──────────────────────────────────────────────────────────
      !activeArea && React.createElement(
        motion.div,
        { initial: { opacity: 0, y: -12 }, animate: { opacity: 1, y: 0 }, className: "mb-8 text-center" },
        React.createElement(
          "div",
          { className: "mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/4 px-3 py-1 text-xs text-white/50" },
          React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" }),
          "Acesso público · Sessão 100% anônima"
        ),
        React.createElement("h1", { className: "text-3xl font-bold text-white mb-2" }, "Ciência & Tecnologia"),
        React.createElement("p", { className: "text-white/50 text-sm max-w-xl mx-auto" },
          "Portal de alto nível para pesquisa científica, segurança digital, IA, computação quântica e mais. " +
          "Nenhum dado é armazenado — sessões efêmeras protegidas por padrão."
        )
      ),

      // ── Settings bar ──────────────────────────────────────────────────
      !activeArea && React.createElement(
        motion.div,
        { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { delay: 0.1 },
          className: "mb-8 flex flex-wrap items-center gap-3 justify-center" },

        React.createElement("span", { className: "text-xs text-white/30" }, "Nível:"),
        LEVELS.map((l) =>
          React.createElement(
            "button",
            {
              key: l.id,
              onClick: () => setLevel(l.id),
              className: `rounded-xl border px-3 py-1.5 text-xs transition-colors ${
                level === l.id
                  ? "border-white/20 bg-white/10 text-white"
                  : "border-white/8 bg-transparent text-white/40 hover:text-white/60"
              }`,
            },
            l.label
          )
        ),

        React.createElement("span", { className: "text-xs text-white/20" }, "|"),
        React.createElement("span", { className: "text-xs text-white/30" }, "Idioma:"),
        LANGUAGES.map((lg) =>
          React.createElement(
            "button",
            {
              key: lg.id,
              onClick: () => setLanguage(lg.id),
              className: `rounded-xl border px-3 py-1.5 text-xs transition-colors ${
                language === lg.id
                  ? "border-white/20 bg-white/10 text-white"
                  : "border-white/8 bg-transparent text-white/40 hover:text-white/60"
              }`,
            },
            lg.label
          )
        )
      ),

      // ── Area grid ─────────────────────────────────────────────────────
      !activeArea && React.createElement(
        "div",
        { className: "grid gap-4 sm:grid-cols-2 lg:grid-cols-2" },
        SCIENCE_AREAS.map((area, idx) =>
          React.createElement(
            motion.button,
            {
              key: area.id,
              initial: { opacity: 0, y: 16 },
              animate: { opacity: 1, y: 0 },
              transition: { delay: 0.08 * idx },
              onClick: () => setActiveArea(area),
              className: `rounded-2xl border ${area.border} bg-gradient-to-br ${area.color} p-5 text-left transition-all hover:scale-[1.01] hover:border-white/20`,
            },
            React.createElement(
              "div",
              { className: "flex items-start gap-3 mb-3" },
              React.createElement(FuturisticIcon, { name: area.iconName, className: "h-7 w-7 mt-0.5 text-sky-400/80" }),
              React.createElement(
                "div",
                { className: "flex-1" },
                React.createElement("h3", { className: "font-semibold text-white text-sm mb-0.5" }, area.label),
                React.createElement("p", { className: "text-xs text-white/45 leading-relaxed" }, area.desc)
              )
            ),
            React.createElement(
              "div",
              { className: "flex flex-wrap gap-1.5" },
              area.tags.slice(0, 3).map((t) =>
                React.createElement(
                  "span",
                  { key: t, className: `rounded-full border px-2 py-0.5 text-xs ${area.badge}` },
                  t
                )
              )
            )
          )
        )
      ),

      // ── Privacy notice (bottom of grid) ─────────────────────────────
      !activeArea && React.createElement(
        motion.div,
        { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { delay: 0.7 },
          className: "mt-8 rounded-2xl border border-white/6 bg-white/2 p-4 text-center" },
        React.createElement("p", { className: "text-xs text-white/25" },
          "Privacidade garantida — nenhuma mensagem, IP ou dado pessoal é armazenado. " +
          "Sessões são efêmeras e ficam apenas na memória do seu navegador. " +
          "Conforme LGPD (Lei 13.709/2018) e princípios de Privacy by Design."
        )
      ),

      // ── Active chat ──────────────────────────────────────────────────
      activeArea && React.createElement(
        "div",
        { className: "h-[calc(100vh-120px)] flex flex-col" },
        React.createElement(ScienceChatPanel, {
          area: activeArea,
          level,
          language,
          onBack: () => setActiveArea(null),
        })
      )
    )
  );
}
