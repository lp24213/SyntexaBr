"use client";

import React from "react";
import { motion } from "framer-motion";

// ─── Neural node component ───────────────────────────────────────────────────
function NeuralNode({ x, y, delay }) {
  return React.createElement(
    motion.div,
    {
      className: "absolute rounded-full",
      style: {
        left: x + "%",
        top: y + "%",
        width: 6,
        height: 6,
        background: "rgba(140,148,160,0.35)",
        boxShadow: "0 0 10px rgba(140,148,160,0.1)",
      },
      initial: { opacity: 0, scale: 0 },
      whileInView: { opacity: 1, scale: 1 },
      viewport: { once: true },
      transition: { duration: 0.5, delay: delay, ease: [0.22, 1, 0.36, 1] },
    }
  );
}

// ─── Animated connection line ────────────────────────────────────────────────
function NeuralConnection({ x1, y1, x2, y2, delay }) {
  var length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
  var angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI);
  return React.createElement(
    motion.div,
    {
      className: "absolute origin-left",
      style: {
        left: x1 + "%",
        top: y1 + "%",
        width: length + "%",
        height: 1,
        background: "linear-gradient(90deg, rgba(140,148,160,0.15), rgba(140,148,160,0.02))",
        transform: "rotate(" + angle + "deg)",
      },
      initial: { scaleX: 0 },
      whileInView: { scaleX: 1 },
      viewport: { once: true },
      transition: { duration: 0.8, delay: delay, ease: [0.22, 1, 0.36, 1] },
    }
  );
}

// ─── Inference chain item ────────────────────────────────────────────────────
function InferenceChainItem({ step, label, desc, delay }) {
  return React.createElement(
    motion.div,
    {
      className: "relative flex items-start gap-4",
      initial: { opacity: 0, x: -16 },
      whileInView: { opacity: 1, x: 0 },
      viewport: { once: true },
      transition: { duration: 0.45, delay: delay },
    },
    React.createElement("div", {
      className: "mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[rgba(20,24,30,0.08)] bg-white text-[11px] font-semibold text-[#8e9094]",
    }, step),
    React.createElement("div", null,
      React.createElement("p", { className: "text-sm font-medium text-[#1a1c1e]" }, label),
      React.createElement("p", { className: "text-xs text-[#8e9094] leading-relaxed" }, desc)
    )
  );
}

// ─── Quantum LLM Core Section ────────────────────────────────────────────────
export function QuantumLLMCore({ locale, t }) {
  var nodes = [
    { x: 20, y: 25 }, { x: 35, y: 15 }, { x: 50, y: 28 },
    { x: 65, y: 12 }, { x: 80, y: 22 }, { x: 25, y: 50 },
    { x: 45, y: 55 }, { x: 60, y: 45 }, { x: 75, y: 52 },
    { x: 30, y: 75 }, { x: 55, y: 70 }, { x: 70, y: 78 },
  ];

  var connections = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 5], [1, 5], [2, 6], [3, 6], [4, 7],
    [5, 8], [6, 8], [7, 8],
    [5, 9], [6, 10], [8, 11], [9, 10], [10, 11],
  ];

  var chains = [
    { step: "01", label: t("llmStep1", locale), desc: t("llmStep1Desc", locale) },
    { step: "02", label: t("llmStep2", locale), desc: t("llmStep2Desc", locale) },
    { step: "03", label: t("llmStep3", locale), desc: t("llmStep3Desc", locale) },
    { step: "04", label: t("llmStep4", locale), desc: t("llmStep4Desc", locale) },
    { step: "05", label: t("llmStep5", locale), desc: t("llmStep5Desc", locale) },
  ];

  return React.createElement(
    "section",
    { id: "quantum-core", className: "relative mt-8 scroll-mt-24 overflow-hidden rounded-[20px] border border-[rgba(20,24,30,0.06)] bg-white p-7 md:p-10" },

    // Header
    React.createElement(
      motion.div,
      {
        className: "mb-8",
        initial: { opacity: 0, y: 12 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true },
        transition: { duration: 0.5 },
      },
      React.createElement("p", { className: "mb-2 inline-flex rounded-full border border-[rgba(20,24,30,0.08)] bg-[#fafbfc] px-3 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-[#8e9094]" },
        t("llmBadge", locale)
      ),
      React.createElement("h2", { className: "text-[1.5rem] font-semibold tracking-tight text-[#1a1c1e] md:text-[1.75rem]" },
        t("llmTitle", locale)
      ),
      React.createElement("p", { className: "mt-2 max-w-2xl text-[15px] leading-relaxed text-[#5a5c5e]" },
        t("llmLead", locale)
      )
    ),

    // Content: Neural graph + Inference chain
    React.createElement("div", { className: "grid gap-8 lg:grid-cols-2" },

      // Left: Neural topology visualization
      React.createElement(
        "div",
        { className: "relative h-[340px] overflow-hidden rounded-2xl border border-[rgba(20,24,30,0.05)] bg-[#fafbfc]" },
        // Ambient radial glow
        React.createElement("div", {
          className: "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
          style: {
            width: 280, height: 280,
            background: "radial-gradient(circle, rgba(200,210,225,0.12) 0%, transparent 70%)",
            borderRadius: "50%",
          },
        }),
        // Nodes
        nodes.map(function (n, i) {
          return React.createElement(NeuralNode, { key: i, x: n.x, y: n.y, delay: 0.05 * i });
        }),
        // Connections
        connections.map(function (c, i) {
          var a = nodes[c[0]];
          var b = nodes[c[1]];
          return React.createElement(NeuralConnection, { key: i, x1: a.x, y1: a.y, x2: b.x, y2: b.y, delay: 0.04 * i });
        }),
        // Labels
        React.createElement("div", { className: "absolute bottom-3 left-4 text-[10px] font-mono text-[#8e9094]" }, "neural_topology.v7")
      ),

      // Right: Inference chain
      React.createElement("div", { className: "flex flex-col gap-5" },
        chains.map(function (c, i) {
          return React.createElement(InferenceChainItem, {
            key: i,
            step: c.step,
            label: c.label,
            desc: c.desc,
            delay: 0.08 * i,
          });
        })
      )
    )
  );
}
