"use client";

import React from "react";
import { motion } from "framer-motion";

// ─── Windows SVG Icon (real, not emoji) ──────────────────────────────────────
function WindowsIcon() {
  return React.createElement("svg", {
    viewBox: "0 0 88 88",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    className: "h-7 w-7",
  },
    React.createElement("path", {
      d: "M0 12.5L35.8 7.2V40.8H0V12.5ZM39.8 6.6L88 0V40.6H39.8V6.6ZM0 44.6H35.8V78.2L0 72.9V44.6ZM39.8 44.6H88V85.3L39.8 78.7V44.6Z",
      fill: "currentColor",
    })
  );
}

// ─── Linux SVG Icon (Tux-inspired, real) ─────────────────────────────────────
function LinuxIcon() {
  return React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    className: "h-7 w-7",
  },
    React.createElement("path", {
      d: "M12 2C11 2 10.2 2.8 10.2 3.8C10.2 4.6 10.7 5.3 11.4 5.6C11.2 5.8 11 6.1 11 6.5V7.5C11 7.9 11.3 8.2 11.7 8.2H12.3C12.7 8.2 13 7.9 13 7.5V6.5C13 6.1 12.8 5.8 12.6 5.6C13.3 5.3 13.8 4.6 13.8 3.8C13.8 2.8 13 2 12 2Z",
      fill: "currentColor",
      opacity: "0.9",
    }),
    React.createElement("ellipse", {
      cx: "12", cy: "14.5", rx: "5.5", ry: "6.5",
      fill: "currentColor",
      opacity: "0.85",
    }),
    React.createElement("path", {
      d: "M7 16C6 16 5 17 5 18.5C5 20 6.5 21 8 21C9.5 21 10 20 10 19",
      stroke: "currentColor",
      strokeWidth: "1.2",
      strokeLinecap: "round",
      opacity: "0.7",
    }),
    React.createElement("path", {
      d: "M17 16C18 16 19 17 19 18.5C19 20 17.5 21 16 21C14.5 21 14 20 14 19",
      stroke: "currentColor",
      strokeWidth: "1.2",
      strokeLinecap: "round",
      opacity: "0.7",
    }),
    React.createElement("ellipse", {
      cx: "12", cy: "12.5", rx: "2", ry: "1.2",
      fill: "currentColor",
      opacity: "0.3",
    })
  );
}

// ─── Download Card ─────────────────────────────────────────────────────────────
function DownloadCard({ href, icon, label, sub, delay }) {
  return React.createElement(
    motion.a,
    {
      href: href,
      className: "group relative flex flex-col items-center gap-4 rounded-2xl border border-[rgba(20,24,30,0.06)] bg-[#fafbfc] p-6 transition-all duration-300 hover:border-[rgba(20,24,30,0.12)] hover:bg-white hover:shadow-[0_4px_20px_rgba(15,20,30,0.04)]",
      initial: { opacity: 0, y: 14 },
      whileInView: { opacity: 1, y: 0 },
      viewport: { once: true },
      transition: { duration: 0.45, delay: delay, ease: [0.22, 1, 0.36, 1] },
    },
    // Icon container
    React.createElement("div", {
      className: "flex h-14 w-14 items-center justify-center rounded-xl border border-[rgba(20,24,30,0.06)] bg-white text-[#5a5c5e] transition-transform duration-300 group-hover:scale-[1.05] group-hover:text-[#1a1c1e]",
    }, icon),
    // Text
    React.createElement("div", { className: "text-center" },
      React.createElement("p", { className: "text-sm font-medium text-[#1a1c1e]" }, label),
      React.createElement("p", { className: "mt-0.5 text-[11px] text-[#8e9094]" }, sub)
    ),
    // Arrow
    React.createElement("div", {
      className: "mt-1 text-[#8e9094] transition-all duration-300 group-hover:translate-x-0.5 group-hover:text-[#1a1c1e]",
    }, "→")
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
        t("homeDownloadsTitle", locale)
      ),
      React.createElement("p", { className: "mt-2 max-w-xl text-[15px] leading-relaxed text-[#5a5c5e]" },
        t("homeDownloadsLead", locale)
      )
    ),

    React.createElement("div", { className: "grid gap-4 sm:grid-cols-2" },
      React.createElement(DownloadCard, {
        href: "/download/SyntexaAI-Setup-1.0.0.exe",
        icon: React.createElement(WindowsIcon, null),
        label: t("homeWinBuild", locale),
        sub: t("homeWinSub", locale) || "Windows 10/11 · 64-bit",
        delay: 0.1,
      }),
      React.createElement(DownloadCard, {
        href: "/download/SyntexaAI-linux-x64.tar.gz",
        icon: React.createElement(LinuxIcon, null),
        label: t("homeLinuxBuild", locale),
        sub: t("homeLinuxSub", locale) || "Linux · x64 · tar.gz",
        delay: 0.2,
      })
    )
  );
}
