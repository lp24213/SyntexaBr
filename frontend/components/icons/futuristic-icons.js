/**
 * Syntexa SVG Icon System — minimal, thin-line, enterprise-grade.
 * Uso: FuturisticIcon({ name: "atom", className: "h-4 w-4 text-[#8e9094]" })
 */
import React from "react";

function S(props, children) {
  return React.createElement(
    "svg",
    {
      viewBox: "0 0 24 24",
      fill: "none",
      xmlns: "http://www.w3.org/2000/svg",
      stroke: "currentColor",
      strokeWidth: "1.35",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      "aria-hidden": "true",
      ...props,
    },
    children
  );
}

const DEF = { className: "h-4 w-4 shrink-0 text-[#8e9094]" };

export function FuturisticIcon(opts) {
  var name = (opts && opts.name) || "spark";
  var cn = (opts && opts.className) || DEF.className;
  var fn = ICON_MAP[name] || ICON_MAP.spark;
  return fn({ className: cn });
}

var ICON_MAP = {
  spark: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 3v3M12 18v3M3 12h3M18 12h3" }),
      React.createElement("path", { d: "M7 7l1.5 1.5M15.5 15.5L17 17M17 7l-1.5 1.5M7 17l1.5-1.5" }),
      React.createElement("circle", { cx: "12", cy: "12", r: "3" })
    );
  },
  book: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M6 4h5a3 3 0 013 3v14a3 3 0 00-3-3H6V4z" }),
      React.createElement("path", { d: "M18 4h-5a3 3 0 00-3 3v14a3 3 0 013-3h5V4z" })
    );
  },
  flask: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M9 3h6M10 3v5l-4 9a2 2 0 002 2h8a2 2 0 002-2l-4-9V3" }),
      React.createElement("path", { d: "M8 14h8" })
    );
  },
  atom: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "12", r: "1.5", fill: "currentColor", stroke: "none" }),
      React.createElement("ellipse", { cx: "12", cy: "12", rx: "9", ry: "4", transform: "rotate(0 12 12)" }),
      React.createElement("ellipse", { cx: "12", cy: "12", rx: "9", ry: "4", transform: "rotate(60 12 12)" }),
      React.createElement("ellipse", { cx: "12", cy: "12", rx: "9", ry: "4", transform: "rotate(120 12 12)" })
    );
  },
  telescope: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M3 21l4-4M7 17l10-10 4 4-10 10-4-4z" }),
      React.createElement("path", { d: "M14 7l3-3 4 4-3 3" }),
      React.createElement("path", { d: "M5 14L3 21l7-2" })
    );
  },
  code: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M9 7l-4 5 4 5M15 7l4 5-4 5" }),
      React.createElement("path", { d: "M13 5l-2 14" })
    );
  },
  gear: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "12", r: "3" }),
      React.createElement("path", { d: "M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" })
    );
  },
  sigma: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M6 7l4 10M18 7l-4 10M8 12h8" })
    );
  },
  integral: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M8 5c-2 4-2 10 0 14M16 5c2 4 2 10 0 14" }),
      React.createElement("path", { d: "M11 9h4M11 15h4" })
    );
  },
  brain: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M9.5 4a3.5 3.5 0 00-2 6.5 3.5 3.5 0 002 6.5M14.5 4a3.5 3.5 0 012 6.5 3.5 3.5 0 01-2 6.5" }),
      React.createElement("path", { d: "M12 4v3M12 17v3M8 8h2M14 8h2M8 16h2M14 16h2" })
    );
  },
  lock: function (p) {
    return S(
      { ...p },
      React.createElement("rect", { x: "5", y: "11", width: "14", height: "10", rx: "2" }),
      React.createElement("path", { d: "M8 11V8a4 4 0 018 0v3" })
    );
  },
  dna: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M7 4c2 2 2 4 0 6s-2 4 0 6M17 4c-2 2-2 4 0 6s2 4 0 6" }),
      React.createElement("path", { d: "M9 8h6M9 16h6M10 6l4 12" })
    );
  },
  cross: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 4v16M8 8h8M8 16h8" }),
      React.createElement("circle", { cx: "12", cy: "12", r: "8" })
    );
  },
  scroll: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M8 4h8a2 2 0 012 2v14H6V6a2 2 0 012-2z" }),
      React.createElement("path", { d: "M8 8h8M8 12h6" })
    );
  },
  chart: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 20V4M4 20h16" }),
      React.createElement("path", { d: "M8 16l3-6 3 4 4-9" })
    );
  },
  scale: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 3v18M5 7l7-4 7 4M5 17l7 4 7-4" }),
      React.createElement("circle", { cx: "12", cy: "12", r: "2" })
    );
  },
  globe: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "12", r: "9" }),
      React.createElement("path", { d: "M3 12h18M12 3a15 15 0 000 18M12 3a15 15 0 010 18" })
    );
  },
  chat: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2h-6l-4 4v-4H6a2 2 0 01-2-2V6z" }),
      React.createElement("path", { d: "M8 9h8M8 12h5" })
    );
  },
  pencil: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 20l4-1 11-11-3-3L5 16l-1 4z" }),
      React.createElement("path", { d: "M13 6l5 5" })
    );
  },
  clipboard: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M9 4h6l1 2h3v14H5V6h3l1-2z" }),
      React.createElement("path", { d: "M9 12h6M9 16h4" })
    );
  },
  microscope: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M6 18h12M9 18V9l-2-2M15 18V9l2-2" }),
      React.createElement("circle", { cx: "12", cy: "5", r: "2" }),
      React.createElement("path", { d: "M12 7v2" })
    );
  },
  building: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 21V8l8-4 8 4v13" }),
      React.createElement("path", { d: "M9 21v-6h6v6M9 13h6" })
    );
  },
  medal: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "9", r: "5" }),
      React.createElement("path", { d: "M8 14l-2 7 6-3 6 3-2-7" })
    );
  },
  download: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 4v10M8 10l4 4 4-4" }),
      React.createElement("path", { d: "M4 18h16" })
    );
  },
  map: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 6l6-2 4 2 6-2v14l-6 2-4-2-6 2V6z" }),
      React.createElement("path", { d: "M10 4v14M14 6v12" })
    );
  },
  userTie: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "7", r: "3" }),
      React.createElement("path", { d: "M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2M12 11v3" })
    );
  },
  shield: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 3l8 4v6c0 5-3.5 9-8 10-4.5-1-8-5-8-10V7l8-4z" }),
      React.createElement("path", { d: "M9 12l2 2 4-4" })
    );
  },
  crystal: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 2l9 6-3 14H6L3 8l9-6z" }),
      React.createElement("path", { d: "M12 2v20M3 8h18" })
    );
  },
  wave: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M2 12c2-2 4-2 6 0s4 2 6 0 4-2 6 0 4 2 6 0" }),
      React.createElement("path", { d: "M2 16c2-2 4-2 6 0s4 2 6 0 4-2 6 0 4 2 6 0" })
    );
  },
  bolt: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M13 2L4 14h7l-1 8 10-12h-7l1-8z" })
    );
  },
  hex: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M8 4h8l4 6-4 6H8L4 10l4-6z" })
    );
  },
  grid: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" })
    );
  },
  plus: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 5v14M5 12h14" })
    );
  },
  check: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M5 12l4 4L19 6" })
    );
  },
  trash: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 7h16M10 11v6M14 11v6M6 7l1 12h10l1-12M9 7V5h6v2" })
    );
  },
  key: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "8", cy: "8", r: "3" }),
      React.createElement("path", { d: "M10.5 10.5L20 20M14 14l2 2" })
    );
  },
  doc: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M6 3h8l4 4v14H6z" }),
      React.createElement("path", { d: "M9 12h6M9 16h4" })
    );
  },
  cpu: function (p) {
    return S(
      { ...p },
      React.createElement("rect", { x: "7", y: "7", width: "10", height: "10", rx: "1" }),
      React.createElement("path", { d: "M7 10H4M7 14H4M20 10h-3M20 14h-3M10 7V4M14 7V4M10 20v-3M14 20v-3" })
    );
  },
  quantum: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "12", r: "2", fill: "currentColor", stroke: "none" }),
      React.createElement("path", { d: "M12 2v4M12 18v4M2 12h4M18 12h4" }),
      React.createElement("path", { d: "M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" })
    );
  },
  rocket: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 3c4 4 5 10 3 14l-3 4-3-4c-2-4-1-10 3-14z" }),
      React.createElement("path", { d: "M9 17H6M18 17h-3M12 11v3" })
    );
  },
  orbit: function (p) {
    return S(
      { ...p },
      React.createElement("ellipse", { cx: "12", cy: "12", rx: "9", ry: "4" }),
      React.createElement("circle", { cx: "18", cy: "12", r: "1.5", fill: "currentColor", stroke: "none" })
    );
  },
  admin: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 2L4 6v6c0 5 3.5 9 8 10 4.5-1 8-5 8-10V6l-8-4z" }),
      React.createElement("path", { d: "M9 12l2 2 4-4" })
    );
  },
  online: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "12", r: "6", fill: "currentColor", fillOpacity: "0.2", stroke: "currentColor" }),
      React.createElement("circle", { cx: "12", cy: "12", r: "2.5", fill: "currentColor", stroke: "none" })
    );
  },
  ban: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "12", r: "8" }),
      React.createElement("path", { d: "M5 5l14 14" })
    );
  },
  refresh: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M21 12a9 9 0 11-3-7" }),
      React.createElement("path", { d: "M21 3v6h-6" })
    );
  },
  warn: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M12 3l10 18H2L12 3z" }),
      React.createElement("path", { d: "M12 9v4M12 17h.01" })
    );
  },
  home: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M3 10.5L12 3l9 7.5V21a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1v-10.5z" })
    );
  },
  stop: function (p) {
    return S(
      { ...p },
      React.createElement("rect", { x: "7", y: "7", width: "10", height: "10", rx: "1.5" })
    );
  },
  users: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "9", cy: "8", r: "3" }),
      React.createElement("path", { d: "M3 20v-1a4 4 0 014-4h2M17 11a3 3 0 100-6 3 3 0 000 6zM21 20v-1a4 4 0 00-3-3.87" })
    );
  },
  calendar: function (p) {
    return S(
      { ...p },
      React.createElement("rect", { x: "4", y: "5", width: "16", height: "15", rx: "2" }),
      React.createElement("path", { d: "M8 3v4M16 3v4M4 11h16" })
    );
  },
  lightbulb: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M9 18h6M10 22h4M12 2a5 5 0 00-3 9v2h6v-2a5 5 0 00-3-9z" })
    );
  },
  search: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "11", cy: "11", r: "6" }),
      React.createElement("path", { d: "M20 20l-3-3" })
    );
  },
  ruler: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 20L20 4M8 4h2M6 6h2M8 8h2M6 10h2M8 12h2M6 14h2M8 16h2M6 18h2" })
    );
  },
  predict: function (p) {
    return S(
      { ...p },
      React.createElement("circle", { cx: "12", cy: "12", r: "8" }),
      React.createElement("path", { d: "M12 8v3l2 2M9 5l1.5 1.5M15 5l-1.5 1.5" })
    );
  },
  pen: function (p) {
    return S(
      { ...p },
      React.createElement("path", { d: "M4 20l8-8 4-10 2 2-10 4-8 8v2h2z" }),
      React.createElement("path", { d: "M13 6l5 5" })
    );
  },
};
