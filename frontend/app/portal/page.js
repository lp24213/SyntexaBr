"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";

var DOMAINS = [
  {
    id: "chat",
    iconName: "chat",
    title: "Chat Tradicional",
    subtitle: "Aberto · Open Source",
    color: "border-sky-500/30 hover:border-sky-400/60",
    bg: "from-sky-500/5",
    badge: "Público",
    badgeColor: "bg-sky-500/15 text-sky-300 border-sky-500/25",
    description: "Chat de IA open, sem login. Conversas anônimas com memória de sessão.",
    links: [
      { label: "Iniciar chat", href: "/chat", primary: true },
    ],
    items: [
      "Chat livre com IA (sem login)",
      "Sessão anônima — sem dados armazenados",
      "Modo público gratuito com limites",
      "Modo autenticado com memória de longo prazo",
    ],
  },
  {
    id: "educacao",
    iconName: "book",
    title: "Educação Pública",
    subtitle: "Anônima · Sem Login",
    color: "border-violet-500/30 hover:border-violet-400/60",
    bg: "from-violet-500/5",
    badge: "Anônimo",
    badgeColor: "bg-violet-500/15 text-violet-300 border-violet-500/25",
    description: "Tutor de IA gratuito, laboratórios científicos interativos, preparação para concursos. Nenhum dado identificável é coletado.",
    links: [
      { label: "Área Aluno", href: "/educacao/aluno", primary: true },
      { label: "Laboratórios", href: "/educacao/laboratorios" },
      { label: "Ciência & Tech", href: "/educacao/ciencia" },
      { label: "Concursos", href: "/educacao/concursos" },
    ],
    items: [
      "15 disciplinas do fundamental ao pós-doc",
      "Laboratórios de Física, Química, Algoritmos",
      "Concursos: ENEM, OAB, Residência, FUVEST",
      "Suporte em 4 idiomas — PT, EN, ES, ZH",
    ],
  },
  {
    id: "professor",
    iconName: "userTie",
    title: "Área Profissional",
    subtitle: "Login Obrigatório · Teacher/Researcher",
    color: "border-emerald-500/30 hover:border-emerald-400/60",
    bg: "from-emerald-500/5",
    badge: "Autenticado",
    badgeColor: "bg-emerald-500/15 text-emerald-300 border-emerald-500/25",
    description: "Ferramentas avançadas para professores, pesquisadores e cientistas. Acesso com login — role teacher ou researcher.",
    links: [
      { label: "Área do Professor", href: "/educacao/professor", primary: true },
      { label: "Cadastrar", href: "/cadastro" },
    ],
    items: [
      "Correção automática e geração de provas",
      "Análise de papers e escrita acadêmica (ABNT/APA)",
      "Dashboard de desempenho de alunos",
      "Motor de cálculo simbólico (SymPy)",
    ],
  },
  {
    id: "governo",
    iconName: "building",
    title: "Sistema Institucional",
    subtitle: "Instalação Offline · Escolas e Universidades",
    color: "border-amber-500/30 hover:border-amber-400/60",
    bg: "from-amber-500/5",
    badge: "Offline Only",
    badgeColor: "bg-amber-500/15 text-amber-300 border-amber-500/25",
    description: "Módulo governamental distribuído localmente pelo administrador. Não disponível no site público — instalado em redes internas de instituições de ensino.",
    links: [
      { label: "Baixar sistema", href: "/download", primary: true },
    ],
    items: [
      "Dashboard nacional por região e escola",
      "Previsões de evasão e desempenho com IA",
      "Gerador de políticas públicas educacionais",
      "Funciona 100% offline — dados locais seguros",
    ],
  },
];

function CheckIcon() {
  return React.createElement(
    "svg",
    { className: "h-3.5 w-3.5 shrink-0 text-zinc-500", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M5 13l4 4L19 7", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

export default function PortalPage() {
  var [role, setRole] = useState("user");
  var [authed, setAuthed] = useState(false);

  useEffect(function () {
    try {
      setRole(window.localStorage.getItem("syntexa_role") || "user");
      setAuthed(!!window.localStorage.getItem("syntexa_token"));
    } catch {}
  }, []);

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto max-w-5xl py-4" },

      // Hero
      React.createElement(
        motion.div,
        {
          className: "mb-14 text-center",
          initial: { opacity: 0, y: 16 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.4 },
        },
        React.createElement(
          "div",
          { className: "mb-4 inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-4 py-1.5 text-xs text-zinc-500" },
          React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-sky-400 animate-pulse" }),
          "SyntexaBR — Mapa da Plataforma"
        ),
        React.createElement("h1", { className: "mb-3 text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl" }, "Portal SyntexaBR"),
        React.createElement("p", { className: "mx-auto max-w-xl text-base text-zinc-500" },
          "Entenda a separação de domínios e escolha a área certa para você.")
      ),

      // Role badge if authed
      authed && React.createElement(
        "div",
        { className: "mb-8 flex justify-center" },
        React.createElement(
          "div",
          { className: "inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-4 py-2 text-xs text-zinc-600" },
          "Sessão ativa — papel: ",
          React.createElement("span", { className: "font-semibold text-zinc-900" }, role)
        )
      ),

      // Domain cards
      React.createElement(
        "div",
        { className: "grid gap-5 sm:grid-cols-2" },
        DOMAINS.map(function (domain, idx) {
          return React.createElement(
            motion.div,
            {
              key: domain.id,
              className: "flex flex-col rounded-2xl border bg-gradient-to-b " + domain.bg + " from-white to-zinc-50 p-6 transition-all duration-200 " + domain.color,
              initial: { opacity: 0, y: 20 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 0.35, delay: idx * 0.07 },
            },

            // Header
            React.createElement(
              "div",
              { className: "mb-4 flex items-start justify-between" },
              React.createElement(
                "div",
                null,
                React.createElement("div", { className: "mb-1 flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-200 bg-white" },
                  React.createElement(FuturisticIcon, { name: domain.iconName, className: "h-7 w-7 text-sky-500/85" })),
                React.createElement("h2", { className: "text-lg font-semibold text-zinc-900" }, domain.title),
                React.createElement("p", { className: "text-xs text-zinc-500" }, domain.subtitle)
              ),
              React.createElement(
                "span",
                { className: "shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-medium " + domain.badgeColor },
                domain.badge
              )
            ),

            React.createElement("p", { className: "mb-4 flex-1 text-sm leading-relaxed text-zinc-600" }, domain.description),

            // Feature list
            React.createElement(
              "ul",
              { className: "mb-5 space-y-1.5" },
              domain.items.map(function (item) {
                return React.createElement(
                  "li",
                  { key: item, className: "flex items-start gap-2 text-xs text-zinc-600" },
                  React.createElement(CheckIcon, null),
                  item
                );
              })
            ),

            // Links
            React.createElement(
              "div",
              { className: "mt-auto flex flex-wrap gap-2" },
              domain.links.map(function (link) {
                return React.createElement(
                  "a",
                  {
                    key: link.href,
                    href: link.href,
                    className: link.primary
                      ? "rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs font-medium text-zinc-900 transition-colors hover:bg-zinc-50"
                      : "rounded-xl border border-zinc-200 px-4 py-2 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-50 hover:text-zinc-900",
                  },
                  link.label
                );
              })
            )
          );
        })
      ),

      // Security note
      React.createElement(
        motion.div,
        {
          className: "mt-10 rounded-xl border border-zinc-200 bg-zinc-50 p-5",
          initial: { opacity: 0 },
          animate: { opacity: 1 },
          transition: { delay: 0.5 },
        },
        React.createElement("h3", { className: "mb-3 text-sm font-semibold text-zinc-600 flex items-center gap-2" },
          React.createElement(FuturisticIcon, { name: "shield", className: "h-4 w-4 text-zinc-500" }),
          "Separação de Jurisdição"),
        React.createElement(
          "div",
          { className: "grid gap-3 text-xs text-zinc-500 sm:grid-cols-3" },
          React.createElement("div", null,
            React.createElement("div", { className: "mb-1 font-medium text-zinc-600" }, "Público / Aberto"),
            "Chat tradicional e toda a área Educação pública. Sessões anônimas, sem login, sem dados armazenados."),
          React.createElement("div", null,
            React.createElement("div", { className: "mb-1 font-medium text-zinc-600" }, "Autenticado"),
            "Professores e pesquisadores com login. Ferramentas avançadas com identidade protegida por JWT."),
          React.createElement("div", null,
            React.createElement("div", { className: "mb-1 font-medium text-zinc-600" }, "Offline / Institucional"),
            "Sistema governamental instalado localmente. Sem tráfego para o site público. Dados internos à instituição.")
        )
      )
    )
  );
}
