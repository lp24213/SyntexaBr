"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../components/shell";
import { createStripeCheckout, getSubscriptionStatus } from "../../lib/api";
import { PlanCard } from "../../components/business-plan-page";
import { t } from "../../lib/i18n";
import { useLanguage } from "../../components/language-provider";

// Icones SVG
const CheckIcon = () => React.createElement("svg", { width: "16", height: "16", viewBox: "0 0 16 16", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
  React.createElement("path", { d: "M13.5 4.5L6 12L2.5 8.5", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round" })
);

const TrialIcon = () => React.createElement("svg", { width: "20", height: "20", viewBox: "0 0 20 20", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
  React.createElement("circle", { cx: "10", cy: "10", r: "8", stroke: "currentColor", strokeWidth: "2" }),
  React.createElement("path", { d: "M10 6V10L13 13", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" })
);

const AlertIcon = () => React.createElement("svg", { width: "20", height: "20", viewBox: "0 0 20 20", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
  React.createElement("path", { d: "M10 7V10", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" }),
  React.createElement("path", { d: "M10 13H10.01", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" }),
  React.createElement("circle", { cx: "10", cy: "10", r: "8", stroke: "currentColor", strokeWidth: "2" })
);

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
        "200 mensagens/mes",
        "Chat com pesquisa na web",
        "Respostas com contexto",
        "WhatsApp IA: 0 numeros",
        "Exportacao PDF simples",
        "Sem cartao de credito",
      ],
      highlighted: false,
    },
    {
      key: "basic",
      name: t('planBasicTitle', locale),
      tag: t('planBasicTag', locale),
      price: "R$ 39,00",
      priceLabel: t('perMonth', locale),
      priceStudent: "R$ 19,50",
      studentLabel: t('perStudentMonth', locale),
      description: t('planBasicDescription', locale),
      features: [
        "500 mensagens/mes",
        "Upload de PDF, Word, Excel",
        "Respostas detalhadas",
        "WhatsApp IA: 1 numero",
        "PDF e Word profissionais",
        "Excel com graficos",
      ],
      highlighted: false,
    },
    {
      key: "medium",
      name: t('planMediumTitle', locale),
      tag: t('planMediumTag', locale),
      price: "R$ 99,00",
      priceLabel: t('perMonth', locale),
      priceStudent: "R$ 49,50",
      studentLabel: t('perStudentMonth', locale),
      description: t('planMediumDescription', locale),
      features: [
        "Mensagens ilimitadas",
        "Geracao de imagem/video",
        "Analise de codigo",
        "WhatsApp IA: 3 numeros",
        "Document Engine completo",
        "Automacoes e chatbot",
      ],
      highlighted: true,
    },
    {
      key: "master",
      name: t('planMasterTitle', locale),
      tag: t('planMasterTag', locale),
      price: "R$ 199,00",
      priceLabel: t('perMonth', locale),
      priceStudent: "R$ 99,50",
      studentLabel: t('perStudentMonth', locale),
      description: t('planMasterDescription', locale),
      features: [
        "Tudo ilimitado",
        "WhatsApp IA: ilimitado",
        "Agentes autonomos",
        "White-label",
        "Multiplos usuarios",
        "API empresarial",
      ],
      highlighted: false,
    },
  ];
}

export default function PlanosPage() {
  const { locale } = useLanguage();
  const plans = getPlanData(locale);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    
    const params = new URLSearchParams(window.location.search);
    const blocked = params.get("blocked") === "1";
    const success = params.get("success") === "1";
    
    const token = window.localStorage.getItem("syntexa_token");
    if (!token) {
      setLoading(false);
      return;
    }
    
    // Busca status da subscription no backend
    getSubscriptionStatus(token).then((data) => {
      setSubscription(data);
      setLoading(false);
      
      // Se veio com blocked=1, marcar como expirado
      if (blocked || data?.subscription?.is_expired) {
        setIsExpired(true);
      }
      
      // Se pagamento foi sucesso, atualiza localStorage
      if (success && data?.subscription?.plan) {
        window.localStorage.setItem("syntexa_plan", data.subscription.plan);
      }
    }).catch(() => {
      setLoading(false);
    });
  }, []);

  async function handleSubscribe(planKey) {
    if (planKey === "free") {
      if (typeof window === "undefined") return;
      const token = window.localStorage.getItem("syntexa_token");
      window.location.href = token ? "/chat" : "/cadastro";
      return;
    }
    
    try {
      const token = typeof window !== "undefined" ? window.localStorage.getItem("syntexa_token") : null;
      if (!token) {
        window.location.href = "/login?redirect=plans";
        return;
      }
      var url = await createStripeCheckout(planKey, token);
      if (url) window.location.href = url;
    } catch (err) {
      var msg = err instanceof Error ? err.message : String(err);
      alert("Erro no checkout: " + msg);
    }
  }

  const trialDays = subscription?.subscription?.trial_days_left || 0;
  const isTrial = subscription?.subscription?.is_trial || false;
  const currentPlan = subscription?.subscription?.plan || "free";
  const expiresIn = subscription?.subscription?.expires_in_days;

  return React.createElement(
    "div",
    { className: "mx-auto w-full max-w-[1200px] px-4 py-12 sm:px-6" },
    // Header
    React.createElement(
      "div",
      { className: "mb-8 text-center" },
      React.createElement("h1", { className: "text-3xl font-semibold tracking-tight text-zinc-900" }, 
        "Escolha seu Plano"
      ),
      React.createElement(
        "p",
        { className: "mt-3 text-[15px] text-zinc-600" },
        "Comece gratis com 30 dias de trial. Cancele quando quiser."
      )
    ),
    
    // Banner de Trial ou Expirado
    !loading && React.createElement(
      "div",
      { className: "mb-8" },
      isExpired ? 
        React.createElement(
          "div",
          { className: "bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3" },
          React.createElement(AlertIcon),
          React.createElement(
            "div",
            null,
            React.createElement("p", { className: "font-medium text-red-900" }, 
              "Seu trial expirou ou subscription foi suspensa"
            ),
            React.createElement("p", { className: "text-sm text-red-700" }, 
              "Escolha um plano abaixo para continuar usando todas as funcionalidades."
            )
          )
        ) :
        isTrial && trialDays > 0 ?
          React.createElement(
            "div",
            { className: "bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3" },
            React.createElement(TrialIcon),
            React.createElement(
              "div",
              null,
              React.createElement("p", { className: "font-medium text-green-900" }, 
                "Voce esta no periodo de trial"
              ),
              React.createElement("p", { className: "text-sm text-green-700" }, 
                "Faltam " + trialDays + " dias gratis. Aproveite todas as funcionalidades!"
              )
            )
          ) :
          currentPlan !== "free" ?
            React.createElement(
              "div",
              { className: "bg-blue-50 border border-blue-200 rounded-lg p-4" },
              React.createElement("p", { className: "font-medium text-blue-900" }, 
                "Plano atual: " + currentPlan.toUpperCase()
              ),
              expiresIn !== null && React.createElement("p", { className: "text-sm text-blue-700" }, 
                "Renova em " + expiresIn + " dias"
              )
            ) :
            null
    ),
    
    // Grid de Planos
    React.createElement(
      "div",
      { className: "grid gap-5 sm:grid-cols-2 lg:grid-cols-4" },
      plans.map(function (plan) {
        var isCurrent = currentPlan === plan.key;
        return React.createElement(PlanCard, { 
          key: plan.key, 
          plan: plan, 
          onSubscribe: handleSubscribe,
          isCurrent: isCurrent,
          CheckIcon: CheckIcon
        });
      })
    ),
    
    // Info adicional
    React.createElement(
      "div",
      { className: "mt-12 text-center" },
      React.createElement("p", { className: "text-sm text-zinc-500" }, 
        "Pagamento seguro via Stripe. 30 dias de garantia."
      )
    )
  );
}


