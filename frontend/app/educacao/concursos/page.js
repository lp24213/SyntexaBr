"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { AppShell } from "@/components/shell";
import { concursosTutorStream, gradeEnemEssayStream } from "@/lib/api";
import { FuturisticIcon } from "@/components/icons/futuristic-icons";

// ─── Exam definitions ─────────────────────────────────────────────────────────
const EXAMS = [
  {
    id: "enem",
    label: "ENEM",
    iconName: "medal",
    full: "Exame Nacional do Ensino Médio",
    color: "from-sky-500/20 to-cyan-500/20",
    border: "border-sky-500/30",
    badge: "text-sky-300 border-sky-500/20 bg-sky-500/10",
    subjects: ["Linguagens", "Matemática", "Ciências da Natureza", "Ciências Humanas"],
    tags: ["BNCC", "Vestibular", "Prouni", "Sisu", "Fies"],
    tip: "Redação e questões de múltipla escolha. Use o modo Simulado para praticar questões no formato real.",
  },
  {
    id: "oab",
    label: "OAB",
    iconName: "scale",
    full: "Exame da Ordem dos Advogados do Brasil",
    color: "from-amber-500/20 to-yellow-500/20",
    border: "border-amber-500/30",
    badge: "text-amber-300 border-amber-500/20 bg-amber-500/10",
    subjects: ["Direito Constitucional", "Civil", "Penal", "Trabalhista", "Tributário", "Processual"],
    tags: ["FGV", "CESPE", "Primeira fase", "Segunda fase", "Peça prática"],
    tip: "Cite artigos de lei, jurisprudência (STF/STJ) e a doutrina majoritária nas respostas.",
  },
  {
    id: "residencia",
    label: "Residência Médica",
    iconName: "cross",
    full: "Concurso para Residência Médica",
    color: "from-rose-500/20 to-pink-500/20",
    border: "border-rose-500/30",
    badge: "text-rose-300 border-rose-500/20 bg-rose-500/10",
    subjects: ["Clínica Médica", "Cirurgia", "Pediatria", "GO", "Psiquiatria", "MFC"],
    tags: ["USP", "UNIFESP", "UFRJ", "SUSep", "ACLS", "ATLS"],
    tip: "Foco em raciocínio clínico, diagnóstico diferencial e condutas baseadas em evidências.",
  },
  {
    id: "fuvest",
    label: "FUVEST / Unicamp",
    iconName: "building",
    full: "Vestibulares de Universidades Públicas",
    color: "from-violet-500/20 to-purple-500/20",
    border: "border-violet-500/30",
    badge: "text-violet-300 border-violet-500/20 bg-violet-500/10",
    subjects: ["Redação", "Português", "Matemática", "Ciências", "História", "Geografia"],
    tags: ["USP", "Unicamp", "UNESP", "Discursiva", "Interpretação"],
    tip: "Questões discursivas exigem respostas completas com fundamentação e repertório cultural.",
  },
  {
    id: "enade",
    label: "ENADE",
    iconName: "book",
    full: "Exame Nacional de Desempenho dos Estudantes",
    color: "from-green-500/20 to-emerald-500/20",
    border: "border-green-500/30",
    badge: "text-green-300 border-green-500/20 bg-green-500/10",
    subjects: ["Formação Geral", "Componente Específico", "Ciências", "Humanas"],
    tags: ["INEP", "Formação superior", "Competências profissionais"],
    tip: "Avalia competências profissionais integradas com temas sociais e científicos contemporâneos.",
  },
  {
    id: "concurso_geral",
    label: "Concurso Público",
    iconName: "medal",
    full: "Concursos Federais e Estaduais",
    color: "from-indigo-500/20 to-blue-500/20",
    border: "border-indigo-500/30",
    badge: "text-indigo-300 border-indigo-500/20 bg-indigo-500/10",
    subjects: ["Português", "Raciocínio Lógico", "Direito Adm.", "Informática", "Atualidades"],
    tags: ["CESPE", "FCC", "VUNESP", "FGV", "Agentes", "Analistas"],
    tip: "Foco em bancas: CESPE (certo/errado), FCC (letra de lei), FGV (interpretação).",
  },
];

const MODES = [
  { id: "chat", label: "Tirar Dúvida", iconName: "chat" },
  { id: "simulado", label: "Questão de Prova", iconName: "clipboard" },
  { id: "resumo", label: "Resumo do Assunto", iconName: "doc" },
  { id: "redacao", label: "Corrigir Redação", iconName: "pencil" },
];

const LANGUAGES = [
  { id: "pt", label: "PT" },
  { id: "en", label: "EN" },
  { id: "es", label: "ES" },
];

// ─── Session helpers ──────────────────────────────────────────────────────────
function getOrCreateSession() {
  if (typeof window === "undefined") return "anon-ssr";
  let sid = sessionStorage.getItem("edu_concursos_sid");
  if (!sid) {
    sid = "con-" + Math.random().toString(36).slice(2, 9) + "-" + Date.now().toString(36);
    sessionStorage.setItem("edu_concursos_sid", sid);
  }
  return sid;
}

function loadHistory(sid, examId) {
  if (typeof window === "undefined") return [];
  try { return JSON.parse(sessionStorage.getItem(`edu_con_${sid}_${examId}`) || "[]"); }
  catch { return []; }
}

function saveHistory(sid, examId, msgs) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(`edu_con_${sid}_${examId}`, JSON.stringify(msgs.slice(-40)));
}

// ─── Simple markdown renderer ─────────────────────────────────────────────────
function renderText(text) {
  const lines = (text || "").split("\n");
  const els = [];
  let code = null;
  let k = 0;
  for (const raw of lines) {
    if (raw.startsWith("```")) {
      if (code === null) code = [];
      else {
        els.push(React.createElement("pre", { key: k++, className: "my-2 overflow-x-auto rounded-xl border border-white/8 bg-black/40 p-3 text-xs text-green-300 font-mono" }, code.join("\n")));
        code = null;
      }
      continue;
    }
    if (code !== null) { code.push(raw); continue; }
    if (!raw.trim()) { els.push(React.createElement("br", { key: k++ })); continue; }
    if (raw.startsWith("## ")) els.push(React.createElement("p", { key: k++, className: "mt-3 mb-1 font-bold text-white text-base" }, raw.slice(3)));
    else if (raw.startsWith("# ")) els.push(React.createElement("p", { key: k++, className: "mt-4 mb-2 font-bold text-white text-lg" }, raw.slice(2)));
    else if (raw.startsWith("**") && raw.endsWith("**")) els.push(React.createElement("p", { key: k++, className: "font-semibold text-white/90 text-sm" }, raw.slice(2, -2)));
    else if (raw.startsWith("- ") || raw.startsWith("* ")) els.push(React.createElement("p", { key: k++, className: "pl-3 text-white/80 text-sm" }, React.createElement("span", { className: "mr-2 text-white/30" }, "·"), raw.slice(2)));
    else if (/^\d+\. /.test(raw)) els.push(React.createElement("p", { key: k++, className: "pl-3 text-white/80 text-sm" }, raw));
    else els.push(React.createElement("p", { key: k++, className: "text-white/80 text-sm leading-relaxed" }, raw));
  }
  return React.createElement("div", { className: "space-y-0.5" }, ...els);
}

// ─── Chat panel ───────────────────────────────────────────────────────────────
function ConcursoChat({ exam, mode, subject, language, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [essayText, setEssayText] = useState("");
  const [essayTheme, setEssayTheme] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sessionId] = useState(getOrCreateSession);
  const abortRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    const saved = loadHistory(sessionId, exam.id + "_" + mode);
    setMessages(saved.length > 0 ? saved : [{
      role: "assistant",
      content: `Olá! Sou seu tutor especializado em **${exam.full}**.\n\nModo atual: **${MODES.find(m => m.id === mode)?.label}**${subject ? ` · Disciplina: ${subject}` : ""}\n\nComo posso ajudar?`,
    }]);
  }, [exam.id, mode, subject, sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (messages.length > 0) saveHistory(sessionId, exam.id + "_" + mode, messages);
  }, [messages, exam.id, mode, sessionId]);

  const send = useCallback(async () => {
    if (streaming) return;

    // Essay mode
    if (mode === "redacao") {
      const essay = essayText.trim();
      if (essay.length < 50) return;
      const userMsg = { role: "user", content: `**Redação enviada**${essayTheme ? ` — Tema: ${essayTheme}` : ""}\n\n${essay}` };
      setMessages(prev => [...prev, userMsg, { role: "assistant", content: "" }]);
      setStreaming(true);
      const ctrl = new AbortController(); abortRef.current = ctrl;
      try {
        await gradeEnemEssayStream(essay, essayTheme, language, (chunk) => {
          setMessages(prev => {
            const c = [...prev]; const l = c[c.length - 1];
            if (l?.role === "assistant") c[c.length - 1] = { ...l, content: l.content + chunk };
            return c;
          });
        }, ctrl.signal);
      } catch (e) { if (e?.name !== "AbortError") {} }
      setStreaming(false); abortRef.current = null;
      setEssayText(""); setEssayTheme("");
      return;
    }

    const q = input.trim();
    if (!q) return;

    const fullQuestion = mode === "simulado"
      ? `Gere uma questão de múltipla escolha (A-E) no estilo real de ${exam.full}${subject ? ` sobre ${subject}` : ""}: ${q}`
      : mode === "resumo"
      ? `Faça um resumo completo e didático sobre: ${q}`
      : q;

    setMessages(prev => [...prev, { role: "user", content: q }, { role: "assistant", content: "" }]);
    setInput("");
    setStreaming(true);
    const ctrl = new AbortController(); abortRef.current = ctrl;

    const hist = messages.slice(-12).map(m => ({ role: m.role, content: m.content }));

    try {
      await concursosTutorStream(
        exam.id, subject || "geral", fullQuestion, "avancado", language, hist,
        (chunk) => {
          setMessages(prev => {
            const c = [...prev]; const l = c[c.length - 1];
            if (l?.role === "assistant") c[c.length - 1] = { ...l, content: l.content + chunk };
            return c;
          });
        }, ctrl.signal
      );
    } catch (e) { if (e?.name !== "AbortError") {} }
    setStreaming(false); abortRef.current = null;
  }, [input, essayText, essayTheme, streaming, messages, exam, mode, subject, language, sessionId]);

  const exportChat = () => {
    const header = `# ${exam.full} · ${MODES.find(m => m.id === mode)?.label}\n> Anônimo · ${new Date().toLocaleString("pt-BR")}\n\n---\n\n`;
    const body = messages.map(m => `**${m.role === "user" ? "Você" : "Tutor"}**\n\n${m.content}\n\n---\n`).join("\n");
    const blob = new Blob([header + body], { type: "text/markdown" });
    const url = URL.createObjectURL(blob); const a = document.createElement("a");
    a.href = url; a.download = `${exam.id}-${mode}-${Date.now()}.md`; a.click();
    URL.revokeObjectURL(url);
  };

  return React.createElement(
    motion.div,
    { initial: { opacity: 0, x: 16 }, animate: { opacity: 1, x: 0 }, className: "flex flex-col h-full" },

    // Header
    React.createElement("div", { className: `mb-4 flex items-center justify-between gap-3 rounded-2xl border ${exam.border} bg-gradient-to-r ${exam.color} p-4 flex-wrap` },
      React.createElement("div", { className: "flex items-center gap-3" },
        React.createElement("button", { onClick: onBack, className: "rounded-xl border border-white/10 bg-white/5 p-2 text-white/60 hover:bg-white/10 hover:text-white transition-colors" }, "←"),
        React.createElement(FuturisticIcon, { name: exam.iconName, className: "h-7 w-7 text-sky-400/85" }),
        React.createElement("div", null,
          React.createElement("h2", { className: "font-semibold text-white text-sm" }, exam.label),
          React.createElement("p", { className: "text-xs text-white/40" }, `${MODES.find(m => m.id === mode)?.label}${subject ? " · " + subject : ""}`)
        )
      ),
      React.createElement("div", { className: "flex gap-2" },
        React.createElement("button", { onClick: exportChat, title: "Exportar como .md", className: "rounded-xl border border-white/8 bg-white/4 px-3 py-1.5 text-xs text-white/50 hover:bg-white/8" }, "⬇ Exportar"),
        React.createElement("button", { onClick: () => { setMessages([]); saveHistory(sessionId, exam.id + "_" + mode, []); }, className: "rounded-xl border border-white/8 bg-white/4 px-3 py-1.5 text-xs text-white/50 hover:bg-white/8" }, "Limpar")
      )
    ),

    // Messages
    React.createElement("div", { className: "flex-1 overflow-y-auto space-y-4 pr-1" },
      messages.map((msg, i) =>
        React.createElement(motion.div, { key: i, initial: { opacity: 0, y: 4 }, animate: { opacity: 1, y: 0 }, className: `flex ${msg.role === "user" ? "justify-end" : "justify-start"}` },
          React.createElement("div", {
            className: msg.role === "user"
              ? "max-w-[80%] rounded-2xl rounded-tr-sm bg-white/8 border border-white/10 px-4 py-3 text-sm text-white"
              : "max-w-[90%] rounded-2xl rounded-tl-sm border border-white/8 bg-[rgba(12,20,40,0.7)] px-4 py-3",
          },
            msg.role === "user"
              ? React.createElement("p", { className: "text-sm" }, msg.content)
              : React.createElement("div", null,
                  renderText(msg.content || ""),
                  msg.content === "" && React.createElement("span", { className: "inline-block w-1.5 h-3 bg-white/40 rounded-sm animate-pulse" })
                )
          )
        )
      ),
      React.createElement("div", { ref: bottomRef })
    ),

    // Input
    mode === "redacao"
      ? React.createElement("div", { className: "mt-4 space-y-2" },
          React.createElement("input", { value: essayTheme, onChange: e => setEssayTheme(e.target.value), placeholder: "Tema da redação...", className: "w-full rounded-xl border border-white/8 bg-white/4 px-4 py-2 text-xs text-white placeholder-white/25 outline-none focus:border-white/20" }),
          React.createElement("textarea", { value: essayText, onChange: e => setEssayText(e.target.value), rows: 7, disabled: streaming, placeholder: "Cole sua redação aqui para correção nas 5 competências do ENEM (0-1000)...", className: "w-full resize-none rounded-2xl border border-white/8 bg-white/4 px-4 py-3 text-sm text-white placeholder-white/20 outline-none focus:border-white/20 disabled:opacity-50" }),
          React.createElement("button", { onClick: streaming ? () => abortRef.current?.abort() : send, disabled: !streaming && essayText.trim().length < 50, className: `w-full rounded-xl border py-2.5 text-sm font-medium transition-all inline-flex items-center justify-center gap-2 ${streaming ? "border-red-500/30 bg-red-500/10 text-red-300" : "border-sky-500/30 bg-sky-500/10 text-sky-300 disabled:opacity-30"}` }, streaming ? "Parar" : React.createElement(React.Fragment, null, React.createElement(FuturisticIcon, { name: "doc", className: "h-4 w-4" }), "Corrigir Redação"))
        )
      : React.createElement("div", { className: "mt-4 flex gap-2" },
          React.createElement("textarea", { value: input, onChange: e => setInput(e.target.value), onKeyDown: e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }, rows: 2, disabled: streaming, placeholder: mode === "simulado" ? `Diga o tópico e gerei uma questão real de ${exam.label}...` : mode === "resumo" ? "Digite o assunto para resumir..." : `Dúvida sobre ${exam.label}...`, className: "flex-1 resize-none rounded-2xl border border-white/8 bg-white/4 px-4 py-3 text-sm text-white placeholder-white/25 outline-none focus:border-white/20 disabled:opacity-50" }),
          React.createElement("button", { onClick: streaming ? () => abortRef.current?.abort() : send, disabled: !streaming && !input.trim(), className: `rounded-2xl px-4 py-2 text-sm font-medium transition-all ${streaming ? "border border-red-500/30 bg-red-500/10 text-red-300" : "border border-white/10 bg-white/6 text-white hover:bg-white/10 disabled:opacity-30"}` }, streaming ? "Parar" : "Enviar")
        )
  );
}

// ─── Exam selector ────────────────────────────────────────────────────────────
function ExamSelector({ onSelect }) {
  return React.createElement("div", { className: "grid gap-4 sm:grid-cols-2 lg:grid-cols-3" },
    EXAMS.map((exam, idx) =>
      React.createElement(motion.button, {
        key: exam.id,
        initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, transition: { delay: 0.06 * idx },
        onClick: () => onSelect(exam),
        className: `rounded-2xl border ${exam.border} bg-gradient-to-br ${exam.color} p-5 text-left transition-all hover:scale-[1.01] hover:border-white/25`,
      },
        React.createElement("div", { className: "flex items-start gap-3 mb-3" },
          React.createElement(FuturisticIcon, { name: exam.iconName, className: "h-8 w-8 mt-0.5 text-sky-400/85" }),
          React.createElement("div", { className: "flex-1" },
            React.createElement("h3", { className: "font-semibold text-white text-sm mb-0.5" }, exam.label),
            React.createElement("p", { className: "text-xs text-white/40 leading-relaxed" }, exam.full)
          )
        ),
        React.createElement("p", { className: "text-xs text-white/30 mb-3 leading-relaxed" }, exam.tip),
        React.createElement("div", { className: "flex flex-wrap gap-1.5" },
          exam.tags.slice(0, 4).map(t =>
            React.createElement("span", { key: t, className: `rounded-full border px-2 py-0.5 text-[10px] ${exam.badge}` }, t)
          )
        )
      )
    )
  );
}

// ─── Mode/subject selector ────────────────────────────────────────────────────
function ModeSelector({ exam, language, setLanguage, onConfirm }) {
  const [mode, setMode] = useState("chat");
  const [subject, setSubject] = useState("");

  return React.createElement(motion.div, { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, className: "max-w-lg mx-auto space-y-5" },
    React.createElement("div", { className: `rounded-2xl border ${exam.border} bg-gradient-to-r ${exam.color} p-4 flex items-center gap-3` },
      React.createElement(FuturisticIcon, { name: exam.iconName, className: "h-8 w-8 text-sky-400/85" }),
      React.createElement("div", null,
        React.createElement("h2", { className: "font-bold text-white" }, exam.label),
        React.createElement("p", { className: "text-xs text-white/40" }, exam.full)
      )
    ),
    React.createElement("div", { className: "rounded-2xl border border-white/8 bg-white/3 p-4 space-y-3" },
      React.createElement("p", { className: "text-xs font-medium text-white/50 uppercase tracking-wider" }, "Modo"),
      React.createElement("div", { className: "grid grid-cols-2 gap-2" },
        MODES.map(m => React.createElement("button", {
          key: m.id, onClick: () => setMode(m.id),
          className: `rounded-xl border px-3 py-2.5 text-left text-xs transition-all ${mode === m.id ? `${exam.border} bg-white/8 text-white font-medium` : "border-white/8 text-white/40 hover:text-white/70"}`,
        }, React.createElement(FuturisticIcon, { name: m.iconName, className: "h-4 w-4 mr-1.5 inline-block" }), m.label))
      )
    ),
    React.createElement("div", { className: "rounded-2xl border border-white/8 bg-white/3 p-4 space-y-3" },
      React.createElement("p", { className: "text-xs font-medium text-white/50 uppercase tracking-wider" }, "Disciplina / Área (opcional)"),
      React.createElement("div", { className: "flex flex-wrap gap-1.5" },
        exam.subjects.map(s => React.createElement("button", {
          key: s, onClick: () => setSubject(subject === s ? "" : s),
          className: `rounded-full border px-2.5 py-1 text-xs transition-colors ${subject === s ? `${exam.badge}` : "border-white/8 text-white/35 hover:text-white/60"}`,
        }, s))
      )
    ),
    React.createElement("div", { className: "flex items-center gap-2" },
      React.createElement("span", { className: "text-xs text-white/30" }, "Idioma:"),
      LANGUAGES.map(lg => React.createElement("button", {
        key: lg.id, onClick: () => setLanguage(lg.id),
        className: `rounded-xl border px-3 py-1 text-xs transition-colors ${language === lg.id ? "border-white/25 bg-white/10 text-white" : "border-white/8 text-white/35 hover:text-white/60"}`,
      }, lg.label))
    ),
    React.createElement("button", { onClick: () => onConfirm(mode, subject), className: "w-full rounded-2xl border border-white/15 bg-white/6 py-3 text-sm font-medium text-white hover:bg-white/10 transition-all" }, "Iniciar sessão →")
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function ConcursosPage() {
  const [stage, setStage] = useState("select"); // select | configure | chat
  const [exam, setExam] = useState(null);
  const [mode, setMode] = useState("chat");
  const [subject, setSubject] = useState("");
  const [language, setLanguage] = useState("pt");

  return React.createElement(AppShell, null,
    React.createElement("div", { className: "mx-auto max-w-5xl px-4 py-10" },

      // Hero (only on select)
      stage === "select" && React.createElement(motion.div, { initial: { opacity: 0, y: -10 }, animate: { opacity: 1, y: 0 }, className: "mb-8 text-center" },
        React.createElement("div", { className: "mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/4 px-3 py-1 text-xs text-white/50" },
          React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" }),
          "Acesso público · Sessão 100% anônima"
        ),
        React.createElement("h1", { className: "text-3xl font-bold text-white mb-2" }, "Concursos & Vestibulares"),
        React.createElement("p", { className: "text-white/50 text-sm max-w-lg mx-auto" },
          "Tutor especializado para ENEM, OAB, Residência Médica, FUVEST, ENADE e concursos públicos. " +
          "Questões no formato real, correção de redação e resumos."
        )
      ),

      // Back navigation
      stage !== "select" && React.createElement("div", { className: "mb-6 flex items-center gap-2" },
        React.createElement("button", { onClick: () => setStage(stage === "chat" ? "configure" : "select"), className: "inline-flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors" },
          "← " + (stage === "chat" ? "Configurar" : "Escolher exame")
        ),
        stage === "chat" && React.createElement("span", { className: "text-white/20 text-xs" }, "/ " + (exam?.label || "") + " · " + (MODES.find(m => m.id === mode)?.label || ""))
      ),

      // Stages
      stage === "select" && React.createElement(ExamSelector, { onSelect: (e) => { setExam(e); setStage("configure"); } }),
      stage === "configure" && exam && React.createElement(ModeSelector, {
        exam, language, setLanguage,
        onConfirm: (m, s) => { setMode(m); setSubject(s); setStage("chat"); },
      }),
      stage === "chat" && exam && React.createElement("div", { className: "h-[calc(100vh-140px)] flex flex-col" },
        React.createElement(ConcursoChat, { exam, mode, subject, language, onBack: () => setStage("configure") })
      ),

      // Privacy (only on select)
      stage === "select" && React.createElement(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { delay: 0.5 }, className: "mt-8 rounded-2xl border border-white/5 bg-white/2 p-3 text-center" },
        React.createElement("p", { className: "text-xs text-white/20" }, "100% anônimo — nenhum dado, pergunta ou redação é armazenado. LGPD (Lei 13.709/2018).")
      )
    )
  );
}
