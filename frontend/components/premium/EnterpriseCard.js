"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * EnterpriseCard — Card elegante com glow, bordas sofisticadas e animações premium
 * Padrão: OpenAI, Anthropic, Stripe
 */
export function EnterpriseCard({
  icon: Icon,
  title,
  description,
  features = [],
  glowColor = "emerald",
  className = "",
  variant = "default",
  href,
}) {
  const glowColors = {
    emerald: "shadow-emerald-500/20 hover:shadow-emerald-500/30",
    blue: "shadow-blue-500/20 hover:shadow-blue-500/30",
    slate: "shadow-slate-500/20 hover:shadow-slate-500/30",
  };

  const hoverVariants = {
    default: {
      y: -4,
      boxShadow:
        glowColor === "emerald"
          ? "0 20px 50px rgba(5, 150, 105, 0.25)"
          : glowColor === "blue"
            ? "0 20px 50px rgba(59, 130, 246, 0.25)"
            : "0 20px 50px rgba(100, 116, 139, 0.25)",
    },
    flat: {
      backgroundColor: "rgba(5, 150, 105, 0.05)",
    },
  };

  const content = (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      whileHover={hoverVariants[variant]}
      className={`relative rounded-2xl border border-[rgba(15,23,42,0.08)] bg-white/50 backdrop-blur-sm p-6 transition-all duration-300 hover:border-[rgba(5,150,105,0.15)] ${glowColors[glowColor]} ${className}`}
    >
      {/* Subtle glow background */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[rgba(5,150,105,0.02)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      {/* Icon */}
      {Icon && (
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          whileInView={{ scale: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[rgba(5,150,105,0.08)]"
        >
          <Icon className="h-6 w-6 text-[#059669]" />
        </motion.div>
      )}

      {/* Content */}
      <div className="relative z-10">
        <h3 className="text-lg font-medium text-[#0f172a]">{title}</h3>
        <p className="mt-2 text-sm text-[#64748b]">{description}</p>

        {/* Features list */}
        {features.length > 0 && (
          <ul className="mt-4 space-y-2">
            {features.map((feature, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -8 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.15 + i * 0.05 }}
                className="flex items-start gap-2 text-xs text-[#475569]"
              >
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-[#059669] flex-shrink-0" />
                <span>{feature}</span>
              </motion.li>
            ))}
          </ul>
        )}
      </div>
    </motion.div>
  );

  if (href) {
    return (
      <a href={href} className="group">
        {content}
      </a>
    );
  }

  return <div className="group">{content}</div>;
}
