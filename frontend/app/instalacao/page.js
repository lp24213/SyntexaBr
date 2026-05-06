"use client";

import React from "react";
import { AppShell } from "../../components/shell";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";

const STEPS = [
  "Receba da equipe Syntexa o link de download e a chave de licença institucional.",
  "Instale o aplicativo no seu sistema (Windows, macOS, Linux, Android ou iOS via PWA).",
  "No primeiro acesso, informe a chave de licença para ativar a instituição.",
  "Teste login, chat e exportação de arquivos para confirmar a operação.",
];

const SUPPORT = [
  "Se a chave não validar, confirme se não há espaços extras ao copiar/colar.",
  "Se o dispositivo estiver sem internet, o sistema pode operar localmente e sincronizar quando conectar.",
  "Para bloqueios de rede institucional, contate o TI local para liberar o domínio oficial da Syntexa.",
];

export default function InstalacaoPublicaPage() {
  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto w-full max-w-4xl px-4 py-8 sm:px-6" },
      React.createElement(
        "section",
        { className: "rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm" },
        React.createElement(
          "h1",
          { className: "inline-flex items-center gap-2 text-2xl font-bold text-zinc-900" },
          React.createElement(FuturisticIcon, { name: "download", className: "h-6 w-6 text-violet-600" }),
          "Instalação da Syntexa"
        ),
        React.createElement(
          "p",
          { className: "mt-2 text-sm text-zinc-600" },
          "Guia rápido para escolas, universidades e órgãos parceiros instalarem o sistema com segurança."
        ),
        React.createElement(
          "ol",
          { className: "mt-5 list-decimal space-y-2 pl-5 text-sm text-zinc-700" },
          STEPS.map(function (step, idx) {
            return React.createElement("li", { key: "step-" + idx }, step);
          })
        ),
        React.createElement(
          "div",
          { className: "mt-5 flex flex-wrap gap-2" },
          React.createElement(
            "a",
            {
              href: "/download",
              className: "inline-flex items-center rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500",
            },
            "Abrir downloads"
          ),
          React.createElement(
            "a",
            {
              href: "/login",
              className: "inline-flex items-center rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50",
            },
            "Acessar plataforma"
          )
        )
      ),
      React.createElement(
        "section",
        { className: "mt-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm" },
        React.createElement(
          "h2",
          { className: "text-base font-semibold text-zinc-900" },
          "Suporte rápido"
        ),
        React.createElement(
          "ul",
          { className: "mt-3 list-disc space-y-2 pl-5 text-sm text-zinc-600" },
          SUPPORT.map(function (item, idx) {
            return React.createElement("li", { key: "sup-" + idx }, item);
          })
        )
      )
    )
  );
}

