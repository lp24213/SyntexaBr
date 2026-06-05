"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * AnimatedGlowButton — Botão premium com glow elegante
 * @param {Object} props
 * @param {React.ReactNode} props.children - Conteúdo do botão
 * @param {Function} props.onClick - Handler de clique
 * @param {"primary" | "secondary" | "outline"} props.variant - Estilo
 * @param {"sm" | "md" | "lg"} props.size - Tamanho
 * @param {boolean} props.disabled - Desabilitado
 * @param {string} props.className - Classes CSS adicionais
 */
export function AnimatedGlowButton({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled = false,
  className = "",
}) {
  const baseStyles =
    "font-medium transition-all duration-300 relative inline-flex items-center justify-center rounded-lg";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg",
  };

  const variantStyles = {
    primary:
      "bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg hover:shadow-emerald-500/30",
    secondary:
      "bg-slate-900 hover:bg-slate-800 text-white shadow-lg hover:shadow-slate-500/30",
    outline:
      "border border-emerald-500/40 text-emerald-600 hover:border-emerald-500/70 hover:bg-emerald-50/5",
  };

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className} ${
        disabled ? "opacity-50 cursor-not-allowed" : ""
      }`}
    >
      {children}
    </motion.button>
  );
}
