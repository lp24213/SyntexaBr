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

function IconLanguage() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("circle", { cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "1.5" }),
    React.createElement("path", { d: "M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z", stroke: "currentColor", strokeWidth: "1.5" })
  );
}

function FlagBR() {
  return React.createElement(
    "svg",
    { className: "h-4 w-6 rounded-sm", viewBox: "0 0 900 600", fill: "none" },
    React.createElement("rect", { width: "900", height: "600", fill: "#002776" }),
    React.createElement("polygon", { points: "450,0 900,300 450,600 0,300", fill: "#FECB2F" }),
    React.createElement("ellipse", { cx: "450", cy: "300", rx: "150", ry: "100", fill: "#002776" }),
    React.createElement("text", { x: "450", y: "320", fontSize: "80", fill: "#FECB2F", textAnchor: "middle", fontWeight: "bold" }, "BRASIL")
  );
}

function FlagUS() {
  return React.createElement(
    "svg",
    { className: "h-4 w-6 rounded-sm", viewBox: "0 0 900 600", fill: "none" },
    React.createElement("rect", { width: "900", height: "600", fill: "#B22234" }),
    React.createElement("rect", { y: "0", width: "900", height: "46", fill: "#FFFFFF" }),
    React.createElement("rect", { y: "92", width: "900", height: "46", fill: "#FFFFFF" }),
    React.createElement("rect", { y: "184", width: "900", height: "46", fill: "#FFFFFF" }),
    React.createElement("rect", { y: "276", width: "900", height: "46", fill: "#FFFFFF" }),
    React.createElement("rect", { y: "368", width: "900", height: "46", fill: "#FFFFFF" }),
    React.createElement("rect", { y: "460", width: "900", height: "46", fill: "#FFFFFF" }),
    React.createElement("rect", { y: "552", width: "900", height: "46", fill: "#FFFFFF" }),
    React.createElement("rect", { x: "0", y: "0", width: "360", height: "280", fill: "#3C3B6B" })
  );
}

function FlagES() {
  return React.createElement(
    "svg",
    { className: "h-4 w-6 rounded-sm", viewBox: "0 0 900 600", fill: "none" },
    React.createElement("rect", { y: "0", width: "900", height: "150", fill: "#FFC400" }),
    React.createElement("rect", { y: "150", width: "900", height: "300", fill: "#C60B1E" }),
    React.createElement("rect", { y: "450", width: "900", height: "150", fill: "#FFC400" })
  );
}

function FlagCN() {
  return React.createElement(
    "svg",
    { className: "h-4 w-6 rounded-sm", viewBox: "0 0 900 600", fill: "none" },
    React.createElement("rect", { width: "900", height: "600", fill: "#DE2910" }),
    React.createElement("polygon", { points: "200,100 250,150 210,160 240,190 200,190", fill: "#FFDE00" }),
    React.createElement("polygon", { points: "310,120 350,160 315,170 345,195 310,195", fill: "#FFDE00" }),
    React.createElement("polygon", { points: "380,140 410,170 375,175 405,200 375,200", fill: "#FFDE00" }),
    React.createElement("polygon", { points: "330,220 360,250 330,255 360,280 330,280", fill: "#FFDE00" }),
    React.createElement("polygon", { points: "240,250 270,280 240,285 270,310 240,310", fill: "#FFDE00" })
  );
}

function IconExit() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })
  );
}

function IconWhatsApp() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M3 21l1.65-3.8a9 9 0 1115.35-8.5 9 9 0 01-15.35 8.5L3 21z", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M9.5 9.5c.5-.5 1.2-.8 2-.8 1.5 0 2.5 1 2.5 2.5M9.5 13.5c.5.5 1.2.8 2 .8 1.5 0 2.5-1 2.5-2.5", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" })
  );
}

function IconTikTok() {
  return React.createElement(
    "svg",
    { className: "h-[15px] w-[15px] text-[#5a5c5e]", viewBox: "0 0 24 24", fill: "currentColor" },
    React.createElement("path", { d: "M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.1 1.82 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-.95-.1z" })
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
  whatsapp: IconWhatsApp,
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

  const currentLocale = getClientLocale();
  var navItems = [
    { path: `/i18n/${currentLocale}/`, labelKey: "navHome", icon: IconGlobe },
    { path: `/i18n/${currentLocale}/plans`, labelKey: "plans", icon: IconChart },
    { path: `/i18n/${currentLocale}/chat`, labelKey: "chat", icon: IconChat },
    { path: `/i18n/${currentLocale}/integrations`, labelKey: "integrations", icon: IconWhatsApp },
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
              const label = t(item.labelKey, currentLocale);
              return React.createElement(
                "a",
                {
                  key: href + "-" + item.labelKey,
                  href: href,
                  className:
                    "rounded-lg px-3 py-1.5 text-[13px] text-[#64748b] transition-colors duration-200 hover:bg-[rgba(15,23,42,0.04)] hover:text-[#0f172a]",
                },
                label
              );
            })
          ),
          React.createElement("div", { className: "flex items-center gap-3 min-w-0 flex-1 justify-end" },
            React.createElement("div", { className: "relative group" },
              React.createElement("button", {
                className: "flex items-center gap-1.5 rounded-lg border border-[rgba(15,23,42,0.08)] px-2 py-1.5 hover:bg-[rgba(20,24,30,0.04)] transition-colors",
                title: "Mudar idioma",
              },
                React.createElement(IconLanguage, null)
              ),
              React.createElement("div", { className: "absolute right-0 mt-1 hidden group-hover:flex flex-col bg-white border border-[rgba(15,23,42,0.08)] rounded-lg shadow-lg z-50 min-w-[120px]" },
                React.createElement("button", {
                  onClick: function() {
                    const newLocale = "pt-BR";
                    window.localStorage.setItem("syntexa_locale", newLocale);
                    var currentPath = window.location.pathname;
                    var newPath = currentPath.replace(/^\/i18n\/[^\/]+/, "/i18n/" + newLocale);
                    window.location.pathname = newPath;
                  },
                  className: "flex items-center gap-2 px-3 py-2 text-[13px] hover:bg-[rgba(15,23,42,0.04)] border-b border-[rgba(15,23,42,0.04)]",
                },
                  React.createElement(FlagBR, null),
                  React.createElement("span", {}, "Português")
                ),
                React.createElement("button", {
                  onClick: function() {
                    const newLocale = "en-US";
                    window.localStorage.setItem("syntexa_locale", newLocale);
                    var currentPath = window.location.pathname;
                    var newPath = currentPath.replace(/^\/i18n\/[^\/]+/, "/i18n/" + newLocale);
                    window.location.pathname = newPath;
                  },
                  className: "flex items-center gap-2 px-3 py-2 text-[13px] hover:bg-[rgba(15,23,42,0.04)] border-b border-[rgba(15,23,42,0.04)]",
                },
                  React.createElement(FlagUS, null),
                  React.createElement("span", {}, "English")
                ),
                React.createElement("button", {
                  onClick: function() {
                    const newLocale = "es-ES";
                    window.localStorage.setItem("syntexa_locale", newLocale);
                    var currentPath = window.location.pathname;
                    var newPath = currentPath.replace(/^\/i18n\/[^\/]+/, "/i18n/" + newLocale);
                    window.location.pathname = newPath;
                  },
                  className: "flex items-center gap-2 px-3 py-2 text-[13px] hover:bg-[rgba(15,23,42,0.04)] border-b border-[rgba(15,23,42,0.04)]",
                },
                  React.createElement(FlagES, null),
                  React.createElement("span", {}, "Español")
                ),
                React.createElement("button", {
                  onClick: function() {
                    const newLocale = "zh-CN";
                    window.localStorage.setItem("syntexa_locale", newLocale);
                    var currentPath = window.location.pathname;
                    var newPath = currentPath.replace(/^\/i18n\/[^\/]+/, "/i18n/" + newLocale);
                    window.location.pathname = newPath;
                  },
                  className: "flex items-center gap-2 px-3 py-2 text-[13px] hover:bg-[rgba(15,23,42,0.04)]",
                },
                  React.createElement(FlagCN, null),
                  React.createElement("span", {}, "中文")
                )
              )
            ),
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
            const label = t(item.labelKey, currentLocale);
            return React.createElement("a", {
              key: item.path + "-" + item.labelKey,
              href: encryptedPath(item.path),
              onClick: function () { setMenuOpen(false); },
              className: "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium text-[#5a5c5e] transition-colors hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e]"
            }, React.createElement(Icon, null), React.createElement("span", null, label));
          }),
          authed
            ? React.createElement("button", {
                type: "button",
                onClick: function () { setMenuOpen(false); logout(); },
                className: "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium text-[#5a5c5e] transition-colors hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e] mt-2 border-t border-[rgba(20,24,30,0.06)] pt-2"
              }, React.createElement(IconExit, null), t("logout", currentLocale))
            : React.createElement("a", {
                href: encryptedPath("login"),
                onClick: function () { setMenuOpen(false); },
                className: "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium text-[#5a5c5e] transition-colors hover:bg-[rgba(20,24,30,0.04)] hover:text-[#1a1c1e] mt-2 border-t border-[rgba(20,24,30,0.06)] pt-2"
              }, React.createElement(IconLogin, null), t("login", currentLocale))
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
