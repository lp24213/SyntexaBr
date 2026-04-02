"use client";

import React, { useEffect } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { createStripeCheckout, getProfile } from "../../lib/api";

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

export default function PlansPage() {
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
      if (url) {
        window.location.href = url;
      }
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
      { className: "mx-auto flex max-w-5xl flex-col items-center py-10" },
      React.createElement(
        motion.div,
        {
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.35 },
          className: "mb-10 text-center",
        },
        React.createElement(
          "p",
          {
            className:
              "mb-2 inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-300",
          },
          "Planos Syntexa com desconto estudantil"
        ),
        React.createElement(
          "h1",
          { className: "mt-3 text-2xl font-semibold tracking-tight text-white sm:text-3xl" },
          "Da ideia ao produto rodando em produ\xE7\xE3o"
        ),
        React.createElement(
          "p",
          { className: "mt-3 max-w-xl text-sm text-white/65" },
          "Planos pensados para estudantes, criadores e institui\xE7\xF5es que precisam de uma camada de intelig\xEAncia escal\xE1vel, com at\xE9 50% de desconto para estudantes verificados."
        )
      ),
      React.createElement(
        "div",
        { className: "grid w-full gap-5 md:grid-cols-3" },
        plans.map(function (plan, idx) {
          var cardClass =
            "h-full border relative " +
            (plan.highlighted ? "border-emerald-300/60 bg-gradient-to-b from-emerald-400/10 via-white/5 to-black" : "border-white/10 bg-[#111]");
          return React.createElement(
            motion.div,
            {
              key: plan.name,
              initial: { opacity: 0, y: 12 },
              animate: { opacity: 1, y: 0 },
              transition: { duration: 0.22, delay: idx * 0.05 },
            },
            React.createElement(
              Card,
              {
                className: cardClass,
                title: plan.name === "Médio" ? "Médio \u2014 recomendado" : plan.name,
                description: plan.description,
              },
              plan.tag &&
                React.createElement(
                  "span",
                  {
                    className:
                      "mb-3 inline-flex items-center gap-1 rounded-full border border-white/15 bg-black/40 px-2.5 py-1 text-[11px] font-medium text-white/70",
                  },
                  React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-emerald-400" }),
                  plan.tag
                ),
              React.createElement(
                "div",
                { className: "mb-1 text-2xl font-semibold text-white" },
                plan.price,
                React.createElement(
                  "span",
                  { className: "text-base font-normal text-white/70" },
                  " ",
                  plan.priceLabel
                )
              ),
              React.createElement(
                "div",
                { className: "mb-3 text-xs text-emerald-300" },
                "Estudantes com 50% OFF: ",
                React.createElement("span", { className: "font-semibold" }, plan.priceStudent),
                " ",
                plan.studentLabel
              ),
              React.createElement(
                "ul",
                { className: "mb-5 space-y-2 text-xs text-white/80" },
                plan.features.map(function (f) {
                  return React.createElement(
                    "li",
                    { key: f, className: "flex items-start gap-2" },
                    React.createElement("span", {
                      className: "mt-[3px] h-1.5 w-1.5 shrink-0 rounded-full bg-gradient-to-r from-emerald-300 to-cyan-300",
                    }),
                    React.createElement("span", null, f)
                  );
                })
              ),
              React.createElement(
                Button,
                {
                  variant: plan.highlighted ? "primary" : "outline",
                  className: "w-full justify-center",
                  onClick: function () { handleSubscribe(plan.key || "basic"); },
                },
                "Assinar plano"
              )
            )
          );
        })
      )
    )
  );
}
