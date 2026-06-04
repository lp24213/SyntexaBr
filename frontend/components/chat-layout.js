"use client";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Brand } from "./brand";
import { Button } from "./ui/button";
import { encryptedPath } from "../lib/routes";
import { getAdminMe, listChatSessions } from "../lib/api";
import { FuturisticIcon } from "./icons/futuristic-icons";
import { formatDateTime, t } from "../lib/i18n";
import { useLanguage } from "./language-provider";
import { QuantumCodeStream } from "./quantum-code-stream";


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
  { path: "/chat", labelKey: "chat", icon: IconChat },
  { path: "/plans", labelKey: "plans", icon: IconPlans },
];

// Atalhos de Educação — sempre visíveis
var eduNavItems = [
  { path: "/educacao", labelKey: "educationResearch", icon: "book" },
  { path: "/educacao/aluno", labelKey: "aluno", icon: "users" },
  { path: "/educacao/laboratorios", labelKey: "labs", icon: "microscope" },
  { path: "/educacao/ciencia", labelKey: "scienceTech", icon: "telescope" },
  { path: "/educacao/concursos", labelKey: "competitions", icon: "medal" },
  { path: "/educacao/governo", labelKey: "government", icon: "globe" },
];

var teacherEduItems = [
  { path: "/educacao/professor", labelKey: "teacherArea", icon: "userTie" },
];

var practicalNavItems = [
  {
    href: "/chat?q=" + encodeURIComponent("Syntexa, ative seu modo completo e me apresente todas as capacidades multimodais de forma prática."),
    labelKey: "fullAi",
    icon: "spark",
  },
  { href: "/chat?mode=bank&q=" + encodeURIComponent("Quero organizar meu controle de banco, pix e fluxo de caixa."), labelKey: "bankFinance", icon: "chart" },
  { href: "/chat?mode=agro&q=" + encodeURIComponent("Monte um plano de gestão para agronegócio com custos e produção."), labelKey: "agro", icon: "bolt" },
  { href: "/chat?mode=tax&q=" + encodeURIComponent("Me ajude com impostos no Brasil, nota fiscal e regularização."), labelKey: "taxes", icon: "doc" },
  { href: "/chat?mode=sales_whatsapp&q=" + encodeURIComponent("Crie uma rotina de vendas e mensagens para WhatsApp."), labelKey: "whatsappSales", icon: "chat" },
];

var generalNavItems = [
  { path: "/chat", labelKey: "chat", icon: "chat" },
  { path: "/plans", labelKey: "plans", icon: "chart" },
  { path: "/portal", labelKey: "portal", icon: "globe" },
  { path: "/download", labelKey: "download", icon: "download" },
];

var accountNavItems = [
  { path: "/profile", labelKey: "profile", icon: "users" },
  { path: "/config", labelKey: "settings", icon: "gear" },
  { path: "/portal", labelKey: "portal", icon: "map" },
];

var accountAdminExtraItems = [
  { path: "/download", labelKey: "offlineSystem", icon: "download" },
];

export function ChatLayout(props) {
  var children = props.children;
  var onNewConversation = props.onNewConversation;
  var onSelectSession = props.onSelectSession;
  var sessionsRefreshKey = props.sessionsRefreshKey || 0;
  var router = useRouter();
  var pathname = usePathname();
  const { locale } = useLanguage();

  var _a = useState(false), authed = _a[0], setAuthed = _a[1];
  var _b = useState([]), sessions = _b[0], setSessions = _b[1];
  var _c = useState("user"), role = _c[0], setRole = _c[1];
  var _d = useState(false), isAdmin = _d[0], setIsAdmin = _d[1];
  var _e = useState(false), sidebarOpen = _e[0], setSidebarOpen = _e[1];

  useEffect(function () {
    // Em desktop (sm:), sempre mostrar sidebar. Em mobile, começar fechado.
    if (typeof window !== "undefined") {
      var isMobile = window.innerWidth < 640;
      if (isMobile) {
        setSidebarOpen(false);
      } else {
        setSidebarOpen(true);
      }
    }
  }, []);

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
    window.location.href = "/login";
  }

  return React.createElement(
    "div",
    { className: "chat-root" },
    React.createElement("style", null, "@media (max-width: 639px) { .syntexa-sidebar { display: none !important; visibility: hidden !important; pointer-events: none !important; width: 0 !important; height: 0 !important; } }"),
    React.createElement("div", { className: "fixed inset-0 z-0 pointer-events-none" },
      React.createElement("div", { className: "absolute inset-0 bg-[linear-gradient(180deg,#fafbfc_0%,#f5f6f8_50%,#f3f4f5_100%)]" }),
      React.createElement(QuantumCodeStream, null)
    ),
    React.createElement(
      "div",
      { className: "chat-layout" },
      React.createElement(
        "div",
        { className: "hidden" },
        React.createElement(
          Button,
          {
            type: "button",
            variant: "outline",
            onClick: function () { return setSidebarOpen(!sidebarOpen); },
            className: "inline-flex items-center gap-2 rounded-2xl border border-[#e2e8f0] bg-white px-3 py-2 text-sm text-[#0f172a] shadow-sm",
          },
          React.createElement(IconChat, null),
          t("history", locale)
        )
      ),
      React.createElement(
        "aside",
        {
          className:
            "syntexa-sidebar hidden sm:flex sm:flex-col sm:z-auto sm:h-full sm:max-h-full sm:w-[260px] sm:max-w-[320px] sm:border-r sm:border-b-0 sm:bg-white/70 sm:shadow-none sm:overflow-visible sm:static border-none px-5 py-6 shadow-none transition-all duration-200",
        },
      /* V46 — banner Syntexa interno do sidebar removido (era o "2º header"
         duplicado relatado pelo usuário). O logo já existe no top header. */
      React.createElement(
        "div",
        { className: "mb-4 flex items-center justify-between gap-2" },
        React.createElement("span", { className: "text-xs text-zinc-500" }, t("conversations", locale)),
        React.createElement(
          "div",
          { className: "flex items-center gap-2" },
          React.createElement(Button, {
            size: "sm",
            variant: "ghost",
            onClick: onNewConversation,
            className: "text-xs text-zinc-400 hover:text-zinc-900",
          }, t("new", locale)),
          React.createElement(
            "button",
            {
              type: "button",
              onClick: function () { return setSidebarOpen(false); },
              className: "inline-flex items-center justify-center rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-2.5 py-2 text-xs font-medium text-[#475569] hover:bg-[#f1f5f9] sm:hidden",
              "aria-label": t("close", locale) || "Fechar histórico",
            },
            "×"
          )
        )
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
      /* V46 — seções general / specializations / tools / account removidas
         do sidebar do Console. Toda navegação fica concentrada no header
         (Início · Planos · Console · Login). Mantém-se apenas a lista de
         conversas acima e o botão de logout abaixo. */
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
        "main",
        {
          className: "chat-main",
          style: { paddingTop: 0, background: "transparent", color: "#1a1c1e", position: "relative", isolation: "isolate" },
        },
        React.createElement("div", {
          className: "pointer-events-none absolute inset-0 z-0",
          style: { background: "linear-gradient(180deg,rgba(250,251,252,0.8),rgba(245,246,248,0.95))" },
          "aria-hidden": true,
        }),
        React.createElement("div", { className: "content-layer relative z-10 w-full h-full flex flex-col justify-between min-h-0" }, children)
      )
    )
  );
}
