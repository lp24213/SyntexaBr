"use client";

import React, { useState, useEffect } from "react";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";

// Painel Admin totalmente separado — sem AppShell, layout próprio.
// Acesso somente com is_admin=1 no localStorage.

function AdminGuard({ children }) {
  const [state, setState] = useState("checking");
  useEffect(() => {
    try {
      const isAdmin = window.localStorage.getItem("syntexa_is_admin") === "1";
      const token = window.localStorage.getItem("syntexa_token");
      setState(isAdmin && token ? "ok" : "denied");
    } catch {
      setState("denied");
    }
  }, []);
  if (state === "checking") return React.createElement("div", { className: "flex min-h-screen items-center justify-center bg-zinc-950" },
    React.createElement("div", { className: "text-zinc-500 text-sm animate-pulse" }, "Verificando acesso…"));
  if (state === "denied") return React.createElement("div", { className: "flex min-h-screen flex-col items-center justify-center gap-5 bg-zinc-950 px-4 text-center" },
    React.createElement("div", { className: "flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-500/30 bg-violet-500/10 text-violet-300" },
      React.createElement(FuturisticIcon, { name: "lock", className: "h-10 w-10" })),
    React.createElement("h1", { className: "text-white text-xl font-bold" }, "Acesso restrito"),
    React.createElement("p", { className: "text-zinc-400 text-sm max-w-xs" }, "Esta área é exclusiva para o administrador do sistema. Faça login com sua conta admin."),
    React.createElement("a", { href: "/login", className: "mt-2 rounded-xl bg-violet-600 hover:bg-violet-500 px-6 py-2.5 text-sm font-medium text-white transition-colors" }, "Fazer login"));
  return children;
}

const SECTIONS = [
  {
    iconName: "building",
    title: "Clientes Institucionais",
    desc: "Gerencie licenças para escolas, municípios, estados e governo federal. Crie, renove e revogue chaves de acesso.",
    href: "/admin/institucional",
    color: "border-violet-500/40 hover:border-violet-400/70",
    badge: "Principal",
    badgeColor: "bg-violet-500/20 text-violet-300",
  },
  {
    iconName: "building",
    title: "Painel Governamental",
    desc: "Dashboard educacional nacional: desempenho por região, previsões IA, políticas públicas. Visível apenas para admins.",
    href: "/educacao/governo",
    color: "border-amber-500/40 hover:border-amber-400/70",
    badge: "Restrito",
    badgeColor: "bg-amber-500/20 text-amber-300",
  },
  {
    iconName: "chat",
    title: "Chat & Base de Conhecimento",
    desc: "Adicione itens à base de conhecimento interna. Monitore sessões e conversas do sistema.",
    href: "/chat",
    color: "border-sky-500/40 hover:border-sky-400/70",
    badge: "Chat",
    badgeColor: "bg-sky-500/20 text-sky-300",
  },
  {
    iconName: "book",
    title: "Hub Educacional",
    desc: "Acesse todas as áreas educacionais: Aluno, Professor, Laboratórios, Ciência, Concursos.",
    href: "/educacao",
    color: "border-emerald-500/40 hover:border-emerald-400/70",
    badge: "Educação",
    badgeColor: "bg-emerald-500/20 text-emerald-300",
  },
  {
    iconName: "download",
    title: "Sistema Offline (Download)",
    desc: "Baixe o pacote do sistema institucional para instalar em escolas e prefeituras. Após a instalação, insira a chave de licença.",
    href: "/download",
    color: "border-rose-500/40 hover:border-rose-400/70",
    badge: "Deploy",
    badgeColor: "bg-rose-500/20 text-rose-300",
  },
  {
    iconName: "gear",
    title: "Configurações",
    desc: "Configurações da conta, perfil e preferências do sistema.",
    href: "/config",
    color: "border-zinc-500/40 hover:border-zinc-400/70",
    badge: "Config",
    badgeColor: "bg-zinc-600/40 text-zinc-400",
  },
];

const QUICK_LINKS = [
  { label: "Nova licença institucional", href: "/admin/institucional", primary: true, iconName: "plus" },
  { label: "Painel gov.", href: "/educacao/governo", iconName: "building" },
  { label: "Portal", href: "/portal", iconName: "chart" },
  { label: "Site público", href: "/", iconName: "home" },
];

const STEPS = [
  ["1", "Crie uma licença institucional", "Vá em Clientes Institucionais → Nova licença. Informe nome da escola/prefeitura, tipo e plano."],
  ["2", "Entregue a chave ao TI", "Copie a chave gerada (SYNTEXA-XXXX-XXXX-XXXX) e baixe o Guia de Instalação para o técnico da instituição."],
  ["3", "Monitore online/offline", "O sistema instalado envia sinal a cada hora. Você verá o indicador Online no painel quando estiver ativo."],
];

function AdminPage() {
  const [email, setEmail] = useState("");
  const [now, setNow] = useState("");

  useEffect(() => {
    try { setEmail(window.localStorage.getItem("syntexa_email") || "Administrador"); } catch {}
    setNow(new Date().toLocaleString("pt-BR"));
  }, []);

  function logout() {
    try {
      ["syntexa_token", "syntexa_role", "syntexa_is_admin", "syntexa_email"].forEach(k => localStorage.removeItem(k));
    } catch {}
    window.location.href = "/login";
  }

  return React.createElement("div", { className: "min-h-screen bg-zinc-950 text-white" },

    // Header do admin
    React.createElement("header", { className: "sticky top-0 z-20 border-b border-zinc-800/60 bg-zinc-950/90 backdrop-blur-md" },
      React.createElement("div", { className: "mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8" },
        React.createElement("div", { className: "flex items-center gap-3" },
          React.createElement("div", { className: "flex h-9 w-9 items-center justify-center rounded-xl bg-violet-600/20 border border-violet-500/30" },
            React.createElement(FuturisticIcon, { name: "bolt", className: "h-5 w-5 text-violet-300" })),
          React.createElement("div", null,
            React.createElement("h1", { className: "text-sm font-bold text-white leading-none" }, "Syntexa Admin"),
            React.createElement("p", { className: "text-xs text-zinc-500 mt-0.5" }, "Painel de Controle"))),
        React.createElement("div", { className: "flex items-center gap-3" },
          React.createElement("div", { className: "hidden sm:block text-right" },
            React.createElement("p", { className: "text-xs font-medium text-zinc-300" }, email),
            React.createElement("p", { className: "text-xs text-zinc-600" }, now)),
          React.createElement("button", {
            onClick: logout,
            className: "rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:border-rose-700/60 hover:text-rose-400 transition-colors",
          }, "Sair")))),

    // Conteúdo
    React.createElement("main", { className: "mx-auto max-w-6xl px-5 py-10 sm:px-8 space-y-10" },

      // Bem-vindo
      React.createElement("div", { className: "rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-transparent p-6" },
        React.createElement("div", { className: "flex flex-wrap items-center justify-between gap-4" },
          React.createElement("div", { className: "flex items-start gap-3" },
            React.createElement("div", { className: "mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-violet-500/25 bg-violet-500/10" },
              React.createElement(FuturisticIcon, { name: "spark", className: "h-5 w-5 text-violet-300" })),
            React.createElement("div", null,
              React.createElement("h2", { className: "text-2xl font-bold text-white" }, "Bem-vindo, Admin"),
              React.createElement("p", { className: "text-sm text-zinc-400 mt-1" }, "Você tem controle total da plataforma Syntexa. Use os módulos abaixo para gerenciar clientes, licenças e o sistema educacional."))),
          React.createElement("div", { className: "flex flex-wrap gap-2" },
            QUICK_LINKS.map(l => React.createElement("a", {
              key: l.href,
              href: l.href,
              className: l.primary
                ? "inline-flex items-center gap-2 rounded-xl bg-violet-600 hover:bg-violet-500 px-4 py-2 text-sm font-medium text-white transition-colors shadow-lg shadow-violet-900/30"
                : "inline-flex items-center gap-2 rounded-xl border border-zinc-700 hover:border-zinc-500 bg-zinc-800/60 hover:bg-zinc-700/60 px-4 py-2 text-sm text-zinc-300 transition-colors",
            },
              React.createElement(FuturisticIcon, { name: l.iconName, className: "h-4 w-4 shrink-0 opacity-90" }),
              l.label)))),

        // Instruções rápidas
        React.createElement("div", { className: "mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs text-zinc-400" },
          STEPS.map(([num, title, text]) =>
            React.createElement("div", { key: num, className: "rounded-xl bg-zinc-800/40 border border-zinc-700/40 p-3" },
              React.createElement("div", { className: "font-semibold text-zinc-200 mb-1 flex items-center gap-2" },
                React.createElement("span", { className: "flex h-6 w-6 items-center justify-center rounded-lg border border-violet-500/30 bg-violet-500/10 font-mono text-violet-300" }, num),
                title),
              React.createElement("div", { className: "text-zinc-500 pl-8" }, text))))),


      // Grade de módulos
      React.createElement("div", null,
        React.createElement("h3", { className: "text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4" }, "Módulos do Sistema"),
        React.createElement("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" },
          SECTIONS.map(s => React.createElement("a", {
            key: s.href,
            href: s.href,
            className: `group block rounded-2xl border ${s.color} bg-zinc-900/50 p-5 transition-all duration-200 hover:bg-zinc-800/60`,
          },
            React.createElement("div", { className: "flex items-start justify-between gap-2 mb-3" },
              React.createElement("span", { className: "flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-violet-200" },
                React.createElement(FuturisticIcon, { name: s.iconName, className: "h-6 w-6" })),
              React.createElement("span", { className: `rounded-full px-2 py-0.5 text-xs font-medium ${s.badgeColor}` }, s.badge)),
            React.createElement("h4", { className: "text-sm font-semibold text-white mb-1 group-hover:text-violet-300 transition-colors" }, s.title),
            React.createElement("p", { className: "text-xs text-zinc-500 leading-relaxed" }, s.desc))))),

      // Alerta de segurança
      React.createElement("div", { className: "rounded-xl border border-amber-700/30 bg-amber-900/10 p-4 flex gap-3" },
        React.createElement("div", { className: "text-amber-400 shrink-0 pt-0.5" },
          React.createElement(FuturisticIcon, { name: "shield", className: "h-6 w-6 text-amber-400/90" })),
        React.createElement("div", { className: "text-xs text-zinc-400 space-y-1" },
          React.createElement("p", { className: "font-semibold text-amber-300" }, "Segurança do Admin"),
          React.createElement("p", null, "Este painel é acessível apenas via login com e-mail e senha de administrador. Nunca compartilhe suas credenciais."),
          React.createElement("p", null, "Em produção, altere a ", React.createElement("code", { className: "text-amber-300" }, "VEREDA_SECRET_KEY"), " no arquivo ", React.createElement("code", { className: "text-amber-300" }, ".env"), " para uma chave forte e única."),
          React.createElement("p", null, "O arquivo ", React.createElement("code", { className: "text-amber-300" }, ".env"), " está no ", React.createElement("code", { className: "text-amber-300" }, ".gitignore"), " — nunca será enviado ao repositório."))),
    ),
  );
}

export default function Page() {
  return React.createElement(AdminGuard, null, React.createElement(AdminPage));
}
