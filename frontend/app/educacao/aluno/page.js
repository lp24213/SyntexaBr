"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppShell } from "../../../components/shell";
import { educationTutorStream, educationCompute, gradeEnemEssayStream } from "../../../lib/api";
import MathRenderer, { MathText } from "../../../components/ui/math-renderer";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";

const DISCIPLINES = [
  // Exatas
  { id: "matematica", label: "Matemática", iconName: "sigma", desc: "Álgebra, cálculo, geometria, EDs" },
  { id: "fisica", label: "Física", iconName: "atom", desc: "Mecânica, EM, quântica, relatividade" },
  { id: "quimica", label: "Química", iconName: "flask", desc: "Orgânica, inorgânica, cinética" },
  { id: "astronomia", label: "Astronomia", iconName: "telescope", desc: "Astrofísica, cosmologia, espaço" },
  // Tecnologia
  { id: "programacao", label: "Programação", iconName: "code", desc: "Algoritmos, Python, JS, estruturas" },
  { id: "engenharia", label: "Engenharia", iconName: "gear", desc: "Cálculo aplicado, circuitos, estrutural" },
  { id: "inteligencia_artificial", label: "IA & ML", iconName: "brain", desc: "Machine learning, redes neurais, NLP" },
  { id: "seguranca_digital", label: "Segurança Digital", iconName: "lock", desc: "Criptografia, privacidade, LGPD, OWASP" },
  // Vida
  { id: "biologia", label: "Biologia", iconName: "dna", desc: "Genética, fisiologia, ecologia" },
  { id: "saude", label: "Saúde", iconName: "cross", desc: "Anatomia, fisiologia, epidemiologia" },
  // Humanas
  { id: "historia", label: "História", iconName: "scroll", desc: "Brasil, mundo, contemporânea" },
  { id: "economia", label: "Economia", iconName: "chart", desc: "Micro, macro, finanças, mercados" },
  { id: "direito", label: "Direito", iconName: "scale", desc: "Constitucional, civil, digital, LGPD" },
  { id: "ciencias_ambientais", label: "Meio Ambiente", iconName: "globe", desc: "Clima, biodiversidade, sustentabilidade" },
  // Geral
  { id: "geral", label: "Geral", iconName: "hex", desc: "Todas as disciplinas" },
];

const MODES = [
  { id: "chat", label: "Chat", iconName: "chat", desc: "Tire dúvidas livremente" },
  { id: "exercicio", label: "Exercícios", iconName: "pencil", desc: "3 exercícios progressivos com gabarito" },
  { id: "simulado", label: "Simulado", iconName: "clipboard", desc: "Questão estilo ENEM com alternativas" },
  { id: "calculo", label: "Cálculo", iconName: "integral", desc: "Resolução rigorosa com todos os passos" },
  { id: "pesquisa", label: "Pesquisa", iconName: "microscope", desc: "Aprofundamento científico" },
  { id: "redacao", label: "Redação", iconName: "doc", desc: "Correção de redação ENEM com nota 0-1000" },
];

const LEVELS = [
  { id: "basico", label: "Básico", desc: "Ensino Fundamental", color: "text-emerald-700 border-emerald-200 bg-emerald-50" },
  { id: "intermediario", label: "Intermediário", desc: "Ensino Médio", color: "text-sky-700 border-sky-200 bg-sky-50" },
  { id: "avancado", label: "Avançado", desc: "Graduação", color: "text-violet-700 border-violet-200 bg-violet-50" },
  { id: "especialista", label: "Especialista", desc: "Pesquisador", color: "text-amber-700 border-amber-200 bg-amber-50" },
];

const LANGUAGES = [
  { id: "pt", label: "PT", full: "Português" },
  { id: "en", label: "EN", full: "English" },
  { id: "es", label: "ES", full: "Español" },
  { id: "zh", label: "中文", full: "Mandarim" },
];

// ─── Anonymous session helpers (sessionStorage only — ephemeral, never sent to server) ──

function getOrCreateAnonSession() {
  if (typeof window === "undefined") return "anon-ssr";
  let sid = sessionStorage.getItem("edu_aluno_sid");
  if (!sid) {
    sid = "edu-" + Math.random().toString(36).slice(2, 9) + "-" + Date.now().toString(36);
    sessionStorage.setItem("edu_aluno_sid", sid);
  }
  return sid;
}

function loadChatHistory(sessionId, disciplineId) {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(sessionStorage.getItem(`edu_chat_${sessionId}_${disciplineId}`) || "[]");
  } catch { return []; }
}

function saveChatHistory(sessionId, disciplineId, msgs) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(`edu_chat_${sessionId}_${disciplineId}`, JSON.stringify(msgs.slice(-40)));
}

function SendIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M22 2L11 13", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M22 2L15 22l-4-9-9-4 20-7z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" }));
}
function BackIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M19 12H5M12 5l-7 7 7 7", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }));
}
function StopIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("rect", { x: "6", y: "6", width: "12", height: "12", rx: "2", stroke: "currentColor", strokeWidth: "1.5" }));
}
function CalcIcon() {
  return React.createElement("svg", { className: "h-3.5 w-3.5", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("rect", { x: "4", y: "2", width: "16", height: "20", rx: "2", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M8 7h8M8 12h4M8 17h2M16 12v5", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }));
}

function MessageBubble({ role, content, streaming, computeData }) {
  const isUser = role === "user";
  return React.createElement(
    motion.div,
    { className: `flex ${isUser ? "justify-end" : "justify-start"}`, initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.2 } },
    React.createElement("div", {
      className: isUser
        ? "max-w-[78%] rounded-2xl rounded-tr-sm bg-zinc-100 px-4 py-3 text-sm text-zinc-900"
        : "max-w-[90%] rounded-2xl rounded-tl-sm border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-800 leading-relaxed",
    },
      isUser
        ? content
        : React.createElement(MathText, { text: content }),
      streaming && React.createElement("span", { className: "inline-block ml-0.5 h-3.5 w-0.5 animate-pulse bg-zinc-500 align-middle" }),
      computeData && computeData.steps && computeData.steps.length > 0 && React.createElement("div", { className: "mt-3 rounded-xl border border-violet-200 bg-violet-50 p-3 space-y-1" },
        React.createElement("p", { className: "mb-1.5 text-[10px] uppercase tracking-wider text-violet-700" }, "Resultado SymPy"),
        computeData.steps.map(function (s, i) {
          return React.createElement("p", { key: i, className: "font-mono text-xs text-violet-800/90" }, s);
        }),
        computeData.result && React.createElement("div", { className: "mt-2 rounded-lg bg-violet-100 px-3 py-1.5" },
          React.createElement("p", { className: "font-mono text-sm font-bold text-violet-800" }, "= " + computeData.result)
        )
      )
    )
  );
}

export default function AlunoPage() {
  const [discipline, setDiscipline] = useState(null);
  const [mode, setMode] = useState("chat");
  const [level, setLevel] = useState("intermediario");
  const [language, setLanguage] = useState("pt");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [sessionId, setSessionId] = useState("anon-ssr");
  const [essayText, setEssayText] = useState("");
  const [essayTheme, setEssayTheme] = useState("");
  // Feedback adaptativo — aluno sinaliza dificuldade para a IA ajustar próxima resposta
  const [pendingFeedback, setPendingFeedback] = useState(null);
  const abortRef = useRef(null);
  const bottomRef = useRef(null);

  // Export chat history as Markdown file
  const exportChat = function () {
    if (!messages.length) return;
    const disc = DISCIPLINES.find(function (d) { return d.id === discipline; });
    const header = `# Chat — ${disc?.label || "Educação"}\n> Sessão anônima · ${new Date().toLocaleString("pt-BR")}\n\n---\n\n`;
    const body = messages.map(function (m) {
      const role = m.role === "user" ? "**Você**" : "**Tutor**";
      return `${role}\n\n${m.content}\n\n---\n`;
    }).join("\n");
    const blob = new Blob([header + body], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `educacao-${discipline || "chat"}-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(function () {
    setSessionId(getOrCreateAnonSession());
  }, []);

  useEffect(function () {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Persist history in sessionStorage on every change
  useEffect(function () {
    if (discipline && messages.length > 0) {
      saveChatHistory(sessionId, discipline, messages);
    }
  }, [messages, discipline, sessionId]);

  const handleSend = useCallback(async function () {
    if (streaming) return;
    setError(null);

    // ── Redação ENEM mode uses the essay text, not the input field ──
    if (mode === "redacao") {
      const essay = essayText.trim();
      if (!essay || essay.length < 50) { setError("Cole sua redação no campo acima (mínimo 50 caracteres)."); return; }
      const userMsg = { role: "user", content: `**Redação enviada para correção**${essayTheme ? ` — Tema: ${essayTheme}` : ""}\n\n${essay}` };
      const history = [...messages, userMsg];
      setMessages([...history, { role: "assistant", content: "" }]);
      setStreaming(true);
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      try {
        await gradeEnemEssayStream(essay, essayTheme, language, function (chunk) {
          setMessages(function (prev) {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant") updated[updated.length - 1] = { ...last, content: last.content + chunk };
            return updated;
          });
        }, ctrl.signal);
      } catch (err) {
        if (err.name !== "AbortError") setError("Erro ao corrigir redação. Tente novamente.");
      } finally {
        setStreaming(false); abortRef.current = null;
        setEssayText(""); setEssayTheme("");
      }
      return;
    }

    const q = input.trim();
    if (!q) return;
    const userMsg = { role: "user", content: q };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setStreaming(true);
    const assistantMsg = { role: "assistant", content: "" };
    setMessages([...history, assistantMsg]);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // For compute/calculo mode, also try SymPy
    let computeData = null;
    if (mode === "calculo") {
      try {
        computeData = await educationCompute(q, "auto", "x");
      } catch (_) {}
    }

    const feedbackToSend = pendingFeedback;
    setPendingFeedback(null);

    try {
      await educationTutorStream(
        discipline, q, mode,
        messages.slice(-12),
        function (chunk) {
          setMessages(function (prev) {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant") {
              updated[updated.length - 1] = { ...last, content: last.content + chunk };
            }
            return updated;
          });
        },
        ctrl.signal, level, language, feedbackToSend
      );
      if (computeData) {
        setMessages(function (prev) {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === "assistant") {
            updated[updated.length - 1] = { ...last, computeData };
          }
          return updated;
        });
      }
    } catch (err) {
      if (err.name !== "AbortError") setError("Erro ao obter resposta. Tente novamente.");
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, essayText, essayTheme, discipline, mode, level, language, messages, streaming, pendingFeedback]);

  const handleKeyDown = function (ev) {
    if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); handleSend(); }
  };
  const handleStop = function () { if (abortRef.current) abortRef.current.abort(); };

  const goToLabs = function () { window.location.href = "/educacao/laboratorios"; };

  const selectDiscipline = function (id) {
    setDiscipline(id);
    setError(null);
    // Restore history from sessionStorage if available
    const saved = loadChatHistory(sessionId, id);
    const chosen = DISCIPLINES.find(function (d) { return d.id === id; });
    const lvl = LEVELS.find(function (l) { return l.id === level; });
    const lang = LANGUAGES.find(function (l) { return l.id === language; });
    if (saved.length > 0) {
      setMessages(saved);
    } else if (chosen) {
      setMessages([{
        role: "assistant",
        content: `Olá! Sou seu tutor de **${chosen.label}** (nível ${lvl?.label}, idioma: ${lang?.full}).\n\nEscolha um modo no topo e faça sua pergunta. Posso explicar, gerar exercícios, simular questões de vestibular e resolver cálculos completos.`,
      }]);
    }
  };

  const clearChat = function () {
    if (discipline) {
      saveChatHistory(sessionId, discipline, []);
      setMessages([]);
    }
  };

  // ─── Selection screen ─────────────────────────────────────────────────
  if (!discipline) {
    return React.createElement(AppShell, null,
      React.createElement("div", { className: "py-8" },
        React.createElement("div", null,
          React.createElement("button", { onClick: function () { window.location.href = "/educacao"; }, className: "inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-700 mb-6" }, React.createElement(BackIcon, null), "Educação & Pesquisa")
        ),
        React.createElement("div", { className: "mb-8 text-center" },
          React.createElement("div", { className: "mb-3 flex flex-wrap items-center justify-center gap-2" },
            React.createElement("div", { className: "inline-flex items-center gap-2 rounded-full border border-[rgba(20,24,30,0.06)] bg-[#f1f2f4] px-3 py-1 text-xs text-[#5a5c5e]" },
              React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-sky-400 animate-pulse" }),
              "Área Aluno · Público e Gratuito"
            ),
            React.createElement("div", { className: "inline-flex items-center gap-1.5 rounded-full border border-[rgba(20,24,30,0.06)] bg-[#f8f9fa] px-3 py-1 text-xs text-[#5a5c5e]" },
              React.createElement(FuturisticIcon, { name: "lock", className: "h-3 w-3 text-[#5a5c5e]/90" }),
              "Sessão anônima · " + sessionId.slice(0, 10) + "…"
            )
          ),
          React.createElement("h1", { className: "text-3xl font-bold text-zinc-900 sm:text-4xl" }, "Escolha a disciplina"),
          React.createElement("p", { className: "mt-2 text-sm text-zinc-500" }, "Tutor de IA do básico ao nível especialista — sem login, sem limite, sem rastreamento")
        ),

        // Level selector
        React.createElement("div", { className: "mb-6 rounded-2xl border border-zinc-200 bg-white p-4" },
          React.createElement("p", { className: "mb-3 text-xs font-medium text-zinc-500 uppercase tracking-wider" }, "Seu nível"),
          React.createElement("div", { className: "grid grid-cols-2 gap-2 sm:grid-cols-4" },
            LEVELS.map(function (l) {
              return React.createElement("button", { key: l.id, onClick: function () { setLevel(l.id); }, className: `flex flex-col items-start rounded-xl border px-3 py-2 text-left transition-all ${level === l.id ? l.color : "border-zinc-200 text-zinc-500 hover:border-zinc-200 hover:text-zinc-700"}` },
                React.createElement("span", { className: "text-xs font-semibold" }, l.label),
                React.createElement("span", { className: "text-[10px] opacity-70" }, l.desc)
              );
            })
          )
        ),

        // Language selector
        React.createElement("div", { className: "mb-6 flex items-center gap-3 flex-wrap" },
          React.createElement("p", { className: "text-xs text-zinc-500 uppercase tracking-wider" }, "Idioma:"),
          LANGUAGES.map(function (l) {
            return React.createElement("button", { key: l.id, onClick: function () { setLanguage(l.id); }, className: `rounded-xl border px-3 py-1.5 text-xs font-medium transition-all ${language === l.id ? "bg-zinc-100 border-zinc-300 text-zinc-900" : "border-zinc-200 text-zinc-500 hover:text-zinc-700"}` }, l.label, React.createElement("span", { className: "ml-1 hidden sm:inline text-[10px] opacity-60" }, l.full));
          })
        ),

        // Disciplines
        React.createElement("div", { className: "mb-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5" },
          DISCIPLINES.map(function (d, idx) {
            return React.createElement("button", {
              key: d.id,
              onClick: function () { selectDiscipline(d.id); },
              className: "group flex flex-col items-start gap-2 rounded-2xl border border-zinc-200 bg-white p-5 text-left transition-all hover:border-[rgba(20,24,30,0.1)] hover:bg-[#f8f9fa]",
            },
              React.createElement(FuturisticIcon, { name: d.iconName, className: "h-9 w-9 text-[#1a1c1e]/85 shrink-0" }),
              React.createElement("div", null,
                React.createElement("p", { className: "text-sm font-semibold text-zinc-900 group-hover:text-[#5a5c5e] transition-colors" }, d.label),
                React.createElement("p", { className: "text-xs text-zinc-500 leading-tight" }, d.desc)
              )
            );
          })
        ),

        // Mode selector
        React.createElement("div", { className: "rounded-2xl border border-zinc-200 bg-white p-4" },
          React.createElement("p", { className: "mb-3 text-xs font-medium text-zinc-500 uppercase tracking-wider" }, "Modo de estudo"),
          React.createElement("div", { className: "grid grid-cols-2 sm:grid-cols-5 gap-2" },
            MODES.map(function (m) {
              return React.createElement("button", { key: m.id, onClick: function () { setMode(m.id); }, className: `flex flex-col items-start rounded-xl border px-3 py-2 transition-all ${mode === m.id ? "border-[rgba(20,24,30,0.1)] bg-[#f1f2f4] text-[#5a5c5e]" : "border-zinc-200 text-zinc-500 hover:text-zinc-700 hover:border-zinc-200"}` },
                React.createElement("span", { className: "text-sm mb-0.5 inline-flex items-center gap-1.5" }, React.createElement(FuturisticIcon, { name: m.iconName, className: "h-4 w-4 text-[#1a1c1e]/80" }), React.createElement("span", { className: "text-xs font-semibold" }, m.label)),
                React.createElement("span", { className: "text-[10px] opacity-60 leading-tight" }, m.desc)
              );
            })
          )
        ),

        // Shortcuts row
        React.createElement("div", { className: "mt-6 grid gap-3 sm:grid-cols-2" },
          React.createElement("button", { onClick: goToLabs, className: "rounded-2xl border border-zinc-200 bg-zinc-100 p-4 text-left hover:border-zinc-200 transition-all" },
            React.createElement("div", { className: "flex items-center justify-between" },
              React.createElement("div", null,
                React.createElement("p", { className: "text-sm font-medium text-zinc-900 flex items-center gap-2" }, React.createElement(FuturisticIcon, { name: "flask", className: "h-4 w-4 text-[#1a1c1e]/80" }), "Laboratórios Científicos"),
                React.createElement("p", { className: "text-xs text-zinc-500 mt-0.5" }, "Pêndulo, ondas, sorting, SymPy, sandbox Python")
              ),
              React.createElement("svg", { className: "h-4 w-4 text-zinc-400", viewBox: "0 0 24 24", fill: "none" },
                React.createElement("path", { d: "M5 12h14M12 5l7 7-7 7", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }))
            )
          ),
          React.createElement("button", { onClick: function () { window.location.href = "/educacao/ciencia"; }, className: "rounded-2xl border border-zinc-200 bg-zinc-100 p-4 text-left hover:border-zinc-200 transition-all" },
            React.createElement("div", { className: "flex items-center justify-between" },
              React.createElement("div", null,
                React.createElement("p", { className: "text-sm font-medium text-zinc-900 flex items-center gap-2" }, React.createElement(FuturisticIcon, { name: "telescope", className: "h-4 w-4 text-violet-400/80" }), "Ciência & Tecnologia"),
                React.createElement("p", { className: "text-xs text-zinc-500 mt-0.5" }, "IA, quântica, bioinformática, segurança digital")
              ),
              React.createElement("svg", { className: "h-4 w-4 text-zinc-400", viewBox: "0 0 24 24", fill: "none" },
                React.createElement("path", { d: "M5 12h14M12 5l7 7-7 7", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }))
            )
          )
        ),

        // Privacy notice
        React.createElement("div", { className: "mt-4 rounded-2xl border border-zinc-200 bg-zinc-50 p-3 text-center" },
          React.createElement("p", { className: "text-xs text-zinc-400" },
            "Sessão 100% anônima — nenhuma mensagem ou dado pessoal é armazenado no servidor. " +
            "Histórico salvo apenas na memória do seu navegador. Conforme LGPD (Lei 13.709/2018)."
          )
        )
      )
    );
  }

  // ─── Chat screen ────────────────────────────────────────────────────────
  const chosen = DISCIPLINES.find(function (d) { return d.id === discipline; });
  const currentLevel = LEVELS.find(function (l) { return l.id === level; });
  const currentLang = LANGUAGES.find(function (l) { return l.id === language; });
  const currentMode = MODES.find(function (m) { return m.id === mode; });

  return React.createElement(AppShell, null,
    React.createElement("div", { className: "flex h-[calc(100vh-11rem)] flex-col" },
      // Header
      React.createElement("div", { className: "mb-3 flex items-center justify-between flex-wrap gap-2" },
        React.createElement("div", { className: "flex items-center gap-2 flex-wrap" },
          React.createElement("button", { onClick: function () { setDiscipline(null); setMessages([]); }, className: "inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-900" }, React.createElement(BackIcon, null), "Disciplinas"),
          chosen && React.createElement(FuturisticIcon, { name: chosen.iconName, className: "h-6 w-6 text-[#1a1c1e]/85" }),
          React.createElement("span", { className: "text-sm font-medium text-zinc-900" }, chosen?.label),
          React.createElement("span", { className: `hidden rounded-full border px-2 py-0.5 text-[10px] sm:inline ${currentLevel?.color || ""}` }, currentLevel?.label),
          React.createElement("span", { className: "hidden rounded-full border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-[10px] text-zinc-500 sm:inline" }, currentLang?.full)
        ),
        React.createElement("div", { className: "flex items-center gap-1 flex-wrap" },
          React.createElement("span", { className: "hidden sm:inline-flex items-center gap-1 text-[10px] text-zinc-400 mr-1 font-mono" }, React.createElement(FuturisticIcon, { name: "lock", className: "h-3 w-3 text-zinc-400" }), sessionId.slice(0, 8)),
          MODES.map(function (m) {
            return React.createElement("button", { key: m.id, onClick: function () { setMode(m.id); }, className: `inline-flex items-center gap-1 rounded-xl px-2.5 py-1.5 text-xs transition-all ${mode === m.id ? "bg-sky-600/70 text-zinc-900" : "text-zinc-500 hover:text-zinc-700"}` }, React.createElement(FuturisticIcon, { name: m.iconName, className: "h-3.5 w-3.5" }), m.label);
          }),
          React.createElement("button", { onClick: exportChat, title: "Exportar conversa como Markdown", className: "rounded-xl border border-zinc-200 px-2.5 py-1.5 text-xs text-zinc-400 hover:text-zinc-600 inline-flex items-center justify-center" }, React.createElement(FuturisticIcon, { name: "download", className: "h-3.5 w-3.5" })),
          React.createElement("button", { onClick: clearChat, className: "rounded-xl border border-zinc-200 px-2.5 py-1.5 text-xs text-zinc-400 hover:text-zinc-600 inline-flex items-center justify-center" }, React.createElement(FuturisticIcon, { name: "trash", className: "h-3.5 w-3.5" })),
          React.createElement("button", { onClick: function () { setShowSettings(!showSettings); }, className: "rounded-xl border border-zinc-200 px-2.5 py-1.5 text-xs text-zinc-500 hover:text-zinc-900 inline-flex items-center justify-center" }, React.createElement(FuturisticIcon, { name: "gear", className: "h-3.5 w-3.5" }))
        )
      ),

      // Settings panel
      showSettings && React.createElement("div", { className: "mb-3 rounded-xl border border-zinc-200 bg-white p-4" },
        React.createElement("div", { className: "flex flex-wrap gap-4" },
          React.createElement("div", null,
            React.createElement("p", { className: "mb-1.5 text-xs text-zinc-500" }, "Nível"),
            React.createElement("div", { className: "flex gap-1.5" }, LEVELS.map(function (l) {
              return React.createElement("button", { key: l.id, onClick: function () { setLevel(l.id); }, className: `rounded-xl border px-2.5 py-1 text-xs transition-all ${level === l.id ? l.color : "border-zinc-200 text-zinc-500 hover:text-zinc-600"}` }, l.label);
            }))
          ),
          React.createElement("div", null,
            React.createElement("p", { className: "mb-1.5 text-xs text-zinc-500" }, "Idioma"),
            React.createElement("div", { className: "flex gap-1.5" }, LANGUAGES.map(function (l) {
              return React.createElement("button", { key: l.id, onClick: function () { setLanguage(l.id); }, className: `rounded-xl border px-2.5 py-1 text-xs transition-all ${language === l.id ? "bg-zinc-100 border-zinc-300 text-zinc-900" : "border-zinc-200 text-zinc-500 hover:text-zinc-600"}` }, l.label);
            }))
          )
        )
      ),

      // Messages
      React.createElement("div", { className: "flex-1 overflow-y-auto rounded-2xl border border-zinc-200 bg-zinc-50 p-4 space-y-4" },
        messages.map(function (msg, idx) {
          const isLast = idx === messages.length - 1;
          const showFeedback = isLast && msg.role === "assistant" && !streaming && msg.content.length > 20;
          return React.createElement("div", { key: idx },
            React.createElement(MessageBubble, { role: msg.role, content: msg.content, streaming: isLast && streaming && msg.role === "assistant", computeData: msg.computeData }),
            showFeedback && React.createElement("div", { className: "flex items-center gap-2 mt-1.5 ml-2" },
              React.createElement("span", { className: "text-[10px] text-zinc-400" }, "Essa explicação foi:"),
              [
                { id: "facil", label: "Fácil demais ↑", color: pendingFeedback === "facil" ? "border-amber-400/50 bg-amber-500/10 text-amber-300" : "border-zinc-200 text-zinc-400 hover:text-amber-300" },
                { id: "otimo", label: "Ótima", color: pendingFeedback === "otimo" ? "border-[rgba(20,24,30,0.1)] bg-[#f1f2f4] text-[#5a5c5e]" : "border-zinc-200 text-zinc-400 hover:text-[#5a5c5e]" },
                { id: "dificil", label: "Difícil ↓", color: pendingFeedback === "dificil" ? "border-sky-400/50 bg-[#f1f2f4] text-[#5a5c5e]" : "border-zinc-200 text-zinc-400 hover:text-[#5a5c5e]" },
              ].map(function (fb) {
                return React.createElement("button", {
                  key: fb.id,
                  onClick: function () { setPendingFeedback(fb.id === pendingFeedback ? null : fb.id); },
                  className: "rounded-full border px-2.5 py-0.5 text-[10px] transition-all " + fb.color,
                }, fb.label);
              })
            )
          );
        }),
        React.createElement("div", { ref: bottomRef })
      ),

      error && React.createElement("p", { className: "mt-2 text-xs text-red-400" }, error),

      // Input — Redação ENEM mode
      mode === "redacao"
        ? React.createElement("div", { className: "mt-3 space-y-2" },
            React.createElement("input", {
              value: essayTheme,
              onChange: function (e) { setEssayTheme(e.target.value); },
              placeholder: "Tema da redação (opcional)...",
              className: "w-full rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:border-zinc-200",
            }),
            React.createElement("div", { className: "relative" },
              React.createElement("textarea", {
                value: essayText,
                onChange: function (e) { setEssayText(e.target.value); },
                placeholder: "Cole ou escreva sua redação aqui...\n\nA correção avaliará: norma culta, compreensão do tema, coerência, coesão e proposta de intervenção (0-1000).",
                rows: 8,
                disabled: streaming,
                className: "w-full resize-none rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:border-[rgba(20,24,30,0.06)] transition-colors disabled:opacity-50",
              }),
              React.createElement("span", { className: "absolute bottom-3 right-3 text-[10px] text-zinc-400 pointer-events-none" },
                essayText.length + " chars · ~" + essayText.trim().split(/\s+/).filter(Boolean).length + " palavras"
              )
            ),
            React.createElement("div", { className: "flex gap-2" },
              React.createElement("button", {
                onClick: streaming ? handleStop : handleSend,
                disabled: !streaming && essayText.trim().length < 50,
                className: `flex-1 rounded-xl border py-2.5 text-sm font-medium transition-all ${streaming ? "border-red-500/30 bg-red-500/10 text-red-300" : "border-[rgba(20,24,30,0.06)] bg-[#f1f2f4] text-[#5a5c5e] hover:bg-sky-500/20 disabled:opacity-30"}`,
              }, streaming ? "Parar correção" : React.createElement("span", { className: "inline-flex items-center justify-center gap-2" }, React.createElement(FuturisticIcon, { name: "doc", className: "h-4 w-4" }), "Corrigir Redação ENEM")),
              React.createElement("button", { onClick: function () { setEssayText(""); }, className: "rounded-xl border border-zinc-200 px-4 text-xs text-zinc-500 hover:text-zinc-700" }, "Limpar")
            )
          )
        // Normal input
        : React.createElement("div", { className: "mt-3 flex items-end gap-2" },
            React.createElement("div", { className: "flex-1 rounded-2xl border border-zinc-200 bg-white px-4 py-3 focus-within:border-[rgba(20,24,30,0.1)] transition-colors" },
              React.createElement("div", { className: "mb-1 flex items-center gap-1.5" },
                React.createElement("span", { className: "text-[10px] text-zinc-400 inline-flex items-center gap-1" }, currentMode && React.createElement(FuturisticIcon, { name: currentMode.iconName, className: "h-3 w-3 opacity-70" }), currentMode?.label, " · ", currentLevel?.label, " · ", currentLang?.label)
              ),
              React.createElement("textarea", {
                value: input,
                onChange: function (e) { setInput(e.target.value); },
                onKeyDown: handleKeyDown,
                placeholder: mode === "calculo" ? "Ex: derivada de sin(x²), ∫ x² dx, x²-5x+6=0 ..." : mode === "simulado" ? "Peça uma questão estilo ENEM ou especifique o tema..." : "Digite sua pergunta...",
                rows: 2,
                className: "w-full resize-none bg-transparent text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none",
                disabled: streaming,
              })
            ),
            React.createElement("button", {
              onClick: streaming ? handleStop : handleSend,
              disabled: !streaming && !input.trim(),
              className: `flex h-11 w-11 items-center justify-center rounded-xl transition-all ${streaming ? "bg-red-600/70 hover:bg-red-500/90 border border-red-500/40" : "bg-[#1a1c1e] hover:bg-sky-500/90 border border-[rgba(20,24,30,0.1)] disabled:opacity-40"} text-zinc-900`,
            }, streaming ? React.createElement(StopIcon, null) : React.createElement(SendIcon, null))
          )
    )
  );
}
