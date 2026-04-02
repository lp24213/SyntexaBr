"use client";

import React, { useEffect } from "react";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { encryptedPath } from "../../lib/routes";

export default function PerfilPage() {
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
          title: "Perfil do usuário",
          description:
            "Área reservada para informações da sua conta Syntexa e personalização futura.",
        },
        React.createElement(
          "p",
          { className: "text-sm text-white/70" },
          "Em breve: avatar, dados básicos, preferências pessoais e histórico resumido de uso."
        )
      )
    )
  );
}
