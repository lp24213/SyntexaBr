"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { t } from "../../lib/i18n";
import { useLanguage } from "../../components/language-provider";

const WIN_URL = "";
const MAC_URL = "";
const LINUX_URL = "";
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

function IconWindows(props) {
  return React.createElement("svg", { className: props.className || "h-5 w-5", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M2 5.5l8-1.1v7.7H2V5.5zM11 4.3l11-1.5v9.2H11V4.3zM2 12.2h8v7.7l-8-1.1V12.2zM11 12.2h11v9.2L11 19.9v-7.7z", fill: "currentColor" })
  );
}
function IconMac(props) {
  return React.createElement("svg", { className: props.className || "h-5 w-5", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M17.3 8.2c-.6-1-1.6-1.6-2.7-1.6-.4 0-.8.1-1.2.2-.4.1-.7.2-1 .2-.3 0-.6-.1-1-.2-.3-.1-.7-.2-1.1-.2-1.2 0-2.3.7-2.9 1.7-1.2 2.1-.3 5.1.8 6.8.5.8 1.2 1.6 2 1.6.4 0 .6-.1 1-.3.3-.2.7-.3 1.2-.3s.9.1 1.2.3c.3.2.6.3 1 .3.8 0 1.5-.8 2-1.6.4-.5.7-1.1.9-1.7-.1 0-1.7-.7-1.7-2.6 0-1.6 1.2-2.3 1.3-2.4-.7-1-1.8-1.1-2.2-1.1-.1 0-.1 0-.2 0zM14.5 6c.7-.9 1.1-2 1-3.1-1 .1-2.1.7-2.8 1.6-.7.8-1 1.9-.9 2.9 1.1.1 2.1-.5 2.7-1.4z", fill: "currentColor" })
  );
}
function IconLinux(props) {
  return React.createElement("svg", { className: props.className || "h-5 w-5", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M12 3c-1.5 0-2.5 1-2.5 2.5 0 .5.1 1 .3 1.3-.5.3-1.3.8-1.8 1.5-.8 1-1 2.5-.5 4 .3 1 .8 1.8 1.3 2.3-.3.5-.5 1-.5 1.5 0 .5.2 1 .5 1.3-.3.3-.5.8-.5 1.3 0 1 .8 1.8 1.8 1.8h4.5c1 0 1.8-.8 1.8-1.8 0-.5-.2-1-.5-1.3.3-.3.5-.8.5-1.3 0-.5-.2-1-.5-1.5.5-.5 1-1.3 1.3-2.3.5-1.5.3-3-.5-4-.5-.7-1.3-1.2-1.8-1.5.2-.3.3-.8.3-1.3C14.5 4 13.5 3 12 3z", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}
function IconAndroid(props) {
  return React.createElement("svg", { className: props.className || "h-5 w-5", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M6 18a2 2 0 01-2-2V8a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H6z", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M9 6V4M15 6V4M12 11v4M10 13h4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}
function IconIOS(props) {
  return React.createElement("svg", { className: props.className || "h-5 w-5", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("rect", { x: "6", y: "3", width: "12", height: "18", rx: "3", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M10 7h4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

var btnBase =
  "inline-flex items-center justify-center rounded-full text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30 focus-visible:ring-offset-2 focus-visible:ring-offset-black w-full justify-center px-4 py-2";

var btn = "inline-flex w-full items-center justify-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold transition-all";

export default function DownloadPage() {
  const { locale } = useLanguage();
  const [pwaReady, setPwaReady] = useState(false);
  const [pwaInstalled, setPwaInstalled] = useState(false);

  useEffect(function () {
    if (typeof window === "undefined") return;
    if (window.__syntexaPwaPrompt) setPwaReady(true);
    function onReady() { setPwaReady(true); }
    function onInstalled() { setPwaInstalled(true); setPwaReady(false); }
    document.addEventListener("syntexa:pwa-ready", onReady);
    document.addEventListener("syntexa:pwa-installed", onInstalled);
    return function () {
      document.removeEventListener("syntexa:pwa-ready", onReady);
      document.removeEventListener("syntexa:pwa-installed", onInstalled);
    };
  }, []);

  function installPwa() {
    if (typeof window !== "undefined" && window.__syntexaInstallPwa) {
      window.__syntexaInstallPwa();
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "flex min-h-[calc(100vh-6rem)] items-center justify-center py-10 px-4" },
      React.createElement(
        motion.div,
        {
          className: "w-full max-w-lg space-y-5",
          initial: { opacity: 0, y: 20 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.35, ease: "easeOut" },
        },

        /* Header */
        React.createElement("div", { className: "text-center" },
          React.createElement("img", { src: "/LOGOTIPO.png", alt: "Syntexa", className: "mx-auto mb-4 h-16 w-16 rounded-2xl object-contain shadow" }),
          React.createElement("h1", { className: "text-2xl font-bold text-zinc-900" }, t('installTitle', locale)),
          React.createElement("p", { className: "mt-1 text-sm text-zinc-500" }, t('installSubtitle', locale))
        ),

        /* Card principal — Instalar PWA */
        React.createElement("div", { className: "rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm space-y-4" },
          React.createElement("div", { className: "flex items-center gap-3" },
            React.createElement("div", { className: "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-zinc-900 text-white" },
              React.createElement("svg", { viewBox: "0 0 24 24", fill: "none", className: "h-5 w-5" },
                React.createElement("path", { d: "M12 3v13M7 11l5 5 5-5M3 19h18", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round" })
              )
            ),
            React.createElement("div", null,
              React.createElement("p", { className: "font-semibold text-zinc-900" }, t('installPwaTitle', locale)),
              React.createElement("p", { className: "text-xs text-zinc-500" }, t('installPwaPlatforms', locale))
            )
          ),
          React.createElement("ul", { className: "space-y-1.5 text-sm text-zinc-600" },
            React.createElement("li", { className: "flex items-center gap-2" }, React.createElement("span", { className: "text-green-500 font-bold" }, "✓"), t('installPwaFeature1', locale)),
            React.createElement("li", { className: "flex items-center gap-2" }, React.createElement("span", { className: "text-green-500 font-bold" }, "✓"), t('installPwaFeature2', locale)),
            React.createElement("li", { className: "flex items-center gap-2" }, React.createElement("span", { className: "text-green-500 font-bold" }, "✓"), t('installPwaFeature3', locale)),
            React.createElement("li", { className: "flex items-center gap-2" }, React.createElement("span", { className: "text-green-500 font-bold" }, "✓"), t('installPwaFeature4', locale))
          ),
          pwaInstalled
            ? React.createElement("div", { className: btn + " bg-green-50 text-green-700 border border-green-200" }, t('installPwaInstalled', locale))
            : pwaReady
            ? React.createElement("button", { type: "button", onClick: installPwa, className: btn + " bg-zinc-900 text-white hover:bg-zinc-800 shadow" }, t('installPwaInstallNow', locale))
            : React.createElement("div", { className: "space-y-2" },
                React.createElement("button", { type: "button", onClick: installPwa, className: btn + " bg-zinc-900 text-white hover:bg-zinc-800 shadow" }, t('installPwaInstall', locale)),
                React.createElement("p", { className: "text-center text-[11px] text-zinc-400" }, t('installPwaHelp', locale))
              )
        ),

        /* Separador */
        React.createElement("div", { className: "flex items-center gap-3" },
          React.createElement("div", { className: "flex-1 border-t border-zinc-200" }),
          React.createElement("span", { className: "text-xs text-zinc-400" }, t('installOr', locale)),
          React.createElement("div", { className: "flex-1 border-t border-zinc-200" })
        ),

        /* Abrir no browser */
        React.createElement("a", { href: "/chat", className: btn + " border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 shadow-sm" },
          t('installOpenBrowser', locale)
        ),

        /* iOS / Android instrução */
        React.createElement("div", { className: "rounded-2xl border border-zinc-100 bg-zinc-50 p-4 space-y-3 text-xs text-zinc-500" },
          React.createElement("p", { className: "font-semibold text-zinc-700" }, t('installIosTitle', locale)),
          React.createElement("p", null, t('installIosHelp', locale)),
          React.createElement("p", { className: "font-semibold text-zinc-700 pt-1" }, t('installAndroidTitle', locale)),
          React.createElement("p", null, t('installAndroidHelp', locale))
        )
      )
    )
  );
}
