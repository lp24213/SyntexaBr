"use client";

import React, { useEffect } from "react";
import { AppShell } from "../../components/shell";
import { createStripeCheckout, getProfile } from "../../lib/api";
import { PlanCard } from "../../components/business-plan-page";
import { getClientLocale, t } from "../../lib/i18n";

function getPlanData(locale) {
  return [
    {
      key: "free",
      name: t('planFreeTitle', locale),
      tag: t('planFreeTag', locale),
      price: t('planFreePrice', locale),
      priceLabel: t('perMonth', locale),
      priceStudent: t('planFreePrice', locale),
      studentLabel: t('forEver', locale),
      description: t('planFreeDescription', locale),
      features: [
      "120 mensagens por dia",
      "Chat com pesquisa na web",
      "Respostas com contexto e citações",
      "WhatsApp IA: 1 número",
      "Exportação PDF simples",
      "Sem cartão de crédito",
      ],
      highlighted: false,
  },
    {
      key: "basic",
      name: t('planBasicTitle', locale),
      tag: t('planBasicTag', locale),
      price: t('planBasicPrice', locale),
      priceLabel: t('perMonth', locale),
      priceStudent: "R$ 19,50",
      studentLabel: t('perStudentMonth', locale),
      description: t('planBasicDescription', locale),
      features: [
      "500 mensagens/mês",
      "Upload de PDF, Word, Excel e imagens",
      "Respostas detalhadas com fontes",
      "WhatsApp IA: 1 número + 500 msgs",
      "PDF e Word profissionais",
      "Excel com gráficos e fórmulas",
      ],
      highlighted: false,
  },
    {
      key: "medium",
      name: t('planMediumTitle', locale),
      tag: t('planMediumTag', locale),
      price: t('planMediumPrice', locale),
      priceLabel: t('perMonth', locale),
      priceStudent: "R$ 49,50",
      studentLabel: t('perStudentMonth', locale),
      description: t('planMediumDescription', locale),
      features: [
      "Mensagens ilimitadas (uso justo)",
      "Geração de imagem, vídeo e áudio",
      "Análise de código e dados",
      "WhatsApp IA: 3 números + ilimitado",
      "Document Engine completo (PDF/Word/Excel)",
      "Automações e chatbot empresarial",
      "Contexto estendido para projetos longos",
      ],
      highlighted: true,
  },
    {
      key: "master",
      name: t('planMasterTitle', locale),
      tag: t('planMasterTag', locale),
      price: t('planMasterPrice', locale),
      priceLabel: t('perMonth', locale),
      priceStudent: "R$ 99,50",
      studentLabel: t('perStudentMonth', locale),
      description: t('planMasterDescription', locale),
      features: [
      "Tudo do plano Médio, sem limites",
      "WhatsApp IA: números ilimitados",
      "Agentes autônomos e automações",
      "White-label disponível",
      "Múltiplos usuários e SSO",
      "API empresarial completa",
      "Suporte prioritário e SLA dedicado",
      ],
      highlighted: false,
    },
  ];
}

export default function PlanosPage() {
  const locale = getClientLocale();
  const plans = getPlanData(locale);

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
      alert(t('checkoutError', locale) + msg);
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
        React.createElement("h1", { className: "text-3xl font-semibold tracking-tight text-zinc-900" }, t('plansPageTitle', locale)),
        React.createElement(
          "p",
          { className: "mt-3 text-[15px] text-zinc-600" },
          t('plansPageDescription', locale)
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

