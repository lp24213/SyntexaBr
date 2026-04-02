"use client";

import React from "react";

/**
 * Logo Syntexa em SVG — ícone S + wordmark, identidade Syntexa, visual futurista.
 * Substitui a img do LOGOTIPO.png por vetor nítido em qualquer tamanho.
 */
export function Brand(props) {
  const { className, alt } = props;
  const cn =
    "object-contain object-left " +
    (className || "h-24 w-[320px] sm:h-28 sm:w-[420px]");

  return React.createElement(
    "svg",
    {
      className: cn,
      viewBox: "0 0 240 48",
      fill: "none",
      xmlns: "http://www.w3.org/2000/svg",
      "aria-label": alt || "Syntexa",
      role: "img",
    },
    React.createElement("defs", null, [
      React.createElement(
        "radialGradient",
        {
          id: "syntexa-glow",
          cx: "0",
          cy: "0",
          r: "1",
          gradientUnits: "userSpaceOnUse",
          gradientTransform: "scale(20) translate(4 2)",
        },
        React.createElement("stop", { stopColor: "currentColor", stopOpacity: "0.25" }),
        React.createElement("stop", { offset: "1", stopColor: "currentColor", stopOpacity: "0" })
      ),
    ]),
    // Glow atrás do ícone
    React.createElement("ellipse", {
      cx: "28",
      cy: "24",
      rx: "14",
      ry: "16",
      fill: "url(#syntexa-glow)",
    }),
    // Ícone: S estilizado (identidade Syntexa)
    React.createElement("path", {
      d: "M24 10c4 0 8 2 8 6s-3 6-8 8c-4 2-8 4-8 8s3 6 8 6",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      fill: "none",
      className: "text-white",
    }),
    // Wordmark "Syntexa"
    React.createElement(
      "text",
      {
        x: "52",
        y: "32",
        fill: "currentColor",
        style: {
          fontFamily: "system-ui, -apple-system, 'SF Pro Display', 'Segoe UI', sans-serif",
          fontSize: "26px",
          fontWeight: 600,
          letterSpacing: "-0.02em",
        },
      },
      "Syntexa"
    )
  );
}
