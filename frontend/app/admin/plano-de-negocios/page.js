"use client";

import React, { useState, useEffect } from "react";
import { BusinessPlanPage } from "../../../components/business-plan-page";
import { getAdminMe } from "../../../lib/api";
import { encryptedPath } from "../../../lib/routes";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";

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
  if (state === "checking")
    return React.createElement(
      "div",
      { className: "flex min-h-screen items-center justify-center bg-[#f8f9fb]" },
      React.createElement("div", { className: "text-zinc-500 text-sm animate-pulse" }, "Verificando acesso…")
    );
  if (state === "denied")
    return React.createElement(
      "div",
      { className: "flex min-h-screen flex-col items-center justify-center gap-5 bg-[#f8f9fb] px-4 text-center" },
      React.createElement(
        "div",
        { className: "flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-500/30 bg-violet-500/10 text-violet-600" },
        React.createElement(FuturisticIcon, { name: "lock", className: "h-10 w-10" })
      ),
      React.createElement("h1", { className: "text-zinc-900 text-xl font-bold" }, "Acesso restrito"),
      React.createElement(
        "p",
        { className: "max-w-xs text-sm text-zinc-600" },
        "Esta área é exclusiva para o administrador do sistema. Faça login com sua conta admin."
      ),
      React.createElement(
        "a",
        {
          href: encryptedPath("login"),
          className: "mt-2 rounded-xl bg-violet-600 hover:bg-violet-500 px-6 py-2.5 text-sm font-medium text-white transition-colors",
        },
        "Fazer login"
      )
    );
  return children;
}

var plans = [
  { key: "free", name: "Gratuito", tag: "Sem cartão", price: "R$ 0", priceLabel: "/mês", priceStudent: "R$ 0", studentLabel: "para sempre", description: "120 mensagens por dia para experimentar. Chat, pesquisa na web e respostas inteligentes — sem cartão.", features: ["120 mensagens por dia", "Chat com pesquisa na web", "Respostas com contexto e citações", "Sem cartão de crédito"], highlighted: false },
  { key: "basic", name: "Básico", tag: "Para começar", price: "R$ 39", priceLabel: "/mês", priceStudent: "R$ 19,50", studentLabel: "estudante/mês", description: "500 mensagens/mês, upload de arquivos e respostas mais completas. Ideal para estudantes e freelancers.", features: ["500 mensagens/mês", "Upload de PDF, Word, Excel e imagens", "Respostas detalhadas com fontes", "Exportação para PDF e Word"], highlighted: false },
  { key: "medium", name: "Médio", tag: "Mais usado", price: "R$ 99", priceLabel: "/mês", priceStudent: "R$ 49,50", studentLabel: "estudante/mês", description: "Mensagens ilimitadas, geração de imagem/vídeo/áudio, código e contexto estendido. Para profissionais.", features: ["Mensagens ilimitadas (uso justo)", "Geração de imagem, vídeo e áudio", "Análise de código e dados", "Contexto estendido para projetos longos"], highlighted: true },
  { key: "master", name: "Master", tag: "Empresas", price: "R$ 199", priceLabel: "/mês", priceStudent: "R$ 99,50", studentLabel: "estudante/mês", description: "Tudo ilimitado + agentes avançados, suporte prioritário, múltiplos usuários e ferramentas empresariais.", features: ["Tudo do plano Médio, sem limites", "Agentes autônomos e automações", "Múltiplos usuários e SSO", "Suporte prioritário e SLA dedicado"], highlighted: false },
];

export default function PlanoDeNegociosAdminPage() {
  return React.createElement(
    AdminGuard,
    null,
    React.createElement("div", { className: "min-h-screen bg-white" }, React.createElement(BusinessPlanPage, { plans: plans, onSubscribe: function () { alert("Ação de assinatura não disponível no painel admin."); } }))
  );
}
