"use client";

import React, { useEffect } from "react";
import { AppShell } from "../../components/shell";
import { createStripeCheckout, getProfile } from "../../lib/api";
import { BusinessPlanPage } from "../../components/business-plan-page";

var plans = [
  {
    key: "basic",
    name: "Básico",
    tag: "Para começar",
    price: "R$ 39",
    priceLabel: "/mês",
    priceStudent: "R$ 19,50",
    studentLabel: "estudante/mês",
    description: "Para quem quer estudar IA, testar ideias e ter um copiloto pessoal.",
    features: [
      "Até 500 mensagens/mês",
      "Chat com texto, imagem e áudio",
      "Modelos otimizados para estudo e pesquisa",
      "Suporte por e-mail em horário comercial",
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
    description: "Para uso diário em estudo, trabalho e projetos de produto.",
    features: [
      "Mensagens ilimitadas (uso justo)",
      "Contexto estendido para projetos longos",
      "Ferramentas de código, dados e documentos",
      "Upload de imagem, vídeo e áudio com análise multimodal",
    ],
    highlighted: true,
  },
  {
    key: "master",
    name: "Master",
    tag: "Institucional",
    price: "R$ 199",
    priceLabel: "/mês",
    priceStudent: "R$ 99,50",
    studentLabel: "estudante/mês",
    description: "Infraestrutura de IA modular para escolas, universidades e equipes.",
    features: [
      "Tudo do plano Médio",
      "Agentes avançados e automações guiadas",
      "Integração institucional (SSO, auditoria, múltiplos usuários)",
      "Suporte dedicado e condições especiais para turmas",
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
    React.createElement(BusinessPlanPage, { plans: plans, onSubscribe: handleSubscribe })
  );
}

