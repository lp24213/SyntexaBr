"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * GradientBorderCard — Card com bordas com gradiente animado
 * Estilo: Premium, tech, sofisticado
 */
export function GradientBorderCard({
  children,
  title,
  description,
  icon: Icon,
  gradientFrom = "emerald",
  className = "",
}) {
  const gradients = {
    emerald: "from-[rgba(5,150,105,0.3)] to-[rgba(5,150,105,0)]",
    blue: "from-[rgba(59,130,246,0.3)] to-[rgba(59,130,246,0)]",
    purple: "from-[rgba(168,85,247,0.3)] to-[rgba(168,85,247,0)]",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className={`group relative rounded-2xl p-px overflow-hidden ${className}`}
    >
      {/* Animated gradient border */}
      <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${gradients[gradientFrom]} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />

      {/* Inner content */}
      <div className="relative rounded-2xl bg-white p-6">
        {/* Icon */}
        {Icon && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)]"
          >
            <Icon className="h-6 w-6 text-[#059669]" />
          </motion.div>
        )}

        {/* Text */}
        {title && (
          <h3 className="font-medium text-[#0f172a]">{title}</h3>
        )}
        {description && (
          <p className="mt-2 text-sm text-[#64748b]">{description}</p>
        )}

        {/* Children */}
        {children && (
          <div className="mt-4">{children}</div>
        )}
      </div>
    </motion.div>
  );
}
