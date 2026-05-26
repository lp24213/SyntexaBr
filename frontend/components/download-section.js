"use client";

import React from "react";
import { motion } from "framer-motion";

const RAILWAY_DOWNLOAD_BASE = "https://syntexa-backend-production.up.railway.app/v1/desktop/binary";

function IconWindows() {
  return React.createElement("svg", { viewBox: "0 0 88 88", fill: "none", className: "h-7 w-7", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M0 12.5L35.8 7.2V40.8H0V12.5ZM39.8 6.6L88 0V40.6H39.8V6.6ZM0 44.6H35.8V78.2L0 72.9V44.6ZM39.8 44.6H88V85.3L39.8 78.7V44.6Z", fill: "currentColor" })
  );
}

function IconLinux() {
  return React.createElement("svg", { viewBox: "0 0 24 24", fill: "none", className: "h-7 w-7", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M12 2c-1.7 0-3 1.3-3 3 0 .6.2 1.2.5 1.6C8.8 7 8 7.6 7.4 8.5c-.9 1.2-1 2.9-.5 4.3.3.9.8 1.7 1.4 2.2-.3.5-.5 1-.5 1.6 0 .5.2 1 .5 1.4-.3.4-.5.9-.5 1.4 0 1.1.9 2 2 2h5c1.1 0 2-.9 2-2 0-.5-.2-1-.5-1.4.3-.4.5-.9.5-1.4 0-.6-.2-1.1-.5-1.6.6-.5 1.1-1.3 1.4-2.2.5-1.4.4-3.1-.5-4.3C16 7.6 15.2 7 14.5 6.6c.3-.4.5-1 .5-1.6 0-1.7-1.3-3-3-3z", fill: "currentColor", opacity: "0.9" }),
    React.createElement("path", { d: "M8.5 17.5c-1 0-2 .8-2 2s.9 1.5 2 1.5M15.5 17.5c1 0 2 .8 2 2s-.9 1.5-2 1.5", stroke: "currentColor", strokeWidth: "1.2", strokeLinecap: "round", opacity: "0.7" })
  );
}

function IconWeb() {
  return React.createElement("svg", { viewBox: "0 0 24 24", fill: "none", className: "h-7 w-7", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("circle", { cx: "12", cy: "12", r: "9", stroke: "currentColor", strokeWidth: "1.8" }),
    React.createElement("path", { d: "M12 3c-2.5 3-4 5.5-4 9s1.5 6 4 9M12 3c2.5 3 4 5.5 4 9s-1.5 6-4 9M3 12h18", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function DownloadCard({ icon, label, sub, delay, href, filename }) {
  return React.createElement(
    motion.a,
    {
      href: href,
      download: filename,
      className: "group relative flex flex-col items-center gap-4 rounded-2xl border border-[rgba(20,24,30,0.06)] bg-[#fafbfc] p-6 transition-all duration-300 hover:border-[rgba(20,24,30,0.12)] hover:bg-white hover:shadow-[0_4px_20px_rgba(15,20,30,0.04)] cursor-pointer w-full text-left no-underline",
      initial: { opacity: 0, y: 14 },
      whileInView: { opacity: 1, y: 0 },
      viewport: { once: true },
      transition: { duration: 0.45, delay: delay, ease: [0.22, 1, 0.36, 1] },
    },
    React.createElement("div", { className: "flex h-14 w-14 items-center justify-center rounded-xl border border-[rgba(20,24,30,0.06)] bg-white text-[#5a5c5e] transition-transform duration-300 group-hover:scale-[1.05] group-hover:text-[#1a1c1e]" },
      icon
    ),
    React.createElement("div", { className: "text-center" },
      React.createElement("p", { className: "text-sm font-medium text-[#1a1c1e]" }, label),
      React.createElement("p", { className: "mt-0.5 text-[11px] text-[#8e9094]" }, sub)
    ),
    React.createElement("div", { className: "mt-1 text-[#8e9094] transition-all duration-300 group-hover:translate-y-0.5 group-hover:text-[#1a1c1e]" }, "↓")
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
        "Baixar Aplicativo"
      ),
      React.createElement("p", { className: "mt-2 max-w-xl text-[15px] leading-relaxed text-[#5a5c5e]" },
        "Download direto do instalador. Sem loja, sem GitHub, sem zip."
      )
    ),

    React.createElement("div", { className: "grid gap-4 sm:grid-cols-3" },
      React.createElement(DownloadCard, {
        icon: React.createElement(IconWindows, null),
        label: "Windows",
        sub: "Instalador .msi · 64-bit",
        delay: 0.1,
        href: RAILWAY_DOWNLOAD_BASE + "/SyntexaAI-Setup-45.0.0.msi",
        filename: "SyntexaAI-Setup-45.0.0.msi",
      }),
      React.createElement(DownloadCard, {
        icon: React.createElement(IconLinux, null),
        label: "Linux",
        sub: "Aplicativo .AppImage · x64",
        delay: 0.2,
        href: RAILWAY_DOWNLOAD_BASE + "/SyntexaAI-linux-x64-45.0.0.AppImage",
        filename: "SyntexaAI-linux-x64-45.0.0.AppImage",
      }),
      React.createElement(DownloadCard, {
        icon: React.createElement(IconWeb, null),
        label: "Abrir no browser",
        sub: "Acesso imediato · sem instalar",
        delay: 0.3,
        href: "/chat",
        filename: null,
      })
    ),

    React.createElement("p", { className: "mt-5 text-[11px] text-[#8e9094] text-center" },
      "Windows · Linux · Web"
    )
  );
}
