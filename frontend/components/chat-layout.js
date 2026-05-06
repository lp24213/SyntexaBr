"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter, usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Brand } from "./brand";
import { Button } from "./ui/button";
import { encryptedPath } from "../lib/routes";
import { getAdminMe, listChatSessions } from "../lib/api";
import { FuturisticIcon } from "./icons/futuristic-icons";
import { formatDateTime, getClientLocale, t } from "../lib/i18n";

var BinaryRain = dynamic(function () {
  return import("./BinaryRain");
}, { ssr: false });

function IconChat() {
  return React.createElement(
    "svg",
    { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", {
      d: "M6 18l-2.5 2.5M6 18h9a5 5 0 005-5V9a5 5 0 00-5-5H9a5 5 0 00-5 5v4a5 5 0 002 4z",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
      strokeLinejoin: "round",
    }),
    React.createElement("path", {
      d: "M9 10h6M9 13h3",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
    })
  );
}

function IconPlans() {
  return React.createElement(
    "svg",
    { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("rect", {
      x: "4",
      y: "5",
      width: "6",
      height: "14",
      rx: "1.5",
      stroke: "currentColor",
      strokeWidth: "1.5",
    }),
    React.createElement("rect", {
      x: "10",
      y: "3",
      width: "6",
      height: "16",
      rx: "1.5",
      stroke: "currentColor",
      strokeWidth: "1.5",
    }),
    React.createElement("rect", {
      x: "16",
      y: "8",
      width: "4",
      height: "11",
      rx: "1.5",
      stroke: "currentColor",
      strokeWidth: "1.5",
    })
  );
}

var baseNavItems = [
  { path: "chat", labelKey: "chat", icon: IconChat },
  { path: "plans", labelKey: "plans", icon: IconPlans },
];

// Atalhos de Educação — sempre visíveis
var eduNavItems = [
  { path: "educacao", labelKey: "educationResearch", icon: "book" },
  { path: "educacao-laboratorios", labelKey: "labs", icon: "microscope" },
  { path: "educacao-ciencia", labelKey: "scienceTech", icon: "telescope" },
  { path: "educacao-concursos", labelKey: "competitions", icon: "medal" },
];

var teacherEduItems = [
  { path: "educacao-professor", labelKey: "teacherArea", icon: "userTie" },
];

var practicalNavItems = [
  {
    href:
      encryptedPath("chat") +
      "&q=" +
      encodeURIComponent(
        "Syntexa, ative seu modo completo e me apresente todas as capacidades multimodais de forma prática."
      ),
    labelKey: "fullAi",
    icon: "spark",
  },
  { href: encryptedPath("chat") + "&mode=bank&q=" + encodeURIComponent("Quero organizar meu controle de banco, pix e fluxo de caixa."), labelKey: "bankFinance", icon: "chart" },
  { href: encryptedPath("chat") + "&mode=agro&q=" + encodeURIComponent("Monte um plano de gestão para agronegócio com custos e produção."), labelKey: "agro", icon: "bolt" },
  { href: encryptedPath("chat") + "&mode=tax&q=" + encodeURIComponent("Me ajude com impostos no Brasil, nota fiscal e regularização."), labelKey: "taxes", icon: "doc" },
  { href: encryptedPath("chat") + "&mode=sales_whatsapp&q=" + encodeURIComponent("Crie uma rotina de vendas e mensagens para WhatsApp."), labelKey: "whatsappSales", icon: "chat" },
];

var generalNavItems = [
  { path: "chat", labelKey: "chat", icon: "chat" },
  { path: "plans", labelKey: "plans", icon: "chart" },
  { path: "portal", labelKey: "portal", icon: "globe" },
];

var accountNavItems = [
  { path: "profile", labelKey: "profile", icon: "users" },
  { path: "config", labelKey: "settings", icon: "gear" },
  { path: "portal", labelKey: "portal", icon: "map" },
];

var accountAdminExtraItems = [
  { path: "download", labelKey: "offlineSystem", icon: "download" },
  { path: "admin-integrations", labelKey: "apiTokens", icon: "key" },
];

export function ChatLayout(props) {
  var children = props.children;
  var onNewConversation = props.onNewConversation;
  var onSelectSession = props.onSelectSession;
  var sessionsRefreshKey = props.sessionsRefreshKey || 0;
  var router = useRouter();
  var pathname = usePathname();
  var locale = getClientLocale();

  var _a = useState(false), authed = _a[0], setAuthed = _a[1];
  var _b = useState([]), sessions = _b[0], setSessions = _b[1];
  var _c = useState("user"), role = _c[0], setRole = _c[1];
  var _d = useState(false), isAdmin = _d[0], setIsAdmin = _d[1];

  useEffect(function () {
    (async function () {
      try {
        var token = window.localStorage.getItem("syntexa_token");
        var storedRole = window.localStorage.getItem("syntexa_role") || "user";
        var ok = !!token;
        setAuthed(ok);
        setRole(storedRole);
        if (ok) {
          try {
            var me = await getAdminMe(token);
            var adminOk = !!(me && me.is_admin);
            setIsAdmin(adminOk);
            window.localStorage.setItem("syntexa_is_admin", adminOk ? "1" : "0");
          } catch {
            setIsAdmin(false);
            window.localStorage.setItem("syntexa_is_admin", "0");
          }
        } else {
          setIsAdmin(false);
        }
        if (ok) {
          try {
            var list = await listChatSessions(token);
            setSessions(Array.isArray(list) ? list : []);
          } catch {
            setSessions([]);
          }
        } else {
          setSessions([]);
        }
      } catch {
        setAuthed(false);
        setSessions([]);
      }
    })();
  }, [sessionsRefreshKey]);

  function logout() {
    window.localStorage.removeItem("syntexa_token");
    window.location.href = encryptedPath("login");
  }

  return React.createElement(
    "div",
    { className: "relative flex h-[100dvh] max-h-[100dvh] w-full max-w-full overflow-hidden bg-[#ececf0] text-zinc-900" },
    React.createElement(
      "div",
      { className: "fixed top-0 left-0 w-full z-30 flex items-center justify-between h-10 px-4 bg-[#ececf0] border-b border-zinc-200 shadow-sm select-none" },
      React.createElement("div", { className: "flex items-center gap-2" },
        React.createElement("span", { className: "inline-block w-3 h-3 rounded-full bg-[#ff5f56] border border-zinc-300 mr-1" }),
        React.createElement("span", { className: "inline-block w-3 h-3 rounded-full bg-[#ffbd2e] border border-zinc-300 mr-1" }),
        React.createElement("span", { className: "inline-block w-3 h-3 rounded-full bg-[#27c93f] border border-zinc-300" })
      ),
      React.createElement(
        "div",
        { className: "flex flex-1 items-center justify-center" },
        React.createElement(Brand, { className: "h-12 w-[280px] object-contain" })
      ),
      React.createElement("div", { className: "flex items-center gap-2" },
        authed
          ? React.createElement(
              React.Fragment,
              null,
              React.createElement("span", { className: "hidden sm:inline text-xs font-medium text-zinc-600" }, t("authenticatedAccount", locale)),
              React.createElement("button", {
                type: "button",
                onClick: logout,
                className: "rounded-xl border border-zinc-300 bg-white px-3 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm font-medium text-zinc-700 hover:bg-zinc-100",
              }, t("logout", locale))
            )
          : React.createElement(
              React.Fragment,
              null,
              React.createElement("span", { className: "hidden sm:inline text-xs font-medium text-zinc-500" }, t("publicMode", locale)),
              React.createElement("button", {
                type: "button",
                onClick: function () { window.location.href = encryptedPath("login"); },
                className: "rounded-xl border border-zinc-300 bg-white px-3 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm font-medium text-zinc-700 hover:bg-zinc-100",
              }, t("login", locale))
            )
      )
    ),
    React.createElement(
      motion.aside,
      {
        className: "syntexa-sidebar hidden h-full max-h-full min-w-[220px] w-[260px] max-w-[320px] shrink-0 overflow-y-auto px-5 py-6 sm:flex sm:flex-col bg-[#f7f7fa] border-r border-zinc-200",
        style: { paddingTop: 48 },
        initial: { opacity: 0, x: -12 },
        animate: { opacity: 1, x: 0 },
        transition: { duration: 0.25 },
      },
      React.createElement(
        "div",
        { className: "mb-6 flex items-center border-b border-zinc-200 pb-6" },
        React.createElement(
          "a",
          { href: encryptedPath("chat"), className: "flex h-28 min-h-[112px] w-[320px] items-center justify-center" },
          React.createElement(Brand, { className: "h-24 w-full max-w-[300px] object-contain" })
        )
      ),
      React.createElement(
        "div",
        { className: "mb-4 flex items-center justify-between" },
        React.createElement("span", { className: "text-xs text-zinc-500" }, t("conversations", locale)),
        React.createElement(Button, {
          size: "sm",
          variant: "ghost",
          onClick: onNewConversation,
          className: "text-xs text-zinc-400 hover:text-zinc-900",
        }, t("new", locale))
      ),
      React.createElement(
        "div",
        { className: "flex-1 overflow-y-auto text-xs text-zinc-500 space-y-1" },
        sessions.length === 0
          ? React.createElement(
              "p",
              { className: "rounded-lg px-3 py-2 text-zinc-500" },
              t("historyHint", locale)
            )
          : sessions.map(function (s) {
              return React.createElement(
                "button",
                {
                  key: s.id,
                  type: "button",
                  onClick: function () { onSelectSession && onSelectSession(s.id); },
                  className:
                    "flex w-full flex-col items-start gap-0.5 rounded-lg px-3 py-2 text-left text-zinc-700 hover:bg-zinc-100",
                },
                React.createElement(
                  "span",
                  { className: "text-xs font-medium text-zinc-800" },
                  s.title || t("newConversation", locale)
                ),
                React.createElement(
                  "span",
                  { className: "text-[10px] text-zinc-500" },
                  formatDateTime(s.updated_at, locale)
                )
              );
            })
      ),
      React.createElement(
        "div",
        { className: "mt-4 border-t border-zinc-200 pt-3" },
        React.createElement("p", { className: "mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-zinc-600" }, t("general", locale)),
        generalNavItems.map(function (item) {
          var href = encryptedPath(item.path);
          var pathNorm = (pathname || "").replace(/\/$/, "") || "/";
          var hrefNorm = href.replace(/\/$/, "") || href;
          var active = pathNorm === "/" + item.path || pathNorm === href || pathNorm === hrefNorm;
          return React.createElement(
            "a",
            {
              key: href,
              href: href,
              className: "flex items-center gap-2 rounded-lg px-3 py-2 text-xs transition-colors " + (active ? "bg-zinc-100 text-zinc-900" : "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900"),
            },
            React.createElement(FuturisticIcon, { name: item.icon, className: "h-3.5 w-3.5 shrink-0 text-cyan-400/75" }),
            React.createElement("span", null, t(item.labelKey, locale))
          );
        })
      ),
      React.createElement(
        "div",
        { className: "mt-3 border-t border-zinc-200 pt-3" },
        React.createElement("p", { className: "mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-zinc-600" }, t("specializations", locale)),
        practicalNavItems.map(function (item) {
          var href = item.href || encryptedPath(item.path);
          return React.createElement(
            "a",
            {
              key: href,
              href: href,
              className: "flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-900",
            },
            React.createElement(FuturisticIcon, { name: item.icon, className: "h-3.5 w-3.5 shrink-0 text-cyan-400/75" }),
            React.createElement("span", null, t(item.labelKey, locale))
          );
        })
      ),
      React.createElement(
        "div",
        { className: "mt-3 border-t border-zinc-200 pt-3" },
        React.createElement("p", { className: "mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-zinc-600" }, t("tools", locale)),
        eduNavItems.concat((role === "teacher" || role === "researcher") ? teacherEduItems : []).map(function (item) {
          var href = item.href || encryptedPath(item.path);
          return React.createElement(
            "a",
            {
              key: href,
              href: href,
              className: "flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-900",
            },
            React.createElement(FuturisticIcon, { name: item.icon, className: "h-3.5 w-3.5 shrink-0 text-cyan-400/75" }),
            React.createElement("span", null, t(item.labelKey, locale))
          );
        })
      ),
      React.createElement(
        "div",
        { className: "mt-3 border-t border-zinc-200 pt-3" },
        React.createElement("p", { className: "mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-zinc-600" }, t("account", locale)),
        accountNavItems.concat(isAdmin ? accountAdminExtraItems : []).map(function (item) {
          var href = encryptedPath(item.path);
          return React.createElement(
            "a",
            {
              key: href,
              href: href,
              className: "flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-900",
            },
            React.createElement(FuturisticIcon, { name: item.icon, className: "h-3.5 w-3.5 shrink-0 text-cyan-400/75" }),
            React.createElement("span", null, t(item.labelKey, locale))
          );
        })
      ),
      authed &&
        React.createElement(
          "div",
          { className: "mt-4 border-t border-zinc-200 pt-3" },
          React.createElement(
            "button",
            {
              type: "button",
              onClick: logout,
              className: "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900",
            },
            t("logout", locale)
          )
        )
    ),
    React.createElement(
      "div",
      { className: "flex min-h-0 min-w-0 flex-1 flex-col w-full max-w-full overflow-hidden bg-[#f7f7fa]" },
      // ...existing code...
      React.createElement(
        motion.main,
        {
          className: "chat-main flex min-h-0 min-w-0 w-full flex-1 flex-col overflow-hidden",
          style: { paddingTop: 48, background: "transparent", color: "#111827", position: "relative", isolation: "isolate" },
          initial: { opacity: 0, y: 6 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.22 },
        },
        React.createElement("div", {
          className: "pointer-events-none absolute inset-0 z-0",
          style: { background: "linear-gradient(180deg,#f7f7fa,#eef0f4)" },
          "aria-hidden": true,
        }),
        React.createElement(BinaryRain, null),
        React.createElement("div", { className: "content-layer relative z-10 w-full h-full flex flex-col justify-between min-h-0" }, children)
      ),
      React.createElement(
        "footer",
        {
          className: "hidden sm:block border-t border-zinc-200 px-3 py-2 sm:px-5 sm:py-3 text-center text-[11px] text-zinc-400 shrink-0 bg-[#f7f7fa]",
          suppressHydrationWarning: true,
        },
        "© ",
        React.createElement("span", { suppressHydrationWarning: true }, String(new Date().getFullYear())),
        " SyntexaBR. " + t("rightsReserved", locale)
      )
    )
  );
}
