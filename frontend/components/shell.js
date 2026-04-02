"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Brand } from "./brand";
import { encryptedPath } from "../lib/routes";
import { FuturisticIcon } from "./icons/futuristic-icons";

function IconAdminNav() {
  return React.createElement(FuturisticIcon, { name: "admin", className: "h-4 w-4 text-cyan-400/85" });
}

function IconConfig() {
  return React.createElement(
    "svg",
    {
      className: "h-4 w-4 text-white/80",
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
      className: "h-4 w-4 text-white/80",
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
    { className: "h-4 w-4 text-white/80", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M12 4v12m0 0l-4-4m4 4l4-4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function IconLogin() {
  return React.createElement(
    "svg",
    {
      className: "h-4 w-4 text-white/80",
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
  const [authed, setAuthed] = useState(false);
  const [role, setRole] = useState("user");
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    try {
      const token = window.localStorage.getItem("syntexa_token");
      const storedRole = window.localStorage.getItem("syntexa_role") || "user";
      const storedAdmin = window.localStorage.getItem("syntexa_is_admin") === "1";
      setAuthed(!!token);
      setRole(storedRole);
      setIsAdmin(storedAdmin);
    } catch {
      setAuthed(false);
    }
  }, []);

  var navItems;
  if (!authed) {
    navItems = [
      { path: "educacao", label: "Educação", icon: null },
      { path: "login", label: "Login", icon: IconLogin },
      { path: "register", label: "Cadastro", icon: null },
      { path: "plans", label: "Planos", icon: null },
      { path: "download", label: "Baixar app", icon: null },
    ];
  } else if (isAdmin) {
    navItems = [
      { path: "admin", label: "Admin", icon: IconAdminNav },
      { path: "chat", label: "Chat", icon: null },
      { path: "educacao", label: "Educação", icon: null },
      { path: "plans", label: "Planos", icon: null },
      { path: "config", label: "Configuração", icon: IconConfig },
      { path: "download", label: "Baixar app", icon: IconDownload },
    ];
  } else if (role === "teacher" || role === "researcher") {
    navItems = [
      { path: "chat", label: "Chat", icon: null },
      { path: "educacao", label: "Educação", icon: null },
      { path: "educacao-professor", label: "Prof.", icon: null },
      { path: "plans", label: "Planos", icon: null },
      { path: "config", label: "Configuração", icon: IconConfig },
      { path: "profile", label: "Perfil", icon: IconProfile },
      { path: "download", label: "Baixar app", icon: null },
    ];
  } else {
    navItems = [
      { path: "chat", label: "Chat", icon: null },
      { path: "educacao", label: "Educação", icon: null },
      { path: "plans", label: "Planos", icon: null },
      { path: "config", label: "Configuração", icon: IconConfig },
      { path: "profile", label: "Perfil", icon: IconProfile },
      { path: "download", label: "Baixar app", icon: null },
    ];
  }

  return React.createElement(
    "div",
    { className: "relative min-h-screen text-white selection:bg-white/10" },
    React.createElement(
      "div",
      { className: "mx-auto flex min-h-screen max-w-6xl flex-col px-5 pb-12 pt-6 sm:px-8 lg:px-10" },
      React.createElement(
        motion.header,
        {
          className: "syntexa-header sticky top-0 z-20 -mx-5 mb-10 px-5 py-5 sm:-mx-8 sm:px-8 lg:-mx-10 lg:px-10",
          initial: { opacity: 0, y: -8 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.3 },
        },
        React.createElement(
          "div",
          { className: "flex items-center justify-between gap-4" },
          React.createElement(
            "a",
            { href: "/", className: "flex items-center gap-3" },
            React.createElement("span", { className: "flex h-16 min-h-[64px] w-[260px] items-center" }, React.createElement(Brand, { className: "h-14 w-full max-w-[240px] object-contain object-left" }))
          ),
          React.createElement(
            "nav",
            { className: "flex items-center gap-1" },
            navItems.map(function (item) {
              const Icon = item.icon;
              const href = encryptedPath(item.path);
              return React.createElement(
                "a",
                {
                  key: href,
                  href: href,
                  className:
                    "inline-flex items-center gap-1 rounded-xl px-3.5 py-2.5 text-sm font-medium text-white/80 transition-colors hover:bg-white/5 hover:text-white",
                },
                Icon
                  ? React.createElement(
                      React.Fragment,
                      null,
                      React.createElement(Icon, null),
                      React.createElement(
                        "span",
                        { className: "hidden sm:inline" },
                        item.label
                      )
                    )
                  : item.label
              );
            })
          )
        )
      ),
      React.createElement(
        motion.main,
        {
          className: "flex-1",
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.35, ease: "easeOut" },
        },
        children
      ),
      React.createElement(
        "footer",
        { className: "mt-8 border-t border-white/10 pt-4 text-center text-[11px] text-white/40" },
        "© ",
        new Date().getFullYear(),
        " SyntexaBR. Todos os direitos reservados. ",
        React.createElement("a", { href: encryptedPath("portal"), className: "underline underline-offset-2 hover:text-white/60" }, "Portal")
      )
    )
  );
}
