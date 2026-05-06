"use client";

import React from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";

function IconStudent() {
  return React.createElement(
    "svg",
    { className: "h-8 w-8", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M12 3L2 8l10 5 10-5-10-5z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M6 10.5v5c0 1.657 2.686 3 6 3s6-1.343 6-3v-5", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("path", { d: "M22 8v6", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function IconTeacher() {
  return React.createElement(
    "svg",
    { className: "h-8 w-8", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("rect", { x: "2", y: "3", width: "15", height: "13", rx: "2", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M8 21l4-4 4 4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M12 17v4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("path", { d: "M6 8h6M6 11h4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("circle", { cx: "20", cy: "7", r: "2", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M20 9v4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function IconGov() {
  return React.createElement(
    "svg",
    { className: "h-8 w-8", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M3 21h18", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("path", { d: "M3 10h18", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("path", { d: "M5 10V21M9 10V21M15 10V21M19 10V21", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }),
    React.createElement("path", { d: "M12 3L3 10h18L12 3z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" })
  );
}

function IconCheck() {
  return React.createElement(
    "svg",
    { className: "h-4 w-4 text-zinc-500 shrink-0", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M5 13l4 4L19 7", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

const AREAS = [
  {
    key: "aluno",
    href: "/educacao/aluno",
    badge: "Acesso Público",
    badgeColor: "bg-sky-50 text-sky-800 border border-sky-200",
    iconColor: "text-cyan-600",
    accent: "from-white to-sky-50/80",
    borderColor: "border-zinc-200 hover:border-cyan-300/80",
    title: "Área Aluno",
    description: "Tutor de IA do ensino fundamental ao pós-doutorado. Gratuito, sem login, sem limite.",
    cta: "Acessar agora",
    ctaClass: "bg-sky-600 hover:bg-sky-500 text-white border border-sky-500 shadow-sm",
    features: [
      "15 disciplinas (Mat, Fís, Quím, IA, Segurança, Saúde...)",
      "4 níveis: Básico → Especialista",
      "Sessão 100% anônima — nenhum dado armazenado",
      "Exercícios, Simulados ENEM/Vestibular",
      "Suporte em 4 idiomas (PT, EN, ES, ZH)",
    ],
    plan: "Plano Público · Gratuito · Anônimo",
  },
  {
    key: "professor",
    href: "/educacao/professor",
    badge: "Login Obrigatório",
    badgeColor: "bg-violet-50 text-violet-900 border border-violet-200",
    iconColor: "text-cyan-600",
    accent: "from-white to-violet-50/70",
    borderColor: "border-zinc-200 hover:border-violet-300",
    title: "Área Professor / Pesquisador",
    description: "Ferramentas avançadas para docentes, pesquisadores e cientistas.",
    cta: "Entrar na área",
    ctaClass: "bg-violet-600 hover:bg-violet-500 text-white border border-violet-500 shadow-sm",
    features: [
      "Correção automática com rubrica e nota",
      "Geração de provas com taxonomia de Bloom",
      "Planos de aula completos (BNCC)",
      "Análise de papers e escrita acadêmica",
      "Formatação ABNT / APA 7ª edição",
    ],
    plan: "Plano Educacional · Gratuito",
  },
  {
    key: "offline",
    href: "/download",
    badge: "Instalação Local",
    badgeColor: "bg-amber-50 text-amber-900 border border-amber-200",
    iconColor: "text-cyan-600",
    accent: "from-white to-amber-50/70",
    borderColor: "border-zinc-200 hover:border-amber-300",
    title: "Sistema Offline (Download Local)",
    description: "Download aberto para qualquer usuário que queira operar localmente sem internet. Também pode ser implantado por administradores em escolas, universidades e instituições.",
    cta: "Baixar sistema offline",
    ctaClass: "bg-amber-600 hover:bg-amber-500 text-white border border-amber-500 shadow-sm",
    features: [
      "Dashboard nacional por região e escola",
      "Previsões de evasão e desempenho com IA",
      "Gerador de políticas públicas educacionais",
      "Relatórios automáticos para órgãos públicos",
      "Funciona sem internet — dados locais seguros",
    ],
    plan: "Plano Offline · Download local",
  },
];

const ICONS = { aluno: IconStudent, professor: IconTeacher, offline: IconGov };

export default function EducacaoPage() {
  const handleNav = (href) => { window.location.href = href; };

  const heroSection = React.createElement(
    motion.div,
    {
      className: "mb-16 text-center",
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.5 },
    },
    React.createElement(
      "div",
      { className: "mb-4 inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-4 py-1.5 text-xs text-zinc-500" },
      React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-cyan-500 animate-pulse" }),
      "SyntexaBR Educação & Pesquisa"
    ),
    React.createElement("h1", { className: "mb-4 text-4xl font-bold tracking-tight text-zinc-900 sm:text-5xl" }, "Educação & Pesquisa"),
    React.createElement(
      "p",
      { className: "mx-auto max-w-2xl text-lg text-zinc-500" },
      "Plataforma completa de IA educacional — do aluno ao governo. Escolha sua área de acesso."
    )
  );

  const areaCards = React.createElement(
    "div",
    { className: "grid gap-6 md:grid-cols-3" },
    AREAS.map(function (area, idx) {
      const Icon = ICONS[area.key];
      return React.createElement(
        motion.div,
        {
          key: area.key,
          className: `relative flex flex-col overflow-hidden rounded-2xl border bg-gradient-to-b ${area.accent} bg-white p-7 shadow-sm transition-all duration-200 ${area.borderColor}`,
          initial: { opacity: 0, y: 24 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.4, delay: 0.1 + idx * 0.08 },
        },
        React.createElement(
          "div",
          { className: "mb-5 flex items-start justify-between" },
          React.createElement("div", { className: area.iconColor }, React.createElement(Icon, null)),
          React.createElement("span", { className: `rounded-full px-2.5 py-1 text-[11px] font-medium ${area.badgeColor}` }, area.badge)
        ),
        React.createElement("h2", { className: "mb-2 text-xl font-semibold text-zinc-900" }, area.title),
        React.createElement("p", { className: "mb-6 text-sm text-zinc-500 leading-relaxed flex-1" }, area.description),
        React.createElement(
          "ul",
          { className: "mb-7 space-y-2" },
          area.features.map(function (f) {
            return React.createElement(
              "li",
              { key: f, className: "flex items-start gap-2 text-xs text-zinc-500" },
              React.createElement(IconCheck, null),
              f
            );
          })
        ),
        React.createElement(
          "div",
          { className: "mt-auto" },
          React.createElement(
            "p",
            { className: "mb-3 text-[11px] text-zinc-400" },
            area.plan
          ),
          React.createElement(
            "button",
            {
              onClick: function () { handleNav(area.href); },
              className: `w-full rounded-[14px] px-4 py-2.5 text-sm font-medium transition-all ${area.ctaClass}`,
            },
            area.cta
          )
        )
      );
    })
  );

  const labsSection = React.createElement(
    motion.div,
    {
      className: "mt-10",
      initial: { opacity: 0, y: 16 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.4, delay: 0.35 },
    },
    React.createElement(
      "button",
      {
        onClick: function () { window.location.href = "/educacao/laboratorios"; },
        className: "w-full rounded-2xl border border-zinc-200 bg-white p-6 text-left shadow-sm transition-all hover:border-cyan-200 hover:bg-cyan-50/40",
      },
      React.createElement(
        "div",
        { className: "flex items-start justify-between gap-4 flex-wrap" },
        React.createElement(
          "div",
          null,
          React.createElement(
            "div",
            { className: "mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-xs font-medium text-cyan-900" },
            React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-cyan-500" }),
            "Acesso Público"
          ),
          React.createElement("h3", { className: "text-lg font-semibold text-zinc-900 flex items-center gap-2" },
            React.createElement(FuturisticIcon, { name: "flask", className: "h-6 w-6 text-cyan-600" }),
            "Laboratórios Científicos Interativos"),
          React.createElement(
            "p",
            { className: "mt-1 text-sm text-zinc-500" },
            "Simulações físicas em tempo real, motor de cálculo simbólico (SymPy + NumPy), plotter de funções, sandbox Python e estatística — tudo no navegador."
          )
        ),
        React.createElement(
          "div",
          { className: "flex flex-wrap gap-1.5 shrink-0" },
          ["Projétil", "Pêndulo", "Ondas", "Funções", "SymPy", "Química", "Circuitos", "Sorting", "Python", "Estatística"].map(function (lab) {
            return React.createElement("span", { key: lab, className: "rounded-xl border border-zinc-200 bg-zinc-100 px-2 py-1 text-xs text-zinc-500" }, lab);
          })
        )
      )
    )
  );

  const scienceSection = React.createElement(
    motion.div,
    {
      className: "mt-4",
      initial: { opacity: 0, y: 16 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.4, delay: 0.42 },
    },
    React.createElement(
      "button",
      {
        onClick: function () { window.location.href = "/educacao/ciencia"; },
        className: "w-full rounded-2xl border border-zinc-200 bg-white p-6 text-left shadow-sm transition-all hover:border-cyan-200 hover:bg-cyan-50/40",
      },
      React.createElement(
        "div",
        { className: "flex items-start justify-between gap-4 flex-wrap" },
        React.createElement(
          "div",
          null,
          React.createElement(
            "div",
            { className: "mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-xs font-medium text-cyan-900" },
            React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-cyan-500" }),
            "Acesso Público · Anônimo"
          ),
          React.createElement("h3", { className: "text-lg font-semibold text-zinc-900 flex items-center gap-2" },
            React.createElement(FuturisticIcon, { name: "telescope", className: "h-6 w-6 text-cyan-600" }),
            "Ciência & Tecnologia de Ponta"),
          React.createElement(
            "p",
            { className: "mt-1 text-sm text-zinc-500" },
            "Portal especializado: Astronomia, IA & ML, Segurança Digital, Computação Quântica, Bioinformática, Neurociências e muito mais."
          )
        ),
        React.createElement(
          "div",
          { className: "flex flex-wrap gap-1.5 shrink-0" },
          ["Astronomia", "IA & ML", "Segurança", "Quântica", "Bioinformática", "Clima", "Saúde", "Direito"].map(function (area) {
            return React.createElement("span", { key: area, className: "rounded-xl border border-zinc-200 bg-zinc-100 px-2 py-1 text-xs text-zinc-500" }, area);
          })
        )
      )
    )
  );

  const concursosSection = React.createElement(
    motion.div,
    {
      className: "mt-4",
      initial: { opacity: 0, y: 16 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.4, delay: 0.46 },
    },
    React.createElement(
      "button",
      {
        onClick: function () { window.location.href = "/educacao/concursos"; },
        className: "w-full rounded-2xl border border-zinc-200 bg-white p-6 text-left shadow-sm transition-all hover:border-cyan-200 hover:bg-cyan-50/40",
      },
      React.createElement(
        "div",
        { className: "flex items-start justify-between gap-4 flex-wrap" },
        React.createElement(
          "div",
          null,
          React.createElement(
            "div",
            { className: "mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-xs font-medium text-cyan-900" },
            React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-cyan-500" }),
            "Acesso Público · Anônimo"
          ),
          React.createElement("h3", { className: "text-lg font-semibold text-zinc-900 flex items-center gap-2" },
            React.createElement(FuturisticIcon, { name: "medal", className: "h-6 w-6 text-cyan-600" }),
            "Concursos & Vestibulares"),
          React.createElement(
            "p",
            { className: "mt-1 text-sm text-zinc-500" },
            "Tutor especializado com questões no formato real, correção de redação ENEM (0-1000) e resumos para: ENEM, OAB, Residência Médica, FUVEST, ENADE e concursos públicos."
          )
        ),
        React.createElement(
          "div",
          { className: "flex flex-wrap gap-1.5 shrink-0" },
          ["ENEM", "OAB", "Residência", "FUVEST", "ENADE", "Concurso"].map(function (e) {
            return React.createElement("span", { key: e, className: "rounded-xl border border-zinc-200 bg-zinc-100 px-2 py-1 text-xs text-zinc-500" }, e);
          })
        )
      )
    )
  );

  const privacySection = React.createElement(
    motion.div,
    {
      className: "mt-8",
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      transition: { duration: 0.4, delay: 0.5 },
    },
    React.createElement(
      "div",
      { className: "rounded-2xl border border-zinc-200 bg-zinc-50 p-5" },
      React.createElement(
        "div",
        { className: "flex flex-wrap items-center gap-4" },
        React.createElement(
          "div",
          { className: "flex-1 min-w-60" },
          React.createElement(
            "div",
            { className: "flex items-center gap-2 mb-1.5" },
            React.createElement(FuturisticIcon, { name: "lock", className: "h-4 w-4 text-zinc-500" }),
            React.createElement("span", { className: "text-sm font-medium text-zinc-600" }, "Privacidade por Design")
          ),
          React.createElement("p", { className: "text-xs text-zinc-400 leading-relaxed" },
            "Toda interação pública é totalmente anônima. Nenhum dado pessoal, histórico de conversa ou IP " +
            "é armazenado no servidor. Sessões são efêmeras, ficam apenas no navegador do usuário e são " +
            "descartadas ao fechar a aba. Conforme LGPD (Lei 13.709/2018) e GDPR."
          )
        ),
        React.createElement(
          "div",
          { className: "flex flex-wrap gap-2 shrink-0" },
          ["Zero tracking", "Sem cookies", "LGPD compliant", "Privacy by Design", "Anônimo por padrão"].map(function (tag) {
            return React.createElement("span", { key: tag, className: "rounded-full border border-zinc-200 px-2.5 py-1 text-xs text-zinc-400" }, tag);
          })
        )
      )
    )
  );

  const plansSection = React.createElement(
    motion.div,
    {
      className: "mt-20",
      initial: { opacity: 0, y: 16 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.5, delay: 0.4 },
    },
    React.createElement(
      "div",
      { className: "mb-8 text-center" },
      React.createElement("h2", { className: "text-2xl font-semibold text-zinc-900" }, "Planos"),
      React.createElement("p", { className: "mt-1 text-sm text-zinc-500" }, "Acesso transparente e sem surpresas")
    ),
    React.createElement(
      "div",
      { className: "grid gap-4 md:grid-cols-3" },
      [
        {
          name: "Público",
          price: "Gratuito",
          sub: "Para alunos",
          color: "border-sky-500/20",
          items: ["Sem login necessário", "Tutor por disciplina", "Geração de exercícios", "Simulados ENEM/Vestibular", "Acesso ilimitado"],
        },
        {
          name: "Educacional",
          price: "Gratuito",
          sub: "Para professores e pesquisadores",
          color: "border-violet-500/20",
          items: ["Login obrigatório", "Correção de provas", "Criação de materiais", "Gestão de turmas", "Assistente de pesquisa"],
        },
        {
          name: "Governamental",
          price: "Sob demanda",
          sub: "Para instituições e governo",
          color: "border-amber-500/20",
          items: ["Acesso por credencial admin", "Infraestrutura dedicada", "Painel de indicadores nacionais", "Relatórios automatizados", "Suporte prioritário"],
        },
      ].map(function (plan) {
        return React.createElement(
          "div",
          {
            key: plan.name,
            className: `rounded-2xl border bg-zinc-50 p-6 ${plan.color}`,
          },
          React.createElement("h3", { className: "mb-1 text-base font-semibold text-zinc-900" }, plan.name),
          React.createElement("p", { className: "mb-1 text-2xl font-bold text-zinc-900" }, plan.price),
          React.createElement("p", { className: "mb-4 text-xs text-zinc-500" }, plan.sub),
          React.createElement(
            "ul",
            { className: "space-y-1.5" },
            plan.items.map(function (item) {
              return React.createElement(
                "li",
                { key: item, className: "flex items-center gap-2 text-xs text-zinc-500" },
                React.createElement(IconCheck, null),
                item
              );
            })
          )
        );
      })
    )
  );

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "py-8" },
      heroSection,
      areaCards,
      labsSection,
      scienceSection,
      concursosSection,
      privacySection,
      plansSection
    )
  );
}
