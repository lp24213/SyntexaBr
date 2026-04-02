"use client";

import React from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";

const WIN_URL = "https://syntexabr.com.br/download/SyntexaAI-Setup-1.0.0.exe";
const MAC_URL = "";

var btnBase =
  "inline-flex items-center justify-center rounded-full text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30 focus-visible:ring-offset-2 focus-visible:ring-offset-black w-full justify-center px-4 py-2";

export default function DownloadPage() {
  const hasWin = !!WIN_URL;
  const hasMac = !!MAC_URL;

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "flex min-h-[calc(100vh-6rem)] items-center justify-center py-10" },
      React.createElement(
        motion.div,
        {
          className: "w-full max-w-2xl",
          initial: { opacity: 0, y: 20 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.35, ease: "easeOut" },
        },
        React.createElement(
          Card,
          {
            title: "Baixar app desktop Syntexa",
            description:
              "Use a Syntexa em uma janela dedicada, com melhor foco, atalhos de teclado e integra\xE7\xE3o nativa ao sistema operacional.",
          },
          React.createElement(
            "div",
            { className: "space-y-6" },
            React.createElement(
              "div",
              { className: "grid gap-4 sm:grid-cols-3" },
              React.createElement(
                "div",
                { className: "rounded-2xl border border-white/10 bg-black/40 p-4" },
                React.createElement(
                  "p",
                  { className: "mb-1 text-sm font-semibold text-white" },
                  "Windows"
                ),
                React.createElement(
                  "p",
                  { className: "mb-3 text-xs text-white/60" },
                  "Compat\xEDvel com Windows 10 ou superior."
                ),
                hasWin
                  ? React.createElement(
                      "a",
                      {
                        href: WIN_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " bg-white hover:bg-zinc-200 text-black",
                      },
                      "Baixar para Windows (.exe)"
                    )
                  : React.createElement(
                      Button,
                      { className: "w-full justify-center", disabled: true },
                      "Download em breve"
                    )
              ),
              React.createElement(
                "div",
                { className: "rounded-2xl border border-white/10 bg-black/40 p-4" },
                React.createElement(
                  "p",
                  { className: "mb-1 text-sm font-semibold text-white" },
                  "macOS"
                ),
                React.createElement(
                  "p",
                  { className: "mb-3 text-xs text-white/60" },
                  "Compat\xEDvel com macOS 12+ (Apple Silicon ou Intel)."
                ),
                hasMac
                  ? React.createElement(
                      "a",
                      {
                        href: MAC_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " border border-white/20 bg-transparent hover:bg-white/5 text-white",
                      },
                      "Baixar para macOS (.dmg)"
                    )
                  : React.createElement(
                      Button,
                      { variant: "outline", className: "w-full justify-center", disabled: true },
                      "Vers\xE3o macOS em breve"
                    )
              ),
              React.createElement(
                "div",
                { className: "rounded-2xl border border-white/10 bg-black/40 p-4" },
                React.createElement(
                  "p",
                  { className: "mb-1 text-sm font-semibold text-white" },
                  "Linux / Ubuntu"
                ),
                React.createElement(
                  "p",
                  { className: "mb-3 text-xs text-white/60" },
                  "Compat\xEDvel com distribui\xE7\xF5es baseadas em Ubuntu 22.04+."
                ),
                React.createElement(
                  Button,
                  { variant: "outline", className: "w-full justify-center", disabled: true },
                  "Vers\xE3o Linux em breve"
                )
              )
            )
          )
        )
      )
    )
  );
}

