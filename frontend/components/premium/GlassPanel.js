"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * GlassPanel — Painel com glassmorphism leve, bordas luminosas e animações
 * Padrão: Anthropic, Modern UI
 */
export function GlassPanel({
  children,
  title,
  subtitle,
  icon: Icon,
  glowIntensity = "subtle",
  className = "",
  animated = true,
  border = true,
}) {
  const glowIntensities = {
    subtle: "shadow-sm shadow-[rgba(5,150,105,0.1)] hover:shadow-md hover:shadow-[rgba(5,150,105,0.15)]",
    medium: "shadow-md shadow-[rgba(5,150,105,0.15)] hover:shadow-lg hover:shadow-[rgba(5,150,105,0.2)]",
    prominent: "shadow-lg shadow-[rgba(5,150,105,0.2)] hover:shadow-xl hover:shadow-[rgba(5,150,105,0.3)]",
  };

  const borderClass = border
    ? "border border-[rgba(5,150,105,0.1)] hover:border-[rgba(5,150,105,0.2)]"
    : "";

  const Component = animated ? motion.div : "div";
  const animationProps = animated
    ? {
        initial: { opacity: 0, y: 20 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true },
        transition: { duration: 0.5 },
      }
    : {};

  return (
    <Component
      {...animationProps}
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br from-white/40 to-white/20 backdrop-blur-xl p-6 transition-all duration-300 ${glowIntensities[glowIntensity]} ${borderClass} ${className}`}
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[rgba(5,150,105,0.05)] to-transparent pointer-events-none rounded-2xl" />

      {/* Animated border glow (optional) */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[rgba(5,150,105,0)] via-[rgba(5,150,105,0.1)] to-[rgba(5,150,105,0)] opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        {(title || subtitle || Icon) && (
          <div className="mb-4 flex items-start justify-between">
            <div className="flex-1">
              {Icon && (
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)]">
                  <Icon className="h-5 w-5 text-[#059669]" />
                </div>
              )}
              {title && (
                <h3 className="text-lg font-medium text-[#0f172a]">{title}</h3>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-[#64748b]">{subtitle}</p>
              )}
            </div>
          </div>
        )}

        {/* Main content */}
        <div className="text-[#475569]">{children}</div>
      </div>
    </Component>
  );
}
