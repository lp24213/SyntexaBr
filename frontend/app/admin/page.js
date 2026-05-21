"use client";

import React, { useState, useEffect } from "react";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";
import { encryptedPath } from "../../lib/routes";
import {
  getAdminAllowedIps,
  getAdminMe,
  getAdminSystemStatus,
  putAdminAllowedIps,
} from "../../lib/api";

// Painel Admin totalmente separado — sem AppShell, layout próprio.
// Acesso somente com is_admin=1 no localStorage.

function AdminGuard({ children }) {
  const [state, setState] = useState("checking");
  useEffect(() => {
    let cancel = false;
    (async function () {
      try {
        const token = window.localStorage.getItem("syntexa_token");
        if (!token) {
          if (!cancel) setState("denied");
          return;
        }
        const me = await getAdminMe(token);
        if (!cancel) setState(me && me.is_admin ? "ok" : "denied");
      } catch {
        if (!cancel) setState("denied");
      }
    })();
    return function () {
      cancel = true;
    };
  }, []);
  if (state === "checking") return React.createElement("div", { className: "flex min-h-screen items-center justify-center bg-[#f8f9fb]" },
    React.createElement("div", { className: "text-zinc-500 text-sm animate-pulse" }, "Verificando acesso…"));
  if (state === "denied") return React.createElement("div", { className: "flex min-h-screen flex-col items-center justify-center gap-5 bg-[#f8f9fb] px-4 text-center" },
    React.createElement("div", { className: "flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-500/30 bg-violet-500/10 text-violet-600" },
      React.createElement(FuturisticIcon, { name: "lock", className: "h-10 w-10" })),
    React.createElement("h1", { className: "text-zinc-900 text-xl font-bold" }, "Acesso restrito"),
    React.createElement("p", { className: "max-w-xs text-sm text-zinc-600" }, "Esta área é exclusiva para o administrador do sistema. Faça login com sua conta admin."),
    React.createElement("a", { href: encryptedPath("login"), className: "mt-2 rounded-xl bg-violet-600 hover:bg-violet-500 px-6 py-2.5 text-sm font-medium text-white transition-colors" }, "Fazer login"));
  return children;
}

const SECTIONS = [
  {
    iconName: "doc",
    title: "Plano de Negócios + Roadmap",
    desc: "Plano executivo com execução de lançamento, GTM, monetização e captação em ritmo operacional.",
    href: "/admin/plano-de-negocios",
    color: "border-emerald-500/40 hover:border-emerald-400/70",
    badge: "Board",
    badgeColor: "bg-emerald-500/20 text-emerald-300",
  },
  {
    iconName: "building",
    title: "Clientes Institucionais",
    desc: "Gerencie licenças/chaves API para escolas, municípios, estados e universidades. Crie, renove e revogue códigos de liberação.",
    href: "/admin/institucional",
    color: "border-violet-500/40 hover:border-violet-400/70",
    badge: "Principal",
    badgeColor: "bg-violet-500/20 text-violet-300",
  },
  {
    iconName: "shield",
    title: "Hub de Segurança",
    desc: "Política de IP, postura operacional e controles administrativos centralizados.",
    href: "/admin/security-hub",
    color: "border-amber-500/40 hover:border-amber-400/70",
    badge: "Security",
    badgeColor: "bg-amber-500/20 text-amber-300",
  },
  {
    iconName: "warn",
    title: "Pentest Admin",
    desc: "Fluxo completo de pentest autorizado: preflight legal, execução controlada e trilha de auditoria total.",
    href: "/admin/pentest-admin",
    color: "border-rose-500/40 hover:border-rose-400/70",
    badge: "Pentest",
    badgeColor: "bg-rose-500/20 text-rose-300",
  },
  {
    iconName: "key",
    title: "API Tokens",
    desc: "Crie tokens para integrar clientes, outras IAs, ERPs e sistemas externos com a API Syntexa.",
    href: "/admin/integrations",
    color: "border-sky-500/40 hover:border-sky-400/70",
    badge: "API",
    badgeColor: "bg-sky-500/20 text-sky-300",
  },
  {
    iconName: "bolt",
    title: "IA soberana & busca híbrida",
    desc: "Arquitetura: motor syntexa_native, RAG, busca multi-fonte (DDG, Wikipedia, notícias, Scholar), citações e score de confiança.",
    href: "/admin/ia-soberana",
    color: "border-emerald-500/40 hover:border-emerald-400/70",
    badge: "Núcleo",
    badgeColor: "bg-emerald-500/20 text-emerald-300",
  },
  {
    iconName: "building",
    title: "Painel Governamental",
    desc: "Ferramentas de análise e relatórios (IA). Indicadores regionais oficiais dependem de integração futura — sem dados fictícios.",
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
    iconName: "doc",
    title: "Runbook Mobile (TI)",
    desc: "Procedimento oficial para distribuição Android/iOS (PWA e Enterprise) com checklist técnico.",
    href: "/admin/mobile-release",
    color: "border-sky-500/40 hover:border-sky-400/70",
    badge: "Ops",
    badgeColor: "bg-sky-500/20 text-sky-300",
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
  { label: "API tokens", href: "/admin/integrations", iconName: "key" },
  { label: "Runbook mobile", href: "/admin/mobile-release", iconName: "doc" },
  { label: "Hub segurança", href: "/admin/security-hub", iconName: "shield" },
  { label: "Pentest Admin", href: "/admin/pentest-admin", iconName: "warn" },
  { label: "Plano + roadmap", href: "/planos", iconName: "doc" },
  { label: "Painel gov.", href: "/educacao/governo", iconName: "building" },
  { label: "Portal", href: "/portal", iconName: "chart" },
  { label: "Docs SEO", href: "/docs", iconName: "book" },
  { label: "Roadmap SEO", href: "/roadmap", iconName: "chart" },
  { label: "Site público", href: "/", iconName: "home" },
];

const STEPS = [
  ["1", "Crie uma licença institucional", "Vá em Clientes Institucionais → Nova licença. Informe nome da instituição, tipo e plano."],
  ["2", "Entregue a chave ao TI", "Copie a chave gerada (formato SYNTEXA-…) e o material de instalação para o responsável na instituição."],
  ["3", "Acompanhe no painel", "Use Clientes Institucionais para status das licenças. Heartbeat e métricas avançadas evoluem conforme o produto."],
];

const MOBILE_RELEASE_STEPS = [
  "Android direto: publique APK assinado no domínio e distribua o link para escolas/universidades.",
  "PWA: os usuários Android podem instalar pelo navegador em 'Instalar app' sem Play Store.",
  "iOS sem App Store: use Apple Enterprise + MDM (ou Ad Hoc por UDID) para instalação institucional.",
  "Licenciamento: valide cada instalação com chave SYNTEXA no endpoint institucional.",
];

const ADVANCED_TOOLS = [
  { title: "Procurar na web", desc: "Pesquisa assistida para respostas atualizadas e verificáveis.", href: "/chat", iconName: "chart" },
  { title: "Canvas estratégico", desc: "Estruture análises, planos e mapas visuais para operações.", href: "/planos", iconName: "doc" },
  { title: "Integração GitHub", desc: "Fluxo técnico para versionamento e entrega contínua.", href: "/admin/mobile-release", iconName: "gear" },
  { title: "Questionários", desc: "Coleta estruturada de dados para instituições e projetos.", href: "/admin/institucional", iconName: "book" },
  { title: "Gerar imagem IA", desc: "Geração com Black Forest Labs e fallback automático.", href: "/download", iconName: "spark" },
  { title: "Investigação profunda", desc: "Módulo para análise mais detalhada de cenários complexos.", href: "/portal", iconName: "bolt" },
  { title: "Documentação pública", desc: "Página otimizada para SEO com visão técnica e institucional.", href: "/docs", iconName: "book" },
  { title: "Roadmap público", desc: "Roadmap de lançamento indexável para SEO e comunicação comercial.", href: "/roadmap", iconName: "chart" },
];

function AdminPage() {
  const [email, setEmail] = useState("");
  const [now, setNow] = useState("");
  const [sys, setSys] = useState(null);
  const [ipsText, setIpsText] = useState("");
  const [ipsSaving, setIpsSaving] = useState(false);

  useEffect(() => {
    try {
      setEmail(window.localStorage.getItem("syntexa_email") || "Administrador");
    } catch {}
    setNow(new Date().toLocaleString("pt-BR"));
    (async function () {
      try {
        const token = window.localStorage.getItem("syntexa_token");
        if (!token) return;
        const [statusData, ipsData] = await Promise.all([
          getAdminSystemStatus(token),
          getAdminAllowedIps(token),
        ]);
        setSys(statusData || null);
        setIpsText(((ipsData && ipsData.ips) || []).join("\n"));
      } catch {}
    })();
  }, []);

  async function saveIps() {
    try {
      setIpsSaving(true);
      const token = window.localStorage.getItem("syntexa_token");
      if (!token) return;
      const lines = ipsText
        .split(/\r?\n/)
        .map((s) => s.trim())
        .filter(Boolean);
      const data = await putAdminAllowedIps(token, lines);
      setIpsText(((data && data.ips) || []).join("\n"));
    } catch {
      // silencioso: UX do admin não deve quebrar fluxo principal
    } finally {
      setIpsSaving(false);
    }
  }

  function logout() {
    try {
      ["syntexa_token", "syntexa_role", "syntexa_is_admin", "syntexa_email"].forEach(k => localStorage.removeItem(k));
    } catch {}
    window.location.href = encryptedPath("login");
  }

  return React.createElement("div", { className: "min-h-screen bg-[#f8f9fb] text-zinc-900" },

    // Header do admin
    React.createElement("header", { className: "sticky top-0 z-20 border-b border-zinc-200 bg-white/95 backdrop-blur-md" },
      React.createElement("div", { className: "mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8" },
        React.createElement("div", { className: "flex items-center gap-3" },
          React.createElement("div", { className: "flex h-9 w-9 items-center justify-center rounded-xl border border-violet-300 bg-violet-50" },
            React.createElement(FuturisticIcon, { name: "bolt", className: "h-5 w-5 text-violet-600" })),
          React.createElement("div", null,
            React.createElement("h1", { className: "text-sm font-bold text-zinc-900 leading-none" }, "Syntexa Admin"),
            React.createElement("p", { className: "text-xs text-zinc-500 mt-0.5" }, "Painel de Controle"))),
        React.createElement("div", { className: "flex items-center gap-3" },
          React.createElement("div", { className: "hidden sm:block text-right" },
            React.createElement("p", { className: "text-xs font-medium text-zinc-700" }, email),
            React.createElement("p", { className: "text-xs text-zinc-600" }, now)),
          React.createElement("button", {
            onClick: logout,
            className: "rounded-lg border border-zinc-300 px-3 py-1.5 text-xs text-zinc-600 transition-colors hover:border-rose-300 hover:text-rose-600",
          }, "Sair")))),

    // Conteúdo
    React.createElement("main", { className: "mx-auto max-w-6xl px-5 py-10 sm:px-8 space-y-10" },

      // Bem-vindo
      React.createElement("div", { className: "rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-transparent p-6" },
        React.createElement("div", { className: "flex flex-wrap items-center justify-between gap-4" },
          React.createElement("div", { className: "flex items-start gap-3" },
            React.createElement("div", { className: "mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-violet-300 bg-violet-50" },
              React.createElement(FuturisticIcon, { name: "spark", className: "h-5 w-5 text-violet-600" })),
            React.createElement("div", null,
              React.createElement("h2", { className: "text-2xl font-bold text-zinc-900" }, "Bem-vindo, Admin"),
              React.createElement("p", { className: "mt-1 text-sm text-zinc-600" }, "Você tem controle total da plataforma Syntexa. Use os módulos abaixo para gerenciar clientes, licenças e o sistema educacional."))),
          React.createElement("div", { className: "flex flex-wrap gap-2" },
            QUICK_LINKS.map(l => React.createElement("a", {
              key: l.href,
              href: encryptedPath((l.href || "").replace(/^\/+/, "")),
              className: l.primary
                ? "inline-flex items-center gap-2 rounded-xl bg-violet-600 hover:bg-violet-500 px-4 py-2 text-sm font-medium text-white transition-colors shadow-lg shadow-violet-900/30"
                : "inline-flex items-center gap-2 rounded-xl border border-zinc-200 hover:border-zinc-300 bg-white hover:bg-zinc-50 px-4 py-2 text-sm text-zinc-700 transition-colors",
            },
              React.createElement(FuturisticIcon, { name: l.iconName, className: "h-4 w-4 shrink-0 opacity-90" }),
              l.label)))),

        // Instruções rápidas
        React.createElement("div", { className: "mt-5 grid grid-cols-1 gap-3 text-xs text-zinc-600 sm:grid-cols-3" },
          STEPS.map(([num, title, text]) =>
            React.createElement("div", { key: num, className: "rounded-xl bg-white border border-zinc-200 p-3" },
              React.createElement("div", { className: "font-semibold text-zinc-800 mb-1 flex items-center gap-2" },
                React.createElement("span", { className: "flex h-6 w-6 items-center justify-center rounded-lg border border-violet-300 bg-violet-50 font-mono text-violet-700" }, num),
                title),
              React.createElement("div", { className: "text-zinc-500 pl-8" }, text))))),

      React.createElement("section", { className: "rounded-2xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm" },
        React.createElement("div", { className: "flex flex-wrap items-start justify-between gap-3" },
          React.createElement("div", null,
            React.createElement("h3", { className: "inline-flex items-center gap-2 text-sm font-semibold text-zinc-900" },
              React.createElement(FuturisticIcon, { name: "doc", className: "h-4 w-4 text-emerald-600" }),
              "Plano de Negócios e Execução no Admin"),
            React.createElement("p", { className: "mt-1 text-xs text-zinc-600" }, "Visão executiva com roadmap operacional de lançamento integrada ao painel administrativo.")),
          React.createElement("a", {
            href: encryptedPath("planos"),
            className: "inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-xs font-medium text-white transition-colors",
          },
            React.createElement(FuturisticIcon, { name: "arrow", className: "h-3.5 w-3.5" }),
            "Abrir plano completo")),
        React.createElement("div", { className: "mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3 text-xs text-zinc-700" },
          React.createElement("div", { className: "rounded-xl border border-emerald-200 bg-white p-3" }, "Resumo executivo, tese de produto e evolução já entregue."),
          React.createElement("div", { className: "rounded-xl border border-emerald-200 bg-white p-3" }, "Roadmap 0-90 dias com foco em lançamento e monetização."),
          React.createElement("div", { className: "rounded-xl border border-emerald-200 bg-white p-3" }, "Captação, risco e expansão condicionados a métricas reais."))),


      // Grade de módulos
      React.createElement("div", null,
        React.createElement("h3", { className: "text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4" }, "Módulos do Sistema"),
        React.createElement("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" },
          SECTIONS.map(s => React.createElement("a", {
            key: s.href,
            href: encryptedPath((s.href || "").replace(/^\/+/, "")),
            className: `group block rounded-2xl border ${s.color} bg-white p-5 shadow-sm transition-all duration-200 hover:bg-zinc-50`,
          },
            React.createElement("div", { className: "flex items-start justify-between gap-2 mb-3" },
              React.createElement("span", { className: "flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-200 bg-zinc-50 text-violet-600" },
                React.createElement(FuturisticIcon, { name: s.iconName, className: "h-6 w-6" })),
              React.createElement("span", { className: `rounded-full px-2 py-0.5 text-xs font-medium ${s.badgeColor}` }, s.badge)),
            React.createElement("h4", { className: "text-sm font-semibold text-zinc-900 mb-1 group-hover:text-violet-700 transition-colors" }, s.title),
            React.createElement("p", { className: "text-xs text-zinc-500 leading-relaxed" }, s.desc))))),

      React.createElement("section", { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement("div", { className: "flex flex-wrap items-start justify-between gap-3" },
          React.createElement("div", null,
            React.createElement("h4", { className: "inline-flex items-center gap-2 text-sm font-semibold text-zinc-900" },
              React.createElement(FuturisticIcon, { name: "download", className: "h-4 w-4 text-violet-600" }),
              "Distribuição Mobile Corporativa"),
            React.createElement("p", { className: "mt-1 text-xs text-zinc-500" }, "Guia operacional para Android e iOS fora de lojas públicas, focado em TI institucional.")),
          React.createElement("a", {
            href: encryptedPath("download"),
            className: "inline-flex items-center gap-2 rounded-xl bg-violet-600 hover:bg-violet-500 px-3 py-2 text-xs font-medium text-white transition-colors",
          },
            React.createElement(FuturisticIcon, { name: "arrow", className: "h-3.5 w-3.5" }),
            "Abrir central de downloads")),
        React.createElement("ol", { className: "mt-4 list-decimal space-y-1.5 pl-5 text-xs text-zinc-600" },
          MOBILE_RELEASE_STEPS.map(function (item, idx) { return React.createElement("li", { key: "m-" + idx }, item); })),
        React.createElement("div", { className: "mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2" },
          React.createElement("a", {
            href: encryptedPath("admin/institucional"),
            className: "rounded-xl border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-100 transition-colors",
          }, "Gerenciar licenças e chaves"),
          React.createElement("a", {
            href: encryptedPath("admin/security-hub"),
            className: "rounded-xl border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-100 transition-colors",
          }, "Política de segurança e IP allowlist"))),

      React.createElement("section", { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement("h4", { className: "text-sm font-semibold text-zinc-900" }, "Ferramentas avançadas"),
        React.createElement("p", { className: "mt-1 text-xs text-zinc-500" }, "Camada expandida do painel com recursos de operação, análise e produtividade."),
        React.createElement("div", { className: "mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3" },
          ADVANCED_TOOLS.map(function (tool) {
            return React.createElement("a", {
              key: tool.title,
              href: encryptedPath((tool.href || "").replace(/^\/+/, "")),
              className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3 hover:bg-zinc-100 transition-colors",
            },
              React.createElement("div", { className: "inline-flex items-center gap-2 text-sm font-medium text-zinc-800" },
                React.createElement(FuturisticIcon, { name: tool.iconName, className: "h-4 w-4 text-violet-600" }),
                tool.title),
              React.createElement("p", { className: "mt-1 text-xs text-zinc-600" }, tool.desc));
          }))),

      React.createElement("div", { className: "grid grid-cols-1 gap-4 lg:grid-cols-2" },
        React.createElement("section", { className: "rounded-xl border border-zinc-200 bg-white p-4" },
          React.createElement("h4", { className: "text-sm font-semibold text-zinc-800 mb-2" }, "Controle de Sistema"),
          React.createElement("p", { className: "text-xs text-zinc-500 mb-3" }, "Visão rápida de carga e concorrência do backend."),
          React.createElement("pre", { className: "max-h-64 overflow-auto rounded-lg bg-zinc-50 p-3 text-[11px] text-zinc-700" },
            JSON.stringify(sys || { loading: "indisponível" }, null, 2))),
        React.createElement("section", { className: "rounded-xl border border-zinc-200 bg-white p-4" },
          React.createElement("h4", { className: "text-sm font-semibold text-zinc-800 mb-2" }, "IPs Permitidos (Admin)"),
          React.createElement("p", { className: "text-xs text-zinc-500 mb-3" }, "Controle de rede institucional para operações restritas."),
          React.createElement("textarea", {
            value: ipsText,
            onChange: function (e) { setIpsText(e.target.value); },
            rows: 8,
            className: "w-full rounded-lg border border-zinc-200 bg-zinc-50 p-2 text-xs text-zinc-700",
            placeholder: "1.2.3.4\n10.0.0.0/24",
          }),
          React.createElement("button", {
            onClick: saveIps,
            disabled: ipsSaving,
            className: "mt-3 rounded-lg bg-violet-600 px-3 py-2 text-xs font-medium text-white hover:bg-violet-500 disabled:opacity-50",
          }, ipsSaving ? "Salvando..." : "Salvar IPs"))),

      // Alerta de segurança
      React.createElement("div", { className: "rounded-xl border border-amber-700/30 bg-amber-900/10 p-4 flex gap-3" },
        React.createElement("div", { className: "text-amber-400 shrink-0 pt-0.5" },
          React.createElement(FuturisticIcon, { name: "shield", className: "h-6 w-6 text-amber-400/90" })),
        React.createElement("div", { className: "space-y-1 text-xs text-zinc-600" },
          React.createElement("p", { className: "font-semibold text-amber-300" }, "Segurança"),
          React.createElement("p", null, "Acesso ao painel admin apenas com sua conta de administrador. Não compartilhe senha nem sessão."),
          React.createElement("p", { className: "text-zinc-500" }, "Chaves de API e segredos do servidor ficam no ambiente da VPS — não aparecem nesta interface."))),
    ),
  );
}

export default function Page() {
  return React.createElement(AdminGuard, null, React.createElement(AdminPage));
}
