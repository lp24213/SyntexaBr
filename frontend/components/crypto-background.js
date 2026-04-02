"use client";

import React from "react";
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
      className: "flex flex-col gap-0 font-mono text-[11px] leading-none text-white",
      style: { opacity: 0.05 + (i % 4) * 0.015 },
      initial: { y: "-100%" },
      animate: { y: "100vh" },
      transition: { duration, repeat: Infinity, repeatDelay: 0 },
    },
    chars.map(function (c, j) {
      return React.createElement("span", { key: i + "-" + j, className: "inline-block" }, c);
    })
  );
}

export function CryptoBackground() {
  return React.createElement(
    "div",
    {
      className: "pointer-events-none fixed inset-0 z-0 overflow-hidden bg-[#02030a]",
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
      style: {
        background:
          "radial-gradient(ellipse 90% 60% at 50% 0%, rgba(226,232,240,0.08) 0%, transparent 55%)," +
          "linear-gradient(to bottom, rgba(15,23,42,0.4), transparent 40%, rgba(3,7,18,0.9))",
      },
    })
  );
}
