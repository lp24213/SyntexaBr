"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Brand } from "./brand";
import { encryptedPath } from "../lib/routes";
import { FuturisticIcon } from "./icons/futuristic-icons";
import { getAdminMe } from "../lib/api";
import { getClientLocale, t } from "../lib/i18n";

function NavIcon({ name }) {
  return React.createElement(FuturisticIcon, { name: name || "spark", className: "h-4 w-4 text-zinc-600" });
}

function IconConfig() {
  return React.createElement(
    "svg",
    {
      className: "h-4 w-4 text-zinc-600",
      viewBox: "0 0 24 24",
      fill: "none",
      xmlns: "http://www.w3.org/2000/svg",
    },
    React.createElement("path", {
      d: "M12 9a3 3 0 100 6 3 3 0 000-6z",
      stroke: "currentColor",
      strokeWidth: "1.5",
    }),
    React.createElement("path", {
      d: "M4 13.5l1.2.2a1 1 0 01.8.7l.3 1.1a1 1 0 00.5.6l.9.5a1 1 0 01.5.8l.1 1.2a1 1 0 001 .9h1.4a1 1 0 001-.9l.1-1.2a1 1 0 01.5-.8l.9-.5a1 1 0 00.5-.6l.3-1.1a1 1 0 01.8-.7l1.2-.2a1 1 0 00.8-1v-1a1 1 0 00-.8-1l-1.2-.2a1 1 0 01-.8-.7l-.3-1.1a1 1 0 00-.5-.6l-.9-.5a1 1 0 01-.5-.8L14 6a1 1 0 00-1-.9h-1.4a1 1 0 00-1 .9l-.1 1.2a1 1 0 01-.5.8l-.9.5a1 1 0 00-.5.6l-.3 1.1a1 1 0 01-.8.7L4 11.5",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
      strokeLinejoin: "round",
    })
  );
}

function IconProfile() {
  return React.createElement(
    "svg",
    {
      className: "h-4 w-4 text-zinc-600",
      viewBox: "0 0 24 24",
      fill: "none",
      xmlns: "http://www.w3.org/2000/svg",
    },
    React.createElement("circle", {
      cx: "12",
      cy: "8",
      r: "3",
      stroke: "currentColor",
      strokeWidth: "1.5",
    }),
    React.createElement("path", {
      d: "M6 18c0-2.2 2.1-4 6-4s6 1.8 6 4",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
    })
  );
}

function IconDownload() {
  return React.createElement(
    "svg",
    { className: "h-4 w-4 text-zinc-600", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M12 4v12m0 0l-4-4m4 4l4-4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function IconLogin() {
  return React.createElement(
    "svg",
    {
      className: "h-4 w-4 text-zinc-600",
      viewBox: "0 0 24 24",
      fill: "none",
      xmlns: "http://www.w3.org/2000/svg",
    },
    React.createElement("path", {
      d: "M10 5h7a2 2 0 012 2v10a2 2 0 01-2 2h-7",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
    }),
    React.createElement("path", {
      d: "M14 12H4",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
    }),
    React.createElement("path", {
      d: "M7 9l-3 3 3 3",
      stroke: "currentColor",
      strokeWidth: "1.5",
      strokeLinecap: "round",
      strokeLinejoin: "round",
    })
  );
}

export function AppShell(props) {
  const { children } = props;
  const locale = getClientLocale();
  const [authed, setAuthed] = useState(false);
  const [role, setRole] = useState("user");
  const [isAdmin, setIsAdmin] = useState(false);

  function logout() {
    try {
      window.localStorage.removeItem("syntexa_token");
      window.localStorage.removeItem("syntexa_role");
      window.localStorage.removeItem("syntexa_is_admin");
    } catch {}
    window.location.href = encryptedPath("login");
  }

  useEffect(() => {
    (async function () {
      try {
        const token = window.localStorage.getItem("syntexa_token");
        const storedRole = window.localStorage.getItem("syntexa_role") || "user";
        setAuthed(!!token);
        setRole(storedRole);
        if (!token) {
          setIsAdmin(false);
          return;
        }
        const me = await getAdminMe(token);
        const validAdmin = !!(me && me.is_admin);
        setIsAdmin(validAdmin);
        window.localStorage.setItem("syntexa_is_admin", validAdmin ? "1" : "0");
      } catch {
        setAuthed(false);
        setIsAdmin(false);
      }
    })();
  }, []);

  var navItems;
  if (!authed) {
    navItems = [
      { path: "educacao", label: "Educação", iconName: "book" },
      { path: "login", label: t("login", locale), icon: IconLogin },
      { path: "register", label: "Cadastro", iconName: "users" },
      { path: "plans", label: t("plans", locale), iconName: "chart" },
      { path: "download", label: "Baixar app", iconName: "download" },
    ];
  } else if (isAdmin) {
    navItems = [
      { path: "admin", label: "Admin", iconName: "admin" },
      { path: "chat", label: t("chat", locale), iconName: "chat" },
      { path: "educacao", label: "Educação", iconName: "book" },
      { path: "portal", label: "Portal", iconName: "globe" },
      { path: "plans", label: t("plans", locale), iconName: "chart" },
      { path: "profile", label: t("profile", locale), iconName: "users" },
      { path: "config", label: "Config", iconName: "gear" },
      { path: "download", label: "Baixar", iconName: "download" },
    ];
  } else if (role === "teacher" || role === "researcher") {
    navItems = [
      { path: "chat", label: t("chat", locale), iconName: "chat" },
      { path: "educacao", label: "Educação", iconName: "book" },
      { path: "educacao-professor", label: "Prof.", iconName: "userTie" },
      { path: "plans", label: t("plans", locale), iconName: "chart" },
      { path: "config", label: "Configuração", icon: IconConfig },
      { path: "profile", label: "Perfil", icon: IconProfile },
      { path: "download", label: "Baixar app", iconName: "download" },
    ];
  } else {
    navItems = [
      { path: "chat", label: t("chat", locale), iconName: "chat" },
      { path: "educacao", label: "Educação", iconName: "book" },
      { path: "plans", label: t("plans", locale), iconName: "chart" },
      { path: "config", label: "Configuração", icon: IconConfig },
      { path: "profile", label: "Perfil", icon: IconProfile },
      { path: "download", label: "Baixar app", iconName: "download" },
    ];
  }

  return React.createElement(
    "div",
    { className: "relative min-h-screen w-full max-w-[100vw] overflow-x-hidden bg-[#f8f9fb] text-zinc-900 selection:bg-slate-200/80" },
    React.createElement(
      "div",
      { className: "mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 pb-10 pt-4 sm:px-8 sm:pb-12 sm:pt-6 lg:px-10" },
      React.createElement(
        motion.header,
        {
          className: "syntexa-header sticky top-0 z-20 -mx-4 mb-8 rounded-2xl px-4 py-4 sm:-mx-8 sm:mb-10 sm:rounded-none sm:px-8 sm:py-5 lg:-mx-10 lg:px-10",
          initial: { opacity: 0, y: -8 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.3 },
        },
        React.createElement(
          "div",
          { className: "flex flex-col items-center gap-5 sm:flex-row sm:items-center sm:justify-between sm:gap-4" },
          React.createElement(
            "a",
            { href: "/", className: "flex w-full shrink-0 items-center justify-center sm:w-auto sm:justify-start" },
            React.createElement("span", { className: "flex h-14 min-h-[56px] w-full max-w-[220px] items-center justify-center sm:h-16 sm:min-h-[64px] sm:max-w-[260px] sm:justify-start" }, React.createElement(Brand, { className: "h-12 w-full max-w-[200px] object-contain sm:h-14 sm:max-w-[240px] sm:object-left" }))
          ),
          React.createElement(
            "nav",
            { className: "flex w-full max-w-full flex-wrap items-center justify-center gap-1 sm:w-auto sm:flex-nowrap sm:justify-end" },
            navItems.map(function (item) {
              const Icon = item.icon;
              const href = encryptedPath(item.path);
              const showIcon = Icon || item.iconName;
              return React.createElement(
                "a",
                {
                  key: href,
                  href: href,
                  className:
                    "inline-flex min-h-[44px] min-w-[44px] items-center justify-center gap-1 rounded-xl px-2.5 py-2 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900 sm:min-h-0 sm:min-w-0 sm:px-3.5 sm:py-2.5",
                },
                showIcon
                  ? React.createElement(
                      React.Fragment,
                      null,
                      Icon
                        ? React.createElement(Icon, null)
                        : React.createElement(NavIcon, { name: item.iconName }),
                      React.createElement(
                        "span",
                        { className: "hidden sm:inline" },
                        item.label
                      )
                    )
                  : item.label
              );
            })
          ),
          authed &&
            React.createElement(
              "button",
              {
                type: "button",
                onClick: logout,
                className:
                  "inline-flex min-h-[44px] min-w-[44px] items-center justify-center gap-1 rounded-xl border border-zinc-200 bg-zinc-50 px-2.5 py-2 text-sm font-medium text-zinc-700 transition-colors hover:border-zinc-300 hover:bg-zinc-100 hover:text-zinc-900 sm:min-h-0 sm:min-w-0 sm:px-3.5 sm:py-2.5",
              },
              React.createElement(NavIcon, { name: "exit" }),
              React.createElement(
                "span",
                { className: "hidden sm:inline" },
                t("logout", locale)
              )
            )
        )
      ),
      React.createElement(
        motion.main,
        {
          className: "flex-1 w-full min-w-0",
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.35, ease: "easeOut" },
        },
        children
      ),
      React.createElement(
        "footer",
        { className: "mt-8 border-t border-zinc-200 pt-4 text-center text-[11px] text-zinc-500" },
        "© ",
        React.createElement(
          "span",
          { suppressHydrationWarning: true },
          String(new Date().getFullYear())
        ),
        " SyntexaBR. " + t("rightsReserved", locale) + " ",
        React.createElement("a", { href: encryptedPath("portal"), className: "underline underline-offset-2 hover:text-zinc-800" }, "Portal")
      )
    )
  );
}
