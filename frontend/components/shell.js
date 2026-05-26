"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { PwaInstallButton } from "./PwaInstallButton";
import { encryptedPath } from "../lib/routes";
import { getAdminMe } from "../lib/api";
import { getClientLocale, t } from "../lib/i18n";
var QuantumCodeStream = dynamic(function () { return import("./quantum-code-stream").then(function (m) { return m.QuantumCodeStream; }); }, { ssr: false });

function IconConfig() {
  return React.createElement(
    "svg",
    {
      className: "h-[15px] w-[15px] text-[#5a5c5e]",
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
      className: "h-[15px] w-[15px] text-[#5a5c5e]",
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
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M12 4v12m0 0l-4-4m4 4l4-4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function IconLogin() {
  return React.createElement(
    "svg",
    {
      className: "h-[15px] w-[15px] text-[#5a5c5e]",
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

function IconChat() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

function IconBook() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M4 19.5A2.5 2.5 0 016.5 17H20", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

function IconGlobe() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("circle", { cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z", stroke: "currentColor", strokeWidth: "1.5" })
  );
}

function IconChart() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M18 20V10M12 20V4M6 20v-6", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

function IconUsers() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("circle", { cx: "9", cy: "7", r: "4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

function IconUserTie() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("circle", { cx: "12", cy: "7", r: "4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M12 3v4M10 3h4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

function IconGear() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("circle", { cx: "12", cy: "12", r: "3", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

function IconExit() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

const ICON_MAP = {
  chat: IconChat,
  book: IconBook,
  globe: IconGlobe,
  chart: IconChart,
  users: IconUsers,
  userTie: IconUserTie,
  gear: IconGear,
  download: IconDownload,
  exit: IconExit,
};

function IconMenu() {
  return React.createElement("svg", { className: "h-5 w-5", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M4 6h16M4 12h16M4 18h16", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function IconClose() {
  return React.createElement("svg", { className: "h-5 w-5", viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" },
    React.createElement("path", { d: "M6 6l12 12M18 6L6 18", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

export function AppShell(props) {
  const { children, fullWidth } = props;
  const locale = getClientLocale();
  const [authed, setAuthed] = useState(false);
  const [role, setRole] = useState("user");
  const [isAdmin, setIsAdmin] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

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

  useEffect(function () {
    if (typeof document === "undefined") return;
    if (menuOpen) {
      document.body.style.overflow = "hidden";
      document.body.style.touchAction = "none";
    } else {
      document.body.style.overflow = "";
      document.body.style.touchAction = "";
    }
    return function () {
      document.body.style.overflow = "";
      document.body.style.touchAction = "";
    };
  }, [menuOpen]);

  var navItems = [
    { path: "/", label: "Início", icon: IconGlobe },
    { path: "/plans", label: "Planos", icon: IconChart },
    { path: "/chat", label: "Console", icon: IconChat },
  ];

  return React.createElement(
    "div",
    { className: "relative min-h-screen w-full max-w-[100vw] overflow-x-hidden bg-transparent text-[#1a1c1e] selection:bg-[rgba(200,205,212,0.3)]" },
    React.createElement("div", { className: "fixed inset-0 z-0 pointer-events-none" },
      React.createElement("div", { className: "absolute inset-0 bg-[linear-gradient(180deg,#fafbfc_0%,#f5f6f8_50%,#f3f4f5_100%)]" }),
      React.createElement(QuantumCodeStream, null)
    ),
    React.createElement(
      "div",
      { className: fullWidth ? "relative z-10 mx-auto flex min-h-screen w-full flex-col pb-10 pt-14 sm:pb-12 sm:pt-16" : "relative z-10 mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 pb-10 pt-14 sm:px-8 sm:pb-12 sm:pt-16 lg:px-10" },
      React.createElement(
        "header",
        {
          className: "syntexa-header fixed top-0 left-0 z-[40] w-full",
        },
        React.createElement(
          "div",
          { className: "mx-auto flex h-14 max-w-[1280px] items-center justify-between px-4 sm:px-6" },
          React.createElement("div", { className: "flex items-center gap-3 min-w-0 flex-1" },
            React.createElement("button", {
              type: "button",
              onClick: function () { setMenuOpen(!menuOpen); },
              className: "inline-flex items-center justify-center rounded-lg p-2 text-[#64748b] hover:bg-[rgba(15,23,42,0.04)] lg:hidden",
              "aria-label": "Menu",
            }, menuOpen ? React.createElement(IconClose, null) : React.createElement(IconMenu, null)),
            React.createElement(
              "a",
              { href: encryptedPath("/"), className: "flex shrink-0 items-center justify-center" },
              React.createElement("img", {
                src: "/LOGOTIPO.png",
                alt: "Syntexa",
                className: "h-14 w-auto object-contain",
                draggable: false,
                decoding: "async",
              })
            )
          ),
          React.createElement(
            "nav",
            { className: "hidden items-center gap-1 lg:flex absolute left-1/2 -translate-x-1/2" },
            navItems.map(function (item) {
              const Icon = item.icon;
              const href = encryptedPath(item.path);
              return React.createElement(
                "a",
                {
                  key: href + "-" + item.label,
                  href: href,
                  className:
                    "rounded-lg px-3 py-1.5 text-[13px] text-[#64748b] transition-colors duration-200 hover:bg-[rgba(15,23,42,0.04)] hover:text-[#0f172a]",
                },
                item.label
              );
            })
          ),
          React.createElement("div", { className: "flex items-center gap-3 min-w-0 flex-1 justify-end" },
            React.createElement(PwaInstallButton, { className: "hidden sm:inline-flex items-center gap-1.5 rounded-[10px] px-3 py-2 text-[13px] font-medium text-[#5a5c5e] border border-[rgba(15,23,42,0.08)] hover:bg-[rgba(20,24,30,0.04)] transition-colors duration-150" }),
            authed
              ? React.createElement(
                  "button",
                  {
                    type: "button",
                    onClick: logout,
                    className:
                      "inline-flex items-center justify-center gap-1.5 rounded-[10px] px-3 py-2 text-[13px] font-medium text-[#5a5c5e] transition-colors duration-150 hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e]",
                  },
                  React.createElement(IconExit, null),
                  React.createElement("span", { className: "hidden sm:inline" }, t("logout", locale))
                )
              : React.createElement(
                  "a",
                  { href: encryptedPath("login"), className: "inline-flex items-center justify-center gap-1.5 rounded-[10px] px-3 py-2 text-[13px] font-medium text-[#5a5c5e] transition-colors duration-150 hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e]" },
                  React.createElement(IconLogin, null),
                  React.createElement("span", { className: "hidden sm:inline" }, "Login")
                )
          )
        )
      ),
      React.createElement("div", {
        className: "fixed inset-0 z-[35] bg-black/50 backdrop-blur-[4px] sm:hidden transition-opacity duration-300 ease-out " + (menuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"),
        onClick: function () { setMenuOpen(false); }
      }),
      React.createElement("div", { className: "mobile-drawer fixed top-0 left-0 z-[60] h-[100dvh] w-[82%] max-w-[320px] overflow-y-auto border-r border-[rgba(20,24,30,0.06)] bg-white/95 shadow-[0_8px_32px_rgba(15,20,30,0.08)] backdrop-blur-[16px] p-5 pt-16 sm:hidden transition-transform duration-300 ease-out " + (menuOpen ? "translate-x-0" : "-translate-x-full") },
        React.createElement("nav", { className: "flex flex-col gap-0.5" },
          navItems.map(function (item) {
            const Icon = item.icon;
            return React.createElement("a", {
              key: item.path + "-" + item.label,
              href: encryptedPath(item.path),
              onClick: function () { setMenuOpen(false); },
              className: "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium text-[#5a5c5e] transition-colors hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e]"
            }, React.createElement(Icon, null), React.createElement("span", null, item.label));
          }),
          authed
            ? React.createElement("button", {
                type: "button",
                onClick: function () { setMenuOpen(false); logout(); },
                className: "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium text-[#5a5c5e] transition-colors hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e] mt-2 border-t border-[rgba(20,24,30,0.06)] pt-2"
              }, React.createElement(IconExit, null), t("logout", locale))
            : React.createElement("a", {
                href: encryptedPath("login"),
                onClick: function () { setMenuOpen(false); },
                className: "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium text-[#5a5c5e] transition-colors hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e] mt-2 border-t border-[rgba(20,24,30,0.06)] pt-2"
              }, React.createElement(IconLogin, null), t("login", locale))
        )
      ),
      React.createElement(
        "main",
        { className: "flex-1 w-full min-w-0" },
        children
      ),
      React.createElement(
        "footer",
        { className: "mt-8 border-t border-[rgba(20,24,30,0.06)] pt-4 text-center text-[11px] text-[#8e9094]" },
        "© ",
        React.createElement(
          "span",
          { suppressHydrationWarning: true },
          String(new Date().getFullYear())
        ),
        " SyntexaBR. " + t("rightsReserved", locale) + " ",
        React.createElement("a", { href: encryptedPath("portal"), className: "underline underline-offset-2 hover:text-[#1a1c1e] transition-colors" }, "Portal")
      )
    )
  );
}
