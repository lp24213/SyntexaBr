"use client";

import React, { useEffect } from "react";
import { AppShell } from "../../components/shell";
import { createStripeCheckout, getProfile } from "../../lib/api";
import { PlanCard } from "../../components/business-plan-page";

var plans = [
  {
    key: "free",
    name: "Gratuito",
    tag: "Sem cartão",
    price: "R$ 0",
    priceLabel: "/mês",
    priceStudent: "R$ 0",
    studentLabel: "para sempre",
    description: "120 mensagens por dia para experimentar. Chat, pesquisa na web e respostas inteligentes — sem cartão.",
    features: [
      "120 mensagens por dia",
      "Chat com pesquisa na web",
      "Respostas com contexto e citações",
      "Sem cartão de crédito",
    ],
    highlighted: false,
  },
  {
    key: "basic",
    name: "Básico",
    tag: "Para começar",
    price: "R$ 39",
    priceLabel: "/mês",
    priceStudent: "R$ 19,50",
    studentLabel: "estudante/mês",
    description: "500 mensagens/mês, upload de arquivos e respostas mais completas. Ideal para estudantes e freelancers.",
    features: [
      "500 mensagens/mês",
      "Upload de PDF, Word, Excel e imagens",
      "Respostas detalhadas com fontes",
      "Exportação para PDF e Word",
    ],
    highlighted: false,
  },
  {
    key: "medium",
    name: "Médio",
    tag: "Mais usado",
    price: "R$ 99",
    priceLabel: "/mês",
    priceStudent: "R$ 49,50",
    studentLabel: "estudante/mês",
    description: "Mensagens ilimitadas, geração de imagem/vídeo/áudio, código e contexto estendido. Para profissionais.",
    features: [
      "Mensagens ilimitadas (uso justo)",
      "Geração de imagem, vídeo e áudio",
      "Análise de código e dados",
      "Contexto estendido para projetos longos",
    ],
    highlighted: true,
  },
  {
    key: "master",
    name: "Master",
    tag: "Empresas",
    price: "R$ 199",
    priceLabel: "/mês",
    priceStudent: "R$ 99,50",
    studentLabel: "estudante/mês",
    description: "Tudo ilimitado + agentes avançados, suporte prioritário, múltiplos usuários e ferramentas empresariais.",
    features: [
      "Tudo do plano Médio, sem limites",
      "Agentes autônomos e automações",
      "Múltiplos usuários e SSO",
      "Suporte prioritário e SLA dedicado",
    ],
    highlighted: false,
  },
];

export default function PlanosPage() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("success") !== "1") return;
    const token = window.localStorage.getItem("syntexa_token");
    if (!token) return;
    getProfile(token).then((profile) => {
      if (profile && profile.subscription_plan) {
        window.localStorage.setItem("syntexa_plan", profile.subscription_plan);
      }
    });
  }, []);

  async function handleSubscribe(planKey) {
    if (planKey === "free") {
      // Plano gratuito: redireciona para cadastro/chat sem checkout.
      if (typeof window === "undefined") return;
      const token = window.localStorage.getItem("syntexa_token");
      window.location.href = token ? "/chat" : "/cadastro";
      return;
    }
    try {
      const token = typeof window !== "undefined" ? window.localStorage.getItem("syntexa_token") : null;
      var url = await createStripeCheckout(planKey, token || undefined);
      if (url) window.location.href = url;
    } catch (err) {
      var msg = err instanceof Error ? err.message : String(err);
      alert("Erro ao iniciar pagamento: " + msg);
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto w-full max-w-[1200px] px-4 py-12 sm:px-6" },
      React.createElement(
        "div",
        { className: "mb-8 text-center" },
        React.createElement("h1", { className: "text-3xl font-semibold tracking-tight text-zinc-900" }, "Planos Syntexa"),
        React.createElement(
          "p",
          { className: "mt-3 text-[15px] text-zinc-600" },
          "Escolha o plano que faz sentido para você. Estudante com e-mail .edu paga metade em qualquer plano pago."
        )
      ),
      React.createElement(
        "div",
        { className: "grid gap-5 sm:grid-cols-2 lg:grid-cols-4" },
        plans.map(function (plan) {
          return React.createElement(PlanCard, { key: plan.key, plan: plan, onSubscribe: handleSubscribe });
        })
      )
    )
  );
}

