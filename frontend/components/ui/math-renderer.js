"use client";

/**
 * MathRenderer — renderiza fórmulas LaTeX usando KaTeX (carregado via CDN).
 *
 * Uso:
 *   <MathRenderer text="A solução é $x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$" />
 *
 * Detecta automaticamente:
 *   $$...$$  →  bloco de equação (display)
 *   $...$    →  fórmula inline
 *   ```math  →  bloco de código math
 */

import React, { useEffect, useRef, useState } from "react";

const KATEX_CSS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css";
const KATEX_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js";

let katexPromise = null;

function loadKaTeX() {
  if (katexPromise) return katexPromise;
  katexPromise = new Promise((resolve) => {
    if (typeof window === "undefined") { resolve(null); return; }
    if (window.katex) { resolve(window.katex); return; }

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = KATEX_CSS;
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src = KATEX_JS;
    script.onload = () => resolve(window.katex);
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
  return katexPromise;
}

// ─── Unicode symbol fallback map (used when KaTeX hasn't loaded yet) ──────────
const SYMBOL_MAP = {
  "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\delta": "δ",
  "\\epsilon": "ε", "\\varepsilon": "ε", "\\zeta": "ζ", "\\eta": "η",
  "\\theta": "θ", "\\iota": "ι", "\\kappa": "κ", "\\lambda": "λ",
  "\\mu": "μ", "\\nu": "ν", "\\xi": "ξ", "\\pi": "π",
  "\\rho": "ρ", "\\sigma": "σ", "\\tau": "τ", "\\upsilon": "υ",
  "\\phi": "φ", "\\varphi": "φ", "\\chi": "χ", "\\psi": "ψ", "\\omega": "ω",
  "\\Gamma": "Γ", "\\Delta": "Δ", "\\Theta": "Θ", "\\Lambda": "Λ",
  "\\Xi": "Ξ", "\\Pi": "Π", "\\Sigma": "Σ", "\\Upsilon": "Υ",
  "\\Phi": "Φ", "\\Psi": "Ψ", "\\Omega": "Ω",
  "\\infty": "∞", "\\partial": "∂", "\\nabla": "∇",
  "\\sum": "∑", "\\prod": "∏", "\\int": "∫", "\\oint": "∮",
  "\\sqrt": "√", "\\pm": "±", "\\mp": "∓", "\\times": "×", "\\div": "÷",
  "\\leq": "≤", "\\geq": "≥", "\\neq": "≠", "\\approx": "≈",
  "\\equiv": "≡", "\\sim": "∼", "\\propto": "∝",
  "\\in": "∈", "\\notin": "∉", "\\subset": "⊂", "\\supset": "⊃",
  "\\cup": "∪", "\\cap": "∩", "\\emptyset": "∅",
  "\\forall": "∀", "\\exists": "∃", "\\nexists": "∄",
  "\\to": "→", "\\rightarrow": "→", "\\leftarrow": "←", "\\Rightarrow": "⇒",
  "\\Leftarrow": "⇐", "\\Leftrightarrow": "⇔", "\\leftrightarrow": "↔",
  "\\cdot": "·", "\\ldots": "…", "\\cdots": "⋯",
  "\\langle": "⟨", "\\rangle": "⟩",
  "\\hat": "^", "\\bar": "̄", "\\vec": "⃗",
};

function unicodeFallback(latex) {
  let s = latex.trim();
  for (const [cmd, unicode] of Object.entries(SYMBOL_MAP)) {
    s = s.replaceAll(cmd, unicode);
  }
  s = s.replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, "($1)/($2)");
  s = s.replace(/\\sqrt\{([^}]*)\}/g, "√($1)");
  s = s.replace(/\^(\{[^}]*\}|\S)/g, (_, e) => "^" + e.replace(/[{}]/g, ""));
  s = s.replace(/_(\{[^}]*\}|\S)/g, (_, e) => "₋" + e.replace(/[{}]/g, ""));
  s = s.replace(/[{}\\]/g, "");
  return s;
}

// ─── Render a single math string ──────────────────────────────────────────────
function renderMath(katex, latex, displayMode) {
  if (!katex) return unicodeFallback(latex);
  try {
    return katex.renderToString(latex, {
      displayMode,
      throwOnError: false,
      output: "html",
    });
  } catch {
    return unicodeFallback(latex);
  }
}

// ─── Split text into segments: plain | math-inline | math-display ────────────
function parseSegments(text) {
  const segments = [];
  // Match $$...$$ (display) and $...$ (inline)
  const re = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) segments.push({ type: "text", content: text.slice(last, m.index) });
    const raw = m[0];
    if (raw.startsWith("$$")) {
      segments.push({ type: "display", content: raw.slice(2, -2).trim() });
    } else {
      segments.push({ type: "inline", content: raw.slice(1, -1).trim() });
    }
    last = m.index + raw.length;
  }
  if (last < text.length) segments.push({ type: "text", content: text.slice(last) });
  return segments;
}

// ─── Rendered segment component ──────────────────────────────────────────────
function MathSegment({ katex, segment }) {
  if (segment.type === "text") {
    return React.createElement("span", null, segment.content);
  }
  const html = renderMath(katex, segment.content, segment.type === "display");
  if (segment.type === "display") {
    return React.createElement("span", {
      className: "my-2 block overflow-x-auto rounded-xl border border-violet-500/20 bg-violet-500/6 px-4 py-2 text-center",
      dangerouslySetInnerHTML: { __html: html },
    });
  }
  return React.createElement("span", {
    className: "rounded px-0.5 font-mono text-violet-200",
    dangerouslySetInnerHTML: { __html: html },
  });
}

// ─── Main component ──────────────────────────────────────────────────────────
export default function MathRenderer({ text, className }) {
  const [katex, setKaTeX] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadKaTeX().then((k) => { if (!cancelled) setKaTeX(k); });
    return () => { cancelled = true; };
  }, []);

  if (!text) return null;
  const segments = parseSegments(text);
  const hasMath = segments.some((s) => s.type !== "text");

  if (!hasMath) {
    return React.createElement("span", { className }, text);
  }

  return React.createElement(
    "span",
    { className },
    ...segments.map((seg, i) =>
      React.createElement(MathSegment, { key: i, katex, segment: seg })
    )
  );
}

/**
 * MathText — renderizes an entire block (paragraphs) with LaTeX support.
 * Better for multi-line AI responses.
 */
export function MathText({ text, className }) {
  const [katex, setKaTeX] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadKaTeX().then((k) => { if (!cancelled) setKaTeX(k); });
    return () => { cancelled = true; };
  }, []);

  if (!text) return null;
  const lines = text.split("\n");

  const rendered = lines.map((line, li) => {
    if (!line.trim()) return React.createElement("br", { key: li });
    const segs = parseSegments(line);
    const hasMath = segs.some((s) => s.type !== "text");
    if (!hasMath) return React.createElement("span", { key: li }, line, React.createElement("br", null));
    return React.createElement(
      "span",
      { key: li },
      ...segs.map((seg, si) => React.createElement(MathSegment, { key: si, katex, segment: seg })),
      React.createElement("br", null)
    );
  });

  return React.createElement("span", { className }, ...rendered);
}
