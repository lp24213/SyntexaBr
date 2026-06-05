"use client";

import React from "react";

/**
 * NeonDivider — Divisor elegante com gradiente sutil
 * @param {Object} props
 * @param {"subtle" | "medium" | "prominent"} props.variant - Intensidade
 * @param {string} props.className - Classes CSS adicionais
 */
export function NeonDivider({ variant = "subtle", className = "" }) {
  const variantStyles = {
    subtle:
      "h-px bg-gradient-to-r from-transparent via-emerald-500/10 to-transparent",
    medium:
      "h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent shadow-lg shadow-emerald-500/10",
    prominent:
      "h-[2px] bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent shadow-lg shadow-emerald-500/20",
  };

  return (
    <div
      className={`${variantStyles[variant]} my-8 ${className}`}
      role="separator"
      aria-label="Divisor decorativo"
    />
  );
}
