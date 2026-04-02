"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../../components/shell";
import { teacherChatStream, teacherResearchStream, getProfile } from "../../../lib/api";
import { encryptedPath } from "../../../lib/routes";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";

// ─── Tool categories ─────────────────────────────────────────────────────────

const SECTIONS = [
  {
    id: "docencia",
    label: "Docência",
    color: "violet",
    badge: "bg-violet-500/10 text-violet-300 border-violet-500/20",
    tools: [
      { id: "correcao", label: "Corrigir Prova", iconName: "check", api: "teacher", desc: "Correção automática com nota e rubrica completa", placeholder: "Cole a resposta discursiva do aluno para correção detalhada..." },
      { id: "prova", label: "Criar Prova", iconName: "clipboard", api: "teacher", desc: "Questões objetivas e discursivas com gabarito e taxonomia de Bloom", placeholder: "Ex: Prova de Física, 3º EM, tema cinemática, 5 objetivas + 2 discursivas..." },
      { id: "material", label: "Material Didático", iconName: "book", api: "teacher", desc: "Planos de aula, resumos, mapas mentais, slides roteirizados", placeholder: "Ex: Plano de aula 50min, 9º ano, fotossíntese, recursos: quadro + datashow..." },
      { id: "plano_aula", label: "Plano de Aula", iconName: "calendar", api: "teacher", desc: "Plano completo com objetivos SMART, sequência didática e BNCC", placeholder: "Disciplina, turma, duração, tema e competências desejadas..." },
      { id: "turma", label: "Gestão de Turma", iconName: "users", api: "teacher", desc: "Cronogramas, registros, análise de desempenho coletivo", placeholder: "Descreva a turma, período letivo e o que precisa organizar..." },
    ],
  },
  {
    id: "pesquisa",
    label: "Pesquisa Científica",
    color: "sky",
    badge: "bg-sky-500/10 text-sky-300 border-sky-500/20",
    tools: [
      { id: "analisar", label: "Analisar Paper", iconName: "microscope", api: "research", desc: "Extrai hipóteses, metodologia, resultados e contribuições", placeholder: "Cole o abstract ou texto completo do artigo para análise estruturada..." },
      { id: "resumir", label: "Resumir Texto", iconName: "doc", api: "research", desc: "Abstract de 150 palavras + pontos principais + implicações", placeholder: "Cole o texto a ser resumido..." },
      { id: "hipoteses", label: "Gerar Hipóteses", iconName: "lightbulb", api: "research", desc: "5 hipóteses falsificáveis classificadas por viabilidade e impacto", placeholder: "Descreva o contexto, problema e área de pesquisa..." },
      { id: "experimentos", label: "Design Experimental", iconName: "flask", api: "research", desc: "3 designs com variáveis, amostragem, métricas e análise estatística", placeholder: "Descreva as hipóteses e objetivos do experimento..." },
      { id: "escrever", label: "Escrita Acadêmica", iconName: "pen", api: "research", desc: "Produção de artigos, TCC, dissertação com rigor científico", placeholder: "Descreva o tema, objetivo, público e estrutura desejada..." },
    ],
  },
  {
    id: "normas",
    label: "Normas & Revisão",
    color: "emerald",
    badge: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
    tools: [
      { id: "revisar", label: "Revisão Técnica", iconName: "search", api: "research", desc: "Revisão de clareza, precisão técnica e coesão acadêmica", placeholder: "Cole o texto para revisão técnica e melhorias..." },
      { id: "abnt", label: "Formatar ABNT", iconName: "ruler", api: "research", desc: "NBR 6023, 6024, 10520, 14724 — referências e formatação completa", placeholder: "Cole o texto ou lista de referências para formatação ABNT..." },
      { id: "apa", label: "Formatar APA 7ª", iconName: "doc", api: "research", desc: "APA 7th edition — citations, references, running head", placeholder: "Cole o texto ou referências para formatação APA 7ª edição..." },
    ],
  },
];

const ALL_TOOLS = SECTIONS.flatMap(s => s.tools.map(t => ({ ...t, sectionColor: s.color, sectionBadge: s.badge })));

const LEVELS = [
  { id: "intermediario", label: "Médio" },
  { id: "avancado", label: "Superior" },
  { id: "especialista", label: "Pós-Graduação" },
];

const LANGUAGES = [
  { id: "pt", label: "PT" },
  { id: "en", label: "EN" },
  { id: "es", label: "ES" },
  { id: "zh", label: "中文" },
];

const SECTION_COLORS = {
  violet: { border: "border-violet-500/25 hover:border-violet-400/50", active: "border-violet-500/40 bg-violet-500/8", badge: "bg-violet-500/10 text-violet-300 border-violet-500/20", btn: "bg-violet-600/80 border-violet-500/40 hover:bg-violet-500/90" },
  sky: { border: "border-sky-500/25 hover:border-sky-400/50", active: "border-sky-500/40 bg-sky-500/8", badge: "bg-sky-500/10 text-sky-300 border-sky-500/20", btn: "bg-sky-600/80 border-sky-500/40 hover:bg-sky-500/90" },
  emerald: { border: "border-emerald-500/25 hover:border-emerald-400/50", active: "border-emerald-500/40 bg-emerald-500/8", badge: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20", btn: "bg-emerald-600/80 border-emerald-500/40 hover:bg-emerald-500/90" },
};

function BackIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M19 12H5M12 5l-7 7 7 7", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }));
}
function SendIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M22 2L11 13", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M22 2L15 22l-4-9-9-4 20-7z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" }));
}
function StopIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("rect", { x: "6", y: "6", width: "12", height: "12", rx: "2", stroke: "currentColor", strokeWidth: "1.5" }));
}
function LockIcon() {
  return React.createElement("svg", { className: "h-12 w-12 text-violet-400/60", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("rect", { x: "5", y: "11", width: "14", height: "10", rx: "2", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M8 11V7a4 4 0 018 0v4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("circle", { cx: "12", cy: "16", r: "1.5", fill: "currentColor" }));
}

function MessageBubble({ role, content, streaming }) {
  const isUser = role === "user";
  return React.createElement(motion.div, { className: `flex ${isUser ? "justify-end" : "justify-start"}`, initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.2 } },
    React.createElement("div", {
      className: isUser
        ? "max-w-[80%] rounded-2xl rounded-tr-sm bg-white/10 px-4 py-3 text-sm text-white whitespace-pre-wrap"
        : "max-w-[90%] rounded-2xl rounded-tl-sm border border-white/8 bg-[rgba(15,23,42,0.95)] px-4 py-3 text-sm text-white/85 leading-relaxed whitespace-pre-wrap",
    },
      content,
      streaming && React.createElement("span", { className: "inline-block ml-0.5 h-3.5 w-0.5 animate-pulse bg-white/60 align-middle" })
    )
  );
}

export default function ProfessorPage() {
  const [token, setToken] = useState(null);
  const [profile, setProfile] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [activeSection, setActiveSection] = useState("docencia");
  const [activeTool, setActiveTool] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [context, setContext] = useState("");
  const [level, setLevel] = useState("avancado");
  const [language, setLanguage] = useState("pt");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(function () {
    try {
      const t = window.localStorage.getItem("syntexa_token");
      setToken(t || null);
      if (t) {
        getProfile(t).then(function (p) { setProfile(p); }).catch(function () {}).finally(function () { setAuthLoading(false); });
      } else {
        setAuthLoading(false);
      }
    } catch { setAuthLoading(false); }
  }, []);

  useEffect(function () {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const selectTool = function (tool) {
    setActiveTool(tool);
    setMessages([{ role: "assistant", content: `Ferramenta: **${tool.label}**\n\n${tool.desc}.\n\n${tool.placeholder}` }]);
    setError(null);
  };

  const handleSend = useCallback(async function () {
    const q = input.trim();
    if (!q || streaming || !token || !activeTool) return;
    setError(null);
    const userMsg = { role: "user", content: q };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setStreaming(true);
    setMessages([...history, { role: "assistant", content: "" }]);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    const streamFn = activeTool.api === "research"
      ? function (onChunk, signal) { return teacherResearchStream(token, activeTool.id, q, context || null, language, onChunk, signal); }
      : function (onChunk, signal) { return teacherChatStream(token, activeTool.id, q, context || null, level, language, onChunk, signal); };

    try {
      await streamFn(
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
        ctrl.signal
      );
    } catch (err) {
      if (err.name !== "AbortError") setError("Erro ao processar. Tente novamente.");
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, token, activeTool, context, level, language, messages, streaming]);

  const handleKeyDown = function (ev) {
    if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); handleSend(); }
  };
  const handleStop = function () { if (abortRef.current) abortRef.current.abort(); };

  // Loading
  if (authLoading) {
    return React.createElement(AppShell, null,
      React.createElement("div", { className: "flex min-h-[50vh] items-center justify-center" },
        React.createElement("div", { className: "h-6 w-6 animate-spin rounded-full border-2 border-white/20 border-t-violet-400" }))
    );
  }

  // Not authenticated
  if (!token) {
    return React.createElement(AppShell, null,
      React.createElement("div", { className: "flex min-h-[60vh] flex-col items-center justify-center py-12 text-center" },
        React.createElement(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 } },
          React.createElement(LockIcon, null),
          React.createElement("h2", { className: "mt-4 text-2xl font-bold text-white" }, "Acesso Restrito"),
          React.createElement("p", { className: "mt-2 max-w-sm text-sm text-white/50" }, "Área exclusiva para professores e pesquisadores. Faça login ou crie sua conta gratuita."),
          React.createElement("div", { className: "mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center" },
            React.createElement("button", { onClick: function () { window.location.href = encryptedPath("login"); }, className: "rounded-[14px] bg-violet-600/80 border border-violet-500/40 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500/90" }, "Entrar"),
            React.createElement("button", { onClick: function () { window.location.href = encryptedPath("register"); }, className: "rounded-[14px] border border-white/15 px-5 py-2.5 text-sm font-medium text-white/70 hover:text-white" }, "Criar conta")
          ),
          React.createElement("button", { onClick: function () { window.location.href = "/educacao"; }, className: "mt-4 inline-flex items-center gap-1.5 text-xs text-white/30 hover:text-white/60" }, React.createElement(BackIcon, null), "Voltar")
        )
      )
    );
  }

  // Active tool chat
  if (activeTool) {
    const toolSection = SECTIONS.find(s => s.tools.some(t => t.id === activeTool.id));
    const colors = SECTION_COLORS[toolSection?.color || "violet"];

    return React.createElement(AppShell, null,
      React.createElement("div", { className: "flex h-[calc(100vh-11rem)] flex-col" },
        React.createElement(motion.div, { className: "mb-3 flex items-center justify-between flex-wrap gap-2", initial: { opacity: 0 }, animate: { opacity: 1 } },
          React.createElement("div", { className: "flex items-center gap-2" },
            React.createElement("button", { onClick: function () { setActiveTool(null); setMessages([]); }, className: "inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/60 hover:text-white" }, React.createElement(BackIcon, null), "Ferramentas"),
            React.createElement(FuturisticIcon, { name: activeTool.iconName, className: "h-6 w-6 text-violet-300/90" }),
            React.createElement("span", { className: "text-sm font-medium text-white" }, activeTool.label),
            React.createElement("span", { className: `hidden rounded-full border px-2 py-0.5 text-[10px] sm:inline ${colors.badge}` }, toolSection?.label)
          ),
          React.createElement("div", { className: "flex items-center gap-1.5 flex-wrap" },
            LEVELS.map(l => React.createElement("button", { key: l.id, onClick: function () { setLevel(l.id); }, className: `rounded-xl px-2.5 py-1 text-xs transition-all ${level === l.id ? "bg-white/10 text-white border border-white/20" : "text-white/40 hover:text-white/70"}` }, l.label)),
            React.createElement("span", { className: "text-white/20" }, "|"),
            LANGUAGES.map(l => React.createElement("button", { key: l.id, onClick: function () { setLanguage(l.id); }, className: `rounded-xl px-2 py-1 text-xs transition-all ${language === l.id ? "bg-white/10 text-white border border-white/20" : "text-white/40 hover:text-white/70"}` }, l.label))
          )
        ),
        React.createElement("div", { className: "flex-1 overflow-y-auto rounded-2xl border border-white/6 bg-[rgba(8,15,30,0.8)] p-4 space-y-4" },
          messages.map(function (msg, idx) {
            const isLast = idx === messages.length - 1;
            return React.createElement(MessageBubble, { key: idx, role: msg.role, content: msg.content, streaming: isLast && streaming && msg.role === "assistant" });
          }),
          React.createElement("div", { ref: bottomRef })
        ),
        error && React.createElement("p", { className: "mt-2 text-xs text-red-400" }, error),
        context.trim() && React.createElement("p", { className: "mt-1 text-xs text-white/30" }, "Contexto: ", context.slice(0, 60), "..."),
        React.createElement("div", { className: "mt-3 flex items-end gap-2" },
          React.createElement("div", { className: `flex-1 rounded-2xl border bg-[rgba(15,23,42,0.95)] px-4 py-3 transition-colors focus-within:${colors.border.split(" ")[0].replace("border-", "border-")} border-white/10` },
            React.createElement("textarea", {
              value: input,
              onChange: function (e) { setInput(e.target.value); },
              onKeyDown: handleKeyDown,
              placeholder: activeTool.placeholder,
              rows: 3,
              className: "w-full resize-none bg-transparent text-sm text-white placeholder:text-white/25 focus:outline-none",
              disabled: streaming,
            })
          ),
          React.createElement("button", {
            onClick: streaming ? handleStop : handleSend,
            disabled: !streaming && !input.trim(),
            className: `flex h-11 w-11 items-center justify-center rounded-xl border transition-all ${streaming ? "bg-red-600/70 border-red-500/40" : `${colors.btn} disabled:opacity-40`} text-white`,
          }, streaming ? React.createElement(StopIcon, null) : React.createElement(SendIcon, null))
        )
      )
    );
  }

  // Tool selection dashboard
  const currentSection = SECTIONS.find(s => s.id === activeSection);
  const colors = SECTION_COLORS[currentSection?.color || "violet"];

  return React.createElement(AppShell, null,
    React.createElement("div", { className: "py-8 space-y-6" },
      React.createElement(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 } },
        React.createElement("button", { onClick: function () { window.location.href = "/educacao"; }, className: "inline-flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 mb-6" }, React.createElement(BackIcon, null), "Educação & Pesquisa")
      ),
      React.createElement(motion.div, { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 } },
        React.createElement("div", { className: "mb-3 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1 text-xs text-violet-300" }, "Área Professor / Pesquisador"),
        React.createElement("h1", { className: "text-3xl font-bold text-white" }, "Ferramentas Avançadas"),
        React.createElement("p", { className: "mt-1 text-sm text-white/50" }, `Bem-vindo${profile?.full_name ? ", " + profile.full_name : ""}. Selecione uma categoria e ferramenta.`)
      ),

      // Section tabs
      React.createElement("div", { className: "flex flex-wrap gap-2" },
        SECTIONS.map(function (s) {
          const sc = SECTION_COLORS[s.color];
          return React.createElement("button", {
            key: s.id,
            onClick: function () { setActiveSection(s.id); },
            className: `rounded-xl border px-4 py-2 text-sm font-medium transition-all ${activeSection === s.id ? `${sc.active} ${sc.badge}` : "border-white/8 text-white/50 hover:text-white/80"}`,
          }, s.label);
        })
      ),

      // Settings row
      React.createElement("div", { className: "flex items-center gap-4 flex-wrap" },
        React.createElement("div", { className: "flex items-center gap-1.5" },
          React.createElement("p", { className: "text-xs text-white/40" }, "Nível:"),
          LEVELS.map(l => React.createElement("button", { key: l.id, onClick: function () { setLevel(l.id); }, className: `rounded-xl border px-2.5 py-1 text-xs transition-all ${level === l.id ? "bg-white/10 border-white/25 text-white" : "border-white/8 text-white/40 hover:text-white/60"}` }, l.label))
        ),
        React.createElement("div", { className: "flex items-center gap-1.5" },
          React.createElement("p", { className: "text-xs text-white/40" }, "Idioma:"),
          LANGUAGES.map(l => React.createElement("button", { key: l.id, onClick: function () { setLanguage(l.id); }, className: `rounded-xl border px-2.5 py-1 text-xs transition-all ${language === l.id ? "bg-white/10 border-white/25 text-white" : "border-white/8 text-white/40 hover:text-white/60"}` }, l.label))
        )
      ),

      // Tools grid
      React.createElement("div", { className: "grid gap-4 sm:grid-cols-2 lg:grid-cols-3" },
        (currentSection?.tools || []).map(function (tool, idx) {
          return React.createElement(motion.button, {
            key: tool.id,
            onClick: function () { selectTool(tool); },
            className: `group flex flex-col items-start gap-3 rounded-2xl border bg-[rgba(15,23,42,0.9)] p-6 text-left transition-all ${colors.border}`,
            initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.3, delay: idx * 0.04 },
          },
            React.createElement("div", { className: "flex w-full items-start justify-between" },
              React.createElement(FuturisticIcon, { name: tool.iconName, className: "h-8 w-8 text-sky-400/85" }),
              React.createElement("span", { className: `rounded-full border px-2 py-0.5 text-[10px] ${colors.badge}` }, currentSection?.label)
            ),
            React.createElement("div", null,
              React.createElement("p", { className: "font-semibold text-white" }, tool.label),
              React.createElement("p", { className: "mt-0.5 text-xs text-white/40 leading-relaxed" }, tool.desc)
            )
          );
        })
      ),

      // Context input
      React.createElement(motion.div, { className: "rounded-2xl border border-white/8 bg-[rgba(15,23,42,0.7)] p-5", initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { delay: 0.3 } },
        React.createElement("p", { className: "mb-2 text-xs font-medium text-white/50 uppercase tracking-wider" }, "Contexto persistente (opcional)"),
        React.createElement("textarea", {
          value: context,
          onChange: function (e) { setContext(e.target.value); },
          placeholder: "Informe turma, disciplina, nível ou qualquer contexto que ajude a personalizar todas as respostas...",
          rows: 2,
          className: "w-full resize-none bg-transparent text-sm text-white placeholder:text-white/25 focus:outline-none",
        })
      )
    )
  );
}
