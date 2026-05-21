"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../../components/shell";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";
import { getAdminMe } from "../../../lib/api";
import { encryptedPath } from "../../../lib/routes";

// V46 — guarda is_admin igual aos outros /admin/* (antes a página era pública,
// permitindo ler instruções internas sem login).
function AdminGuard({ children }) {
  const [state, setState] = useState("checking");
  useEffect(function () {
    let cancel = false;
    (async function () {
      try {
        const token = typeof window !== "undefined" ? window.localStorage.getItem("syntexa_token") : null;
        if (!token) { if (!cancel) setState("denied"); return; }
        const me = await getAdminMe(token);
        if (!cancel) setState(me && me.is_admin ? "ok" : "denied");
      } catch { if (!cancel) setState("denied"); }
    })();
    return function () { cancel = true; };
  }, []);
  if (state === "checking") return React.createElement("div", { className: "p-10 text-sm text-zinc-500" }, "Verificando acesso…");
  if (state === "denied") {
    if (typeof window !== "undefined") { window.location.href = encryptedPath("login"); }
    return null;
  }
  return children;
}

const ITEMS_ANDROID = [
  "Gerar APK assinado (produção) e publicar em URL HTTPS da Syntexa.",
  "Opcional: gerar AAB para distribuição gerenciada por EMM/MDM.",
  "Habilitar instalação de fontes confiáveis nos dispositivos institucionais.",
  "Validar login, chat, exportações e licenciamento em 3 perfis de usuários.",
];

const ITEMS_IOS = [
  "PWA: Safari -> Compartilhar -> Adicionar à Tela de Início (sem App Store).",
  "Distribuição corporativa: IPA assinado com Apple Enterprise + MDM.",
  "Ad Hoc: registrar UDIDs para grupos restritos de testes.",
  "Se usar itms-services, manter manifest .plist e IPA em HTTPS público.",
];

const ITEMS_SECURITY = [
  "Configurar allowlist de IPs no Hub de Segurança antes da liberação.",
  "Distribuir chaves de licença por instituição com validade definida.",
  "Monitorar heartbeat de licenças para detectar instalações inativas.",
  "Rotacionar chaves comprometidas via botão 'Nova chave' no painel institucional.",
];

export default function MobileReleasePage() {
  return React.createElement(
    AdminGuard,
    null,
    React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto flex w-full max-w-5xl flex-col gap-5 px-4 py-8 sm:px-6" },
      React.createElement(
        "section",
        { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement(
          "h1",
          { className: "inline-flex items-center gap-2 text-xl font-semibold text-zinc-900" },
          React.createElement(FuturisticIcon, { name: "download", className: "h-5 w-5 text-violet-600" }),
          "Runbook de Distribuição Mobile"
        ),
        React.createElement(
          "p",
          { className: "mt-2 text-sm text-zinc-600" },
          "Procedimento oficial para distribuir Syntexa em Android e iOS de forma corporativa, segura e escalável."
        )
      ),
      React.createElement(
        "div",
        { className: "grid grid-cols-1 gap-4 lg:grid-cols-3" },
        React.createElement(
          "section",
          { className: "rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm" },
          React.createElement("h2", { className: "text-sm font-semibold text-zinc-900" }, "Android (APK/AAB)"),
          React.createElement(
            "ol",
            { className: "mt-2 list-decimal space-y-1.5 pl-5 text-xs text-zinc-600" },
            ITEMS_ANDROID.map(function (it, idx) { return React.createElement("li", { key: "a-" + idx }, it); })
          )
        ),
        React.createElement(
          "section",
          { className: "rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm" },
          React.createElement("h2", { className: "text-sm font-semibold text-zinc-900" }, "iOS (PWA / Enterprise)"),
          React.createElement(
            "ol",
            { className: "mt-2 list-decimal space-y-1.5 pl-5 text-xs text-zinc-600" },
            ITEMS_IOS.map(function (it, idx) { return React.createElement("li", { key: "i-" + idx }, it); })
          )
        ),
        React.createElement(
          "section",
          { className: "rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm" },
          React.createElement("h2", { className: "text-sm font-semibold text-zinc-900" }, "Segurança e licença"),
          React.createElement(
            "ol",
            { className: "mt-2 list-decimal space-y-1.5 pl-5 text-xs text-zinc-600" },
            ITEMS_SECURITY.map(function (it, idx) { return React.createElement("li", { key: "s-" + idx }, it); })
          )
        )
      ),
      React.createElement(
        "section",
        { className: "rounded-2xl border border-violet-200 bg-violet-50 p-5 shadow-sm" },
        React.createElement("h2", { className: "text-sm font-semibold text-zinc-900" }, "Variáveis públicas para downloads"),
        React.createElement(
          "pre",
          { className: "mt-2 overflow-auto rounded-xl border border-zinc-200 bg-white p-3 text-[11px] text-zinc-700" },
          [
            "NEXT_PUBLIC_SITE_URL=https://syntexabr.com.br",
            "NEXT_PUBLIC_ANDROID_APK_URL=https://syntexabr.com.br/download/SyntexaAI-android-arm64.apk",
            "NEXT_PUBLIC_DESKTOP_MAC_URL=https://syntexabr.com.br/download/SyntexaAI-macos-universal.dmg",
            "NEXT_PUBLIC_IOS_DIRECT_IPA_URL=",
            "NEXT_PUBLIC_IOS_DIRECT_MANIFEST_URL=",
          ].join("\n")
        ),
        React.createElement(
          "div",
          { className: "mt-3 flex flex-wrap gap-2" },
          React.createElement("a", { href: "/download", className: "rounded-xl bg-violet-600 px-4 py-2 text-xs font-medium text-white hover:bg-violet-500" }, "Ir para Download"),
          React.createElement("a", { href: "/admin/institucional", className: "rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs text-zinc-700 hover:bg-zinc-50" }, "Gerenciar licenças"),
          React.createElement("a", { href: "/admin/security-hub", className: "rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs text-zinc-700 hover:bg-zinc-50" }, "Abrir hub de segurança")
        )
      )
    )
    )
  );
}

