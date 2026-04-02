"use client";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Brand } from "./brand";
import { Button } from "./ui/button";
import { encryptedPath } from "../lib/routes";
import { listChatSessions } from "../lib/api";
import { FuturisticIcon } from "./icons/futuristic-icons";

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
  { path: "chat", label: "Chat", icon: IconChat },
  { path: "plans", label: "Planos", icon: IconPlans },
];

// Atalhos de Educação — sempre visíveis
var eduNavItems = [
  { path: "educacao", label: "Educação & Pesquisa", icon: "book" },
  { path: "educacao-laboratorios", label: "Laboratórios", icon: "microscope" },
  { path: "educacao-ciencia", label: "Ciência & Tecnologia", icon: "telescope" },
  { path: "educacao-concursos", label: "Concursos", icon: "medal" },
];

var teacherEduItems = [
  { path: "educacao-professor", label: "Área do Professor", icon: "userTie" },
];

var adminEduItems = [
  { path: "download", label: "Sistema Offline (Gov)", icon: "download" },
  { path: "portal", label: "Portal", icon: "map" },
];

export function ChatLayout(props) {
  var children = props.children;
  var onNewConversation = props.onNewConversation;
  var onSelectSession = props.onSelectSession;
  var router = useRouter();
  var pathname = usePathname();

  var _a = useState(false), authed = _a[0], setAuthed = _a[1];
  var _b = useState([]), sessions = _b[0], setSessions = _b[1];
  var _c = useState("user"), role = _c[0], setRole = _c[1];
  var _d = useState(false), isAdmin = _d[0], setIsAdmin = _d[1];

  useEffect(function () {
    (async function () {
      try {
        var token = window.localStorage.getItem("syntexa_token");
        var storedRole = window.localStorage.getItem("syntexa_role") || "user";
        var storedAdmin = window.localStorage.getItem("syntexa_is_admin") === "1";
        var ok = !!token;
        setAuthed(ok);
        setRole(storedRole);
        setIsAdmin(storedAdmin);
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
  }, []);

  function logout() {
    window.localStorage.removeItem("syntexa_token");
    window.location.href = encryptedPath("login");
  }

  return React.createElement(
    "div",
    { className: "relative flex h-[100dvh] max-h-[100dvh] w-full max-w-full overflow-hidden text-white" },
    React.createElement(
      motion.aside,
      {
        className: "syntexa-sidebar hidden h-full max-h-full w-[280px] shrink-0 overflow-y-auto px-5 py-6 sm:flex sm:flex-col",
        initial: { opacity: 0, x: -12 },
        animate: { opacity: 1, x: 0 },
        transition: { duration: 0.25 },
      },
      React.createElement(
        "div",
        { className: "mb-6 flex items-center border-b border-white/10 pb-6" },
        React.createElement(
          "a",
          { href: encryptedPath("chat"), className: "flex h-24 min-h-[96px] w-[320px] items-center" },
          React.createElement(Brand, { className: "h-24 w-full max-w-[300px] object-contain object-left" })
        )
      ),
      React.createElement(
        "div",
        { className: "mb-4 flex items-center justify-between" },
        React.createElement("span", { className: "text-xs text-zinc-500" }, "Conversas"),
        React.createElement(Button, {
          size: "sm",
          variant: "ghost",
          onClick: onNewConversation,
          className: "text-xs text-zinc-400 hover:text-white",
        }, "Nova")
      ),
      React.createElement(
        "div",
        { className: "flex-1 overflow-y-auto text-xs text-zinc-500 space-y-1" },
        sessions.length === 0
          ? React.createElement(
              "p",
              { className: "rounded-lg px-3 py-2 text-zinc-500" },
              "Histórico aparecerá aqui após você usar o chat autenticado."
            )
          : sessions.map(function (s) {
              return React.createElement(
                "button",
                {
                  key: s.id,
                  type: "button",
                  onClick: function () { onSelectSession && onSelectSession(s.id); },
                  className:
                    "flex w-full flex-col items-start gap-0.5 rounded-lg px-3 py-2 text-left text-zinc-300 hover:bg-white/5",
                },
                React.createElement(
                  "span",
                  { className: "text-xs font-medium text-white" },
                  s.title || "Nova conversa"
                ),
                React.createElement(
                  "span",
                  { className: "text-[10px] text-zinc-500" },
                  new Date(s.updated_at).toLocaleString("pt-BR")
                )
              );
            })
      ),
      React.createElement(
        "nav",
        { className: "mt-4 border-t border-white/10 pt-3 space-y-0.5" },
        baseNavItems.map(function (item) {
          var Icon = item.icon;
          var href = encryptedPath(item.path);
          var pathNorm = (pathname || "").replace(/\/$/, "") || "/";
          var hrefNorm = href.replace(/\/$/, "") || href;
          var active = pathNorm === "/" + item.path || pathNorm === href || pathNorm === hrefNorm;
          return React.createElement(
            "a",
            {
              key: href,
              href: href,
              className: "flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition-colors " + (active ? "bg-white/10 text-white" : "text-zinc-400 hover:bg-white/5 hover:text-white"),
            },
            Icon && React.createElement(Icon, null),
            React.createElement("span", null, item.label)
          );
        })
      ),
      React.createElement(
        "div",
        { className: "mt-4 border-t border-white/10 pt-3" },
        React.createElement("p", { className: "mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-zinc-600" }, "Ferramentas"),
        eduNavItems.concat(
          (role === "teacher" || role === "researcher") ? teacherEduItems : [],
          isAdmin ? adminEduItems : []
        ).map(function (item) {
          var href = encryptedPath(item.path);
          return React.createElement(
            "a",
            {
              key: href,
              href: href,
              className: "flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-zinc-400 transition-colors hover:bg-white/5 hover:text-white",
            },
            React.createElement(FuturisticIcon, { name: item.icon, className: "h-3.5 w-3.5 shrink-0 text-cyan-400/75" }),
            React.createElement("span", null, item.label)
          );
        })
      ),
      authed &&
        React.createElement(
          "div",
          { className: "mt-4 border-t border-white/10 pt-3" },
          React.createElement(
            "button",
            {
              type: "button",
              onClick: logout,
              className: "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-white/70 hover:bg-white/5 hover:text-white",
            },
            "Sair"
          )
        )
    ),
    React.createElement(
      "div",
      { className: "flex min-h-0 min-w-0 flex-1 flex-col w-full max-w-full overflow-hidden" },
      React.createElement(
        motion.header,
        {
          className: "syntexa-header sticky top-0 z-20 flex items-center justify-between gap-2 px-3 py-3 sm:px-5 sm:py-4 shrink-0",
          initial: { opacity: 0, y: -6 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.25 },
        },
        React.createElement(
          "div",
          { className: "flex items-center gap-3 sm:hidden min-w-0 flex-1" },
          React.createElement("span", { className: "flex h-10 w-full max-w-[160px] shrink-0 items-center" }, React.createElement(Brand, { className: "h-8 w-full max-w-[160px] object-contain object-left" }))
        ),
        React.createElement(
          "div",
          { className: "flex items-center gap-3" },
          authed
            ? React.createElement(
                React.Fragment,
                null,
                React.createElement("span", { className: "hidden sm:inline text-xs font-medium text-white/60" }, "Conta autenticada na Syntexa"),
                React.createElement("button", {
                  type: "button",
                  onClick: logout,
                  className: "rounded-xl border border-white/20 bg-white/5 px-3 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm font-medium text-white hover:bg-white/10",
                }, "Sair")
              )
            : React.createElement(
                React.Fragment,
                null,
                React.createElement("span", { className: "hidden sm:inline text-xs font-medium text-white/55" }, "Modo público gratuito (com limites)"),
                React.createElement("button", {
                  type: "button",
                  onClick: function () { window.location.href = encryptedPath("login"); },
                  className: "rounded-xl border border-white/20 bg-white/5 px-3 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm font-medium text-white hover:bg-white/10",
                }, "Login")
              )
        )
      ),
      React.createElement(
        motion.main,
        {
          className: "flex min-h-0 min-w-0 w-full flex-1 flex-col overflow-hidden",
          initial: { opacity: 0, y: 6 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.22 },
        },
        children
      ),
      React.createElement(
        "footer",
        { className: "hidden sm:block border-t border-white/10 px-3 py-2 sm:px-5 sm:py-3 text-center text-[11px] text-white/40 shrink-0" },
        "© ",
        new Date().getFullYear(),
        " SyntexaBR. Todos os direitos reservados."
      )
    )
  );
}
