"use client";

import React, { useEffect, useState } from "react";
import { t } from "../lib/i18n";
import { useLanguage } from "./language-provider";

export function PwaInstallButton({ className }) {
  const { locale } = useLanguage();
  const [ready, setReady] = useState(false);
  const [installed, setInstalled] = useState(false);

  useEffect(function () {
    if (typeof window === "undefined") return;

    if (window.__syntexaPwaPrompt) setReady(true);

    function onReady() { setReady(true); }
    function onInstalled() { setReady(false); setInstalled(true); }

    document.addEventListener("syntexa:pwa-ready", onReady);
    document.addEventListener("syntexa:pwa-installed", onInstalled);
    return function () {
      document.removeEventListener("syntexa:pwa-ready", onReady);
      document.removeEventListener("syntexa:pwa-installed", onInstalled);
    };
  }, []);

  if (installed || !ready) return null;

  return React.createElement(
    "button",
    {
      type: "button",
      className: className || "inline-flex items-center gap-2 rounded-full border border-[#e2e8f0] bg-white px-4 py-2 text-xs font-medium text-[#0f172a] shadow-sm hover:bg-[#f8fafc] transition-colors",
      onClick: function () {
        if (typeof window !== "undefined" && window.__syntexaInstallPwa) {
          window.__syntexaInstallPwa();
        }
      },
    },
    React.createElement(
      "svg",
      { viewBox: "0 0 24 24", fill: "none", className: "h-3.5 w-3.5 shrink-0", "aria-hidden": "true" },
      React.createElement("path", {
        d: "M12 3v13M7 11l5 5 5-5M3 19h18",
        stroke: "currentColor",
        strokeWidth: "1.8",
        strokeLinecap: "round",
        strokeLinejoin: "round",
      })
    ),
    t("installApp", locale)
  );
}
