"use client";

import React, { useEffect } from "react";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { encryptedPath } from "../../lib/routes";

export default function ConfigPage() {
  useEffect(() => {
    try {
      const token = window.localStorage.getItem("syntexa_token");
      if (!token) {
        window.location.href = encryptedPath("login");
      }
    } catch {
      window.location.href = encryptedPath("login");
    }
  }, []);

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto flex max-w-3xl flex-col py-10" },
      React.createElement(
        Card,
        {
          title: "Configurações da conta",
          description:
            "Em breve: preferências da Syntexa, idioma padrão, limites de sessão e integrações.",
        },
        React.createElement(
          "p",
          { className: "text-sm text-white/70" },
          "Por enquanto, use o painel de planos e o login normal. Esta área será o centro de controle da sua conta."
        )
      )
    )
  );
}

