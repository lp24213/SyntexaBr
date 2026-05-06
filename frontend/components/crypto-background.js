"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

const CHARS = "01{}[]();=<>@#&*%$§|/\\~^+-:.,ABCDEFabcdef0123456789";
const COLS = 16;
const ROWS = 24;

function pick() {
  return CHARS[Math.floor(Math.random() * CHARS.length)];
}

function Column(props) {
  const { i } = props;
  const chars = Array.from({ length: ROWS }, pick);
  const duration = 20 + (i % 5) * 3;
  return React.createElement(
    motion.div,
    {
      className: "flex flex-col gap-0 font-mono text-[11px] leading-none text-slate-500",
      style: { opacity: 0.06 + (i % 4) * 0.02 },
      initial: { y: "-100%" },
      animate: { y: "100vh" },
      transition: { duration, repeat: Infinity, repeatDelay: 0 },
    },
    chars.map(function (c, j) {
      return React.createElement("span", { key: i + "-" + j, className: "inline-block" }, c);
    })
  );
}

const overlayStyle = {
  background:
    "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(159,184,222,0.12) 0%, transparent 50%)," +
    "linear-gradient(to bottom, rgba(248,249,251,0.95), rgba(241,245,249,0.98))",
};

/**
 * O “rain” usa Math.random() por célula; isso quebra hidratação (HTML estático ≠ cliente).
 * Primeiro paint: só o gradiente (SSR = cliente); depois do mount, animação — sem React #418.
 */
export function CryptoBackground() {
  const [mounted, setMounted] = useState(false);
  useEffect(function () {
    setMounted(true);
  }, []);

  if (!mounted) {
    return React.createElement(
      "div",
      {
        className: "pointer-events-none fixed inset-0 z-0 overflow-hidden bg-[#f8f9fb]",
        "aria-hidden": true,
      },
      React.createElement("div", {
        className: "absolute inset-0",
        style: overlayStyle,
      })
    );
  }

  return React.createElement(
    "div",
    {
      className: "pointer-events-none fixed inset-0 z-0 overflow-hidden bg-[#f8f9fb]",
      "aria-hidden": true,
    },
    React.createElement(
      "div",
      { className: "absolute inset-0 flex justify-evenly gap-0" },
      Array.from({ length: COLS }, function (_, i) {
        return React.createElement(Column, { key: i, i: i });
      })
    ),
    React.createElement("div", {
      className: "absolute inset-0",
      style: overlayStyle,
    })
  );
}
