"use client";

import React, { useEffect, useState } from "react";

const CONSENT_KEY = "syntexa_cookie_consent_v1";

function notifyConsent(value) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent("syntexa:cookie-consent", {
      detail: { value },
    })
  );
}

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(CONSENT_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        notifyConsent(parsed?.value === "accepted" ? "accepted" : "essential_only");
      }
      setVisible(!saved);
    } catch {
      setVisible(true);
    }
  }, []);

  function saveConsent(value) {
    try {
      window.localStorage.setItem(
        CONSENT_KEY,
        JSON.stringify({ value, at: new Date().toISOString() })
      );
    } catch {}
    notifyConsent(value);
    setVisible(false);
  }

  if (!visible) return null;

  return React.createElement(
    "div",
    {
      className:
        "pointer-events-none fixed inset-x-0 bottom-3 z-[120] flex justify-center px-3",
      role: "dialog",
      "aria-label": "Consentimento de cookies",
    },
    React.createElement(
      "div",
      { className: "pointer-events-auto w-full max-w-3xl rounded-2xl border border-zinc-200 bg-white/95 px-4 py-4 shadow-xl backdrop-blur md:px-6 md:py-5" },
      React.createElement(
        "p",
        { className: "text-xs leading-relaxed text-zinc-700 md:text-sm" },
        "Usamos cookies para autenticação, segurança, métricas de uso e melhoria da experiência. Ao continuar, você concorda com nossa ",
        React.createElement(
          "a",
          { href: "/privacidade", className: "underline hover:text-zinc-900" },
          "Política de Privacidade"
        ),
        " e ",
        React.createElement(
          "a",
          { href: "/cookies", className: "underline hover:text-zinc-900" },
          "Política de Cookies"
        ),
        "."
      ),
      React.createElement(
        "div",
        { className: "mt-3 flex flex-wrap gap-2" },
        React.createElement(
          "button",
          {
            type: "button",
            onClick: function () {
              saveConsent("accepted");
            },
            className:
              "rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-violet-500",
          },
          "Aceitar cookies"
        ),
        React.createElement(
          "button",
          {
            type: "button",
            onClick: function () {
              saveConsent("essential_only");
            },
            className:
              "rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50",
          },
          "Somente essenciais"
        )
      )
    )
  );
}
