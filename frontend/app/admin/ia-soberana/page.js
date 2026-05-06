"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";
import { getAdminMe } from "../../../lib/api";

function AdminGuard({ children }) {
  const [state, setState] = useState("checking");
  useEffect(() => {
    (async function () {
      try {
        const token = window.localStorage.getItem("syntexa_token");
        if (!token) {
          setState("denied");
          return;
        }
        const me = await getAdminMe(token);
        setState(me && me.is_admin ? "ok" : "denied");
      } catch {
        setState("denied");
      }
    })();
  }, []);
  if (state === "checking") {
    return React.createElement("div", { className: "flex min-h-screen items-center justify-center bg-[#f8f9fb]" },
      React.createElement("div", { className: "text-zinc-500 text-sm animate-pulse" }, "Verificando acesso…"));
  }
  if (state === "denied") {
    return React.createElement("div", { className: "flex min-h-screen flex-col items-center justify-center gap-5 bg-[#f8f9fb] px-4 text-center" },
      React.createElement("div", { className: "flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-500/30 bg-violet-500/10 text-violet-600" },
        React.createElement(FuturisticIcon, { name: "lock", className: "h-10 w-10" })),
      React.createElement("h1", { className: "text-zinc-900 text-xl font-bold" }, "Acesso restrito"),
      React.createElement("p", { className: "text-zinc-400 text-sm max-w-xs" }, "Faça login como administrador."),
      React.createElement("a", { href: "/login", className: "mt-2 rounded-xl bg-violet-600 hover:bg-violet-500 px-6 py-2.5 text-sm font-medium text-white transition-colors" }, "Fazer login"));
  }
  return children;
}

const BLOCKS = [
  {
    title: "Extensão prática Brasil (execução)",
    body: [
      "Foco operacional por problema real (não só teoria):",
      "• Financeiro pessoal e empresarial: fluxo de caixa, cobrança, Pix, conciliação e rotina de banco.",
      "• Impostos e regularização no Brasil: IRPF, notas fiscais, documentação e trâmites junto à Receita Federal.",
      "• Vendas: mensagens prontas e cadências para WhatsApp com objetivo de conversão.",
      "• Agronegócio: gestão de fazenda, custos, planejamento de produção e apoio à decisão do produtor rural.",
      "",
      "Diretriz de resposta:",
      "• Priorizar material pronto para uso (mensagens, checklists, processos e documentos).",
      "• Sugerir caminhos mais rápidos e baratos, com linguagem PT-BR e contexto brasileiro.",
      "• Atuação proativa: alertar riscos e propor próximos passos quando fizer sentido.",
    ].join("\n"),
  },
  {
    title: "Motor",
    body: "DEFAULT_LLM=syntexa_native — núcleo proprietário em vereda_ai (sem API de terceiros como caminho principal). Gateways opcionais: LOCAL_LLM_ENDPOINT, EXLLAMA_ENDPOINT, AZURE_TGI, REMOTE_LLM.",
  },
  {
    title: "Busca híbrida",
    body: "vereda_backend/search/: DuckDuckGo, Wikipedia (API), notícias (DDG News), Semantic Scholar quando o texto parece acadêmico, Google Custom Search JSON se GOOGLE_API_KEY + GOOGLE_CSE_ID estiverem definidos. Yahoo: sem scraping (placeholder).",
  },
  {
    title: "RAG & citações",
    body: "vereda_backend/rag/: retriever, embeddings locais via llm_engine.embed, formatação de referências. Chat injeta contexto web + bloco de fontes + linha de confiança no system prompt.",
  },
  {
    title: "Próximos passos",
    body: "Checkpoints PT-BR em training/, pgvector na Azure PostgreSQL, filas de ingestão no Azure Queue, e métricas no Monitor. Evoluir pesos 100% nacionais no seu GPU/VM.",
  },
];

export default function Page() {
  return React.createElement(AdminGuard, null,
    React.createElement("div", { className: "min-h-screen bg-[#f8f9fb] text-zinc-900" },
      React.createElement("header", { className: "border-b border-zinc-200 bg-white/90 backdrop-blur" },
        React.createElement("div", { className: "mx-auto flex max-w-3xl items-center justify-between gap-4 px-5 py-4" },
          React.createElement(Link, { href: "/admin", className: "text-sm text-violet-600 hover:text-violet-500" }, "← Admin"),
          React.createElement("h1", { className: "text-sm font-semibold text-zinc-800" }, "IA soberana"))),
      React.createElement("main", { className: "mx-auto max-w-3xl px-5 py-10 space-y-6" },
        React.createElement("p", { className: "text-sm text-zinc-500" },
          "Referência rápida da arquitetura implementada no repositório. Configuração sensível permanece no servidor (.env)."),
        BLOCKS.map((b) =>
          React.createElement("section", {
            key: b.title,
            className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm",
          },
            React.createElement("h2", { className: "text-sm font-semibold text-zinc-900 mb-2" }, b.title),
            React.createElement("p", { className: "text-sm text-zinc-600 leading-relaxed whitespace-pre-wrap" }, b.body))),
        React.createElement("p", { className: "text-xs text-zinc-400" },
          "Respeite robots.txt e termos das APIs públicas; o backend prioriza conectores documentados."))));
}
