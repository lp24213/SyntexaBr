"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";

/** Pacotes na VM: GET /v1/desktop/binary/<ficheiro> (deploy-back com static/desktop). */
function desktopAssetUrl(filename) {
  if (typeof process !== "undefined") {
    var cdn = process.env.NEXT_PUBLIC_DESKTOP_CDN_BASE;
    if (cdn && String(cdn).trim()) {
      return String(cdn).replace(/\/$/, "") + "/v1/desktop/binary/" + encodeURIComponent(filename);
    }
  }
  // Preferir download same-origin: o site redireciona para a API.
  return "/download/" + encodeURIComponent(filename);
}

const WIN_URL =
  (typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_DESKTOP_WIN_URL &&
    String(process.env.NEXT_PUBLIC_DESKTOP_WIN_URL).trim()) ||
  desktopAssetUrl("SyntexaAI-Setup-1.0.0.exe");
const SHOW_MAC_DESKTOP =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_SHOW_MAC_DESKTOP === "1";
const MAC_URL = SHOW_MAC_DESKTOP
  ? (typeof process !== "undefined" &&
      process.env.NEXT_PUBLIC_DESKTOP_MAC_URL &&
      String(process.env.NEXT_PUBLIC_DESKTOP_MAC_URL).trim()) ||
    desktopAssetUrl("SyntexaAI-macos-universal.dmg")
  : "";
const LINUX_URL =
  (typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_DESKTOP_LINUX_URL &&
    String(process.env.NEXT_PUBLIC_DESKTOP_LINUX_URL).trim()) ||
  desktopAssetUrl("SyntexaAI-linux-x64.tar.gz");
const IOS_APP_STORE_URL = process.env.NEXT_PUBLIC_IOS_APPSTORE_URL || "";
const IOS_TESTFLIGHT_URL = process.env.NEXT_PUBLIC_IOS_TESTFLIGHT_URL || "";
const ANDROID_APK_URL =
  (typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_ANDROID_APK_URL &&
    String(process.env.NEXT_PUBLIC_ANDROID_APK_URL).trim()) ||
  "";
const ANDROID_AAB_URL = process.env.NEXT_PUBLIC_ANDROID_AAB_URL || "";
const IOS_DIRECT_IPA_URL = process.env.NEXT_PUBLIC_IOS_DIRECT_IPA_URL || "";
const IOS_DIRECT_MANIFEST_URL = process.env.NEXT_PUBLIC_IOS_DIRECT_MANIFEST_URL || "";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://syntexabr.com.br";
const CHROME_DOWNLOAD_HELP =
  "https://support.google.com/chrome/answer/6261569?hl=pt-BR&co=GENIE.Platform%3DDesktop";

var btnBase =
  "inline-flex items-center justify-center rounded-full text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30 focus-visible:ring-offset-2 focus-visible:ring-offset-black w-full justify-center px-4 py-2";

export default function DownloadPage() {
  const [emBreve, setEmBreve] = useState(false);
  useEffect(function () {
    if (typeof window === "undefined") return;
    try {
      var u = new URL(window.location.href);
      if (u.searchParams.get("em_breve") === "1") setEmBreve(true);
    } catch (_) {}
  }, []);

  const hasWin = !!WIN_URL;
  const hasMac = !!MAC_URL;
  const hasLinux = !!LINUX_URL;
  const hasIosStore = !!IOS_APP_STORE_URL;
  const hasIosTestFlight = !!IOS_TESTFLIGHT_URL;
  const hasAndroidApk = !!ANDROID_APK_URL;
  const hasAndroidAab = !!ANDROID_AAB_URL;
  const hasIosDirectIpa = !!IOS_DIRECT_IPA_URL;
  const hasIosDirectManifest = !!IOS_DIRECT_MANIFEST_URL;

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
            emBreve
              ? React.createElement(
                  "div",
                  {
                    className:
                      "rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950",
                  },
                  "O instalador ainda não está publicado neste servidor. Use a versão web (PWA) abaixo ou volte mais tarde — ou peça o link direto à equipe."
                )
              : null,
            hasWin
              ? React.createElement(
                  "div",
                  {
                    className:
                      "rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-xs text-sky-950",
                  },
                  React.createElement(
                    "p",
                    { className: "font-semibold text-sky-950" },
                    "O Chrome diz que o ficheiro é «pouco habitual» ou «suspeito»?"
                  ),
                  React.createElement(
                    "p",
                    { className: "mt-2 leading-relaxed text-sky-900/95" },
                    "Isso é um aviso automático do navegador para executáveis com pouca reputação na Internet, não um diagnóstico de vírus. O pacote Windows é publicado por nós e inclui assinatura digital (editor «Syntexabr»). Para o aviso desaparecer de forma consistente é preciso certificado de código emitido por uma autoridade pública reconhecida (serviço pago) e tempo de uso."
                  ),
                  React.createElement(
                    "p",
                    { className: "mt-2 leading-relaxed text-sky-900/95" },
                    "Se descarregou deste site oficial, pode confirmar em «Manter» / «Transferir ficheiro suspeito» ou ajustar as definições de transferência do Chrome."
                  ),
                  React.createElement(
                    "a",
                    {
                      href: CHROME_DOWNLOAD_HELP,
                      target: "_blank",
                      rel: "noreferrer",
                      className:
                        "mt-2 inline-block text-xs font-medium text-sky-800 underline underline-offset-2 hover:text-sky-950",
                    },
                    "Artigo de ajuda do Google (Chrome)"
                  )
                )
              : null,
            React.createElement(
              "div",
              { className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" },
              React.createElement(
                "div",
                { className: "rounded-2xl border border-zinc-200 bg-zinc-100 p-4" },
                React.createElement(
                  "p",
                  { className: "mb-1 text-sm font-semibold text-zinc-900" },
                  "Windows"
                ),
                React.createElement(
                  "p",
                  { className: "mb-3 text-xs text-zinc-500" },
                  "Compat\xEDvel com Windows 10 ou superior."
                ),
                hasWin
                  ? React.createElement(
                      React.Fragment,
                      null,
                      React.createElement(
                        "a",
                        {
                          href: WIN_URL,
                          target: "_blank",
                          rel: "noreferrer",
                          className: btnBase + " bg-white hover:bg-zinc-200 text-black",
                        },
                        "Baixar para Windows (.exe)"
                      ),
                      React.createElement(
                        "p",
                        {
                          className: "mt-2 text-[11px] leading-snug text-zinc-600",
                        },
                        "Executável portátil: na primeira vez que abrir o app, criamos automaticamente o atalho «Syntexa AI» na sua área de trabalho."
                      )
                    )
                  : React.createElement(
                      Button,
                      { className: "w-full justify-center", disabled: true },
                      "Download em breve"
                    )
              ),
              React.createElement(
                "div",
                { className: "rounded-2xl border border-zinc-200 bg-zinc-100 p-4" },
                React.createElement(
                  "p",
                  { className: "mb-1 text-sm font-semibold text-zinc-900" },
                  "macOS"
                ),
                React.createElement(
                  "p",
                  { className: "mb-3 text-xs text-zinc-500" },
                  "Compat\xEDvel com macOS 12+ (Apple Silicon ou Intel)."
                ),
                hasMac
                  ? React.createElement(
                      "a",
                      {
                        href: MAC_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
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
                { className: "rounded-2xl border border-zinc-200 bg-zinc-100 p-4" },
                React.createElement(
                  "p",
                  { className: "mb-1 text-sm font-semibold text-zinc-900" },
                  "Linux / Ubuntu"
                ),
                React.createElement(
                  "p",
                  { className: "mb-3 text-xs text-zinc-500" },
                  "Pacote .tar.gz oficial (extraia e execute). Serve para Ubuntu, Fedora e outras distros x64."
                ),
                hasLinux
                  ? React.createElement(
                      "a",
                      {
                        href: LINUX_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                      },
                      "Baixar Linux (.tar.gz)"
                    )
                  : React.createElement(
                      Button,
                      { variant: "outline", className: "w-full justify-center", disabled: true },
                      "Linux em breve"
                    )
              )
            ),
            React.createElement(
              "div",
              { className: "rounded-2xl border border-zinc-200 bg-zinc-100 p-4" },
              React.createElement(
                "p",
                { className: "mb-1 text-sm font-semibold text-zinc-900" },
                "Android"
              ),
              React.createElement(
                "p",
                { className: "mb-3 text-xs text-zinc-500" },
                "Distribuição direta para empresas/escolas sem Play Store (APK) e opção de app web instalável."
              ),
              React.createElement(
                "div",
                { className: "space-y-2" },
                hasAndroidApk
                  ? React.createElement(
                      "a",
                      {
                        href: ANDROID_APK_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                      },
                      "Baixar Android (.apk)"
                    )
                  : React.createElement(
                      Button,
                      { variant: "outline", className: "w-full justify-center", disabled: true },
                      "APK em breve"
                    ),
                hasAndroidAab
                  ? React.createElement(
                      "a",
                      {
                        href: ANDROID_AAB_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                      },
                      "Baixar bundle (.aab)"
                    )
                  : null,
                React.createElement(
                  "div",
                  { className: "rounded-xl border border-zinc-200 bg-white p-2 text-[11px] text-zinc-600" },
                  "PWA: no Chrome/Edge Android, abra o site e toque em 'Instalar app' para uso rápido sem loja."
                ),
                React.createElement(
                  "a",
                  {
                    href: SITE_URL,
                    target: "_blank",
                    rel: "noreferrer",
                    className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                  },
                  "Abrir versão web instalável (PWA)"
                )
              )
            ),
            React.createElement(
              "div",
              { className: "rounded-2xl border border-zinc-200 bg-zinc-100 p-4" },
              React.createElement(
                "p",
                { className: "mb-1 text-sm font-semibold text-zinc-900" },
                "iOS (iPhone / iPad)"
              ),
              React.createElement(
                "p",
                { className: "mb-3 text-xs text-zinc-500" },
                "Acesso via App Store ou build beta via TestFlight."
              ),
              React.createElement(
                "div",
                { className: "space-y-2" },
                hasIosStore
                  ? React.createElement(
                      "a",
                      {
                        href: IOS_APP_STORE_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                      },
                      "Abrir na App Store"
                    )
                  : React.createElement(
                      Button,
                      { variant: "outline", className: "w-full justify-center", disabled: true },
                      "App Store em breve"
                    ),
                hasIosTestFlight
                  ? React.createElement(
                      "a",
                      {
                        href: IOS_TESTFLIGHT_URL,
                        target: "_blank",
                        rel: "noreferrer",
                        className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                      },
                      "Entrar no beta TestFlight"
                    )
                  : React.createElement(
                      Button,
                      { variant: "outline", className: "w-full justify-center", disabled: true },
                      "TestFlight em breve"
                    ),
                React.createElement(
                  "a",
                  {
                    href: SITE_URL,
                    target: "_blank",
                    rel: "noreferrer",
                    className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                  },
                  "Instalar no iPhone (PWA sem loja)"
                ),
                hasIosDirectIpa && hasIosDirectManifest
                  ? React.createElement(
                      "a",
                      {
                        href: "itms-services://?action=download-manifest&url=" + encodeURIComponent(IOS_DIRECT_MANIFEST_URL),
                        className: btnBase + " border border-zinc-200 bg-transparent hover:bg-zinc-50 text-zinc-900",
                      },
                      "Instalação direta iOS (empresa)"
                    )
                  : React.createElement(
                      "div",
                      { className: "rounded-xl border border-zinc-200 bg-white p-2 text-[11px] text-zinc-600" },
                      "Sem App Store: iOS direto exige certificado corporativo (Apple Enterprise), MDM ou aparelhos autorizados. Hoje você já pode usar PWA no Safari (Compartilhar -> Adicionar à Tela de Início)."
                    )
              )
            ),
            React.createElement(
              "div",
              { className: "rounded-2xl border border-violet-200 bg-violet-50 p-4" },
              React.createElement("p", { className: "text-sm font-semibold text-zinc-900" }, "Modo offline institucional"),
              React.createElement(
                "ol",
                { className: "mt-2 list-decimal space-y-1 pl-5 text-xs text-zinc-600" },
                React.createElement("li", null, "Baixe o pacote Linux/Ubuntu para o servidor ou laboratório da instituição."),
                React.createElement("li", null, "No painel admin, gere/copie a chave de licença para a escola ou universidade."),
                React.createElement("li", null, "Instale o pacote e registre a chave no primeiro boot da aplicação."),
                React.createElement("li", null, "A operação principal roda localmente; quando houver internet, o sistema faz validação e heartbeat de licença.")
              ),
              React.createElement(
                "div",
                { className: "mt-3 rounded-xl border border-zinc-200 bg-white p-3" },
                React.createElement("p", { className: "text-xs font-semibold text-zinc-800" }, "Endpoints de validação/licença"),
                React.createElement("code", { className: "mt-1 block text-[11px] text-zinc-600" }, "GET /v1/institutional/validate/<CHAVE>"),
                React.createElement("code", { className: "mt-1 block text-[11px] text-zinc-600" }, "POST /v1/institutional/heartbeat/<CHAVE>")
              ),
              React.createElement("div", { className: "mt-3 flex flex-wrap gap-2" },
                React.createElement(
                  "a",
                  {
                    href: "/instalacao",
                    className: "inline-flex items-center justify-center rounded-full border border-zinc-200 bg-white px-4 py-2 text-xs font-medium text-zinc-700 hover:bg-zinc-50",
                  },
                  "Guia público de instalação"
                ),
                React.createElement(
                  "a",
                  {
                    href: "/docs",
                    className: "inline-flex items-center justify-center rounded-full border border-zinc-200 bg-white px-4 py-2 text-xs font-medium text-zinc-700 hover:bg-zinc-50",
                  },
                  "Abrir documentação técnica"
                ))
            )
          )
        )
      )
    )
  );
}

