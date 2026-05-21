"use client";

import React from "react";
import { AppShell } from "../../components/shell";

export default function PrivacidadePage() {
  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "main",
      { className: "py-10 text-zinc-800" },
    React.createElement("h1", { className: "text-2xl font-bold text-zinc-900" }, "Política de Privacidade"),
    React.createElement(
      "p",
      { className: "mt-4 text-sm leading-relaxed" },
      "Tratamos dados pessoais conforme a LGPD, com finalidade de autenticação, segurança, prestação do serviço e melhoria contínua da plataforma."
    ),
    React.createElement(
      "p",
      { className: "mt-3 text-sm leading-relaxed" },
      "Você pode solicitar atualização ou exclusão de dados nos canais oficiais de suporte, observadas obrigações legais de retenção."
    )
  )
  );
}
