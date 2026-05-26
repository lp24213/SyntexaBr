"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

function IconInstall() {
  return React.createElement("svg", { viewBox: "0 0 24 24", fill: "none", className: "h-7 w-7", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M12 3v13M7 11l5 5 5-5", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M3 19h18", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round" })
  );
}

function IconWeb() {
  return React.createElement("svg", { viewBox: "0 0 24 24", fill: "none", className: "h-7 w-7", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("circle", { cx: "12", cy: "12", r: "9", stroke: "currentColor", strokeWidth: "1.8" }),
    React.createElement("path", { d: "M12 3c-2.5 3-4 5.5-4 9s1.5 6 4 9M12 3c2.5 3 4 5.5 4 9s-1.5 6-4 9M3 12h18", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function PwaCard({ delay }) {
  const [pwaReady, setPwaReady] = useState(false);
  const [installed, setInstalled] = useState(false);

  useEffect(function () {
    if (typeof window === "undefined") return;
    if (window.__syntexaPwaPrompt) setPwaReady(true);
    function onReady() { setPwaReady(true); }
    function onInstalled() { setInstalled(true); setPwaReady(false); }
    document.addEventListener("syntexa:pwa-ready", onReady);
    document.addEventListener("syntexa:pwa-installed", onInstalled);
    return function () {
      document.removeEventListener("syntexa:pwa-ready", onReady);
      document.removeEventListener("syntexa:pwa-installed", onInstalled);
    };
  }, []);

  var label = installed ? "App instalado!" : pwaReady ? "Instalar app" : "Instalar app";
  var sub = installed
    ? "Atalho criado no desktop e menu Iniciar"
    : "Windows, Mac ou Linux — atalho no desktop, sem loja";

  return React.createElement(
    motion.button,
    {
      type: "button",
      disabled: installed,
      onClick: function () {
        if (typeof window !== "undefined" && window.__syntexaInstallPwa) {
          window.__syntexaInstallPwa();
        } else {
          alert("Para instalar: no Chrome/Edge, clique no ícone de instalar na barra de endereço (lado direito da URL).");
        }
      },
      className: "group relative flex flex-col items-center gap-4 rounded-2xl border border-[rgba(20,24,30,0.06)] bg-[#fafbfc] p-6 transition-all duration-300 hover:border-[rgba(20,24,30,0.12)] hover:bg-white hover:shadow-[0_4px_20px_rgba(15,20,30,0.04)] cursor-pointer w-full text-left disabled:opacity-60",
      initial: { opacity: 0, y: 14 },
      whileInView: { opacity: 1, y: 0 },
      viewport: { once: true },
      transition: { duration: 0.45, delay: delay, ease: [0.22, 1, 0.36, 1] },
    },
    React.createElement("div", { className: "flex h-14 w-14 items-center justify-center rounded-xl border border-[rgba(20,24,30,0.06)] bg-white text-[#5a5c5e] transition-transform duration-300 group-hover:scale-[1.05] group-hover:text-[#1a1c1e]" },
      React.createElement(IconInstall, null)
    ),
    React.createElement("div", { className: "text-center" },
      React.createElement("p", { className: "text-sm font-medium text-[#1a1c1e]" }, label),
      React.createElement("p", { className: "mt-0.5 text-[11px] text-[#8e9094]" }, sub)
    ),
    !installed && React.createElement("div", { className: "mt-1 text-[#8e9094] transition-all duration-300 group-hover:translate-x-0.5 group-hover:text-[#1a1c1e]" }, "→")
  );
}

// ─── Download Section ────────────────────────────────────────────────────────
export function DownloadSection({ locale, t }) {
  return React.createElement(
    "section",
    { id: "downloads", className: "relative mt-8 scroll-mt-24 overflow-hidden rounded-[20px] border border-[rgba(20,24,30,0.06)] bg-white p-7 md:p-10" },

    React.createElement(
      motion.div,
      {
        className: "mb-6",
        initial: { opacity: 0, y: 10 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true },
        transition: { duration: 0.45 },
      },
      React.createElement("h2", { className: "text-[1.5rem] font-semibold tracking-tight text-[#1a1c1e] md:text-[1.75rem]" },
        "Instale a Syntexa"
      ),
      React.createElement("p", { className: "mt-2 max-w-xl text-[15px] leading-relaxed text-[#5a5c5e]" },
        "App completo — funciona como qualquer aplicativo instalado, com atalho no desktop, menu Iniciar e acesso directo ao chat."
      )
    ),

    React.createElement("div", { className: "grid gap-4 sm:grid-cols-2" },
      React.createElement(PwaCard, { delay: 0.1 }),
      React.createElement(
        motion.a,
        {
          href: "/chat",
          className: "group relative flex flex-col items-center gap-4 rounded-2xl border border-[rgba(20,24,30,0.06)] bg-[#fafbfc] p-6 transition-all duration-300 hover:border-[rgba(20,24,30,0.12)] hover:bg-white hover:shadow-[0_4px_20px_rgba(15,20,30,0.04)]",
          initial: { opacity: 0, y: 14 },
          whileInView: { opacity: 1, y: 0 },
          viewport: { once: true },
          transition: { duration: 0.45, delay: 0.2, ease: [0.22, 1, 0.36, 1] },
        },
        React.createElement("div", { className: "flex h-14 w-14 items-center justify-center rounded-xl border border-[rgba(20,24,30,0.06)] bg-white text-[#5a5c5e] transition-transform duration-300 group-hover:scale-[1.05] group-hover:text-[#1a1c1e]" },
          React.createElement(IconWeb, null)
        ),
        React.createElement("div", { className: "text-center" },
          React.createElement("p", { className: "text-sm font-medium text-[#1a1c1e]" }, "Abrir no browser"),
          React.createElement("p", { className: "mt-0.5 text-[11px] text-[#8e9094]" }, "Acesso imediato — sem instalar nada")
        ),
        React.createElement("div", { className: "mt-1 text-[#8e9094] transition-all duration-300 group-hover:translate-x-0.5 group-hover:text-[#1a1c1e]" }, "→")
      )
    ),

    React.createElement("p", { className: "mt-5 text-[11px] text-[#8e9094] text-center" },
      "Windows · macOS · Linux · Android · iOS — o mesmo app, instalado como PWA pelo Chrome ou Edge"
    )
  );
}
