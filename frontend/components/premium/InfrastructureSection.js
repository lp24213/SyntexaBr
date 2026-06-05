"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * InfrastructureSection — Seção visual de infraestrutura com diagrama animado
 * Expandido do componente existente
 */
export function InfrastructureSection({
  title,
  description,
  layers = [],
  className = "",
}) {
  return (
    <section className={`py-20 ${className}`}>
      <div className="mx-auto max-w-5xl px-5">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-12 text-center"
        >
          {title && (
            <h2 className="text-3xl font-medium text-[#0f172a]">{title}</h2>
          )}
          {description && (
            <p className="mt-4 max-w-2xl text-lg text-[#64748b]">
              {description}
            </p>
          )}
        </motion.div>

        {/* Infrastructure Layers */}
        <div className="space-y-4">
          {layers.map((layer, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="group relative rounded-xl border border-[rgba(15,23,42,0.06)] bg-white p-6 transition-all duration-300 hover:border-[rgba(5,150,105,0.2)] hover:shadow-[0_4px_16px_rgba(5,150,105,0.1)]"
            >
              {/* Background glow */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-[rgba(5,150,105,0.02)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {/* Layer marker */}
              <div className="absolute left-6 top-1/2 h-3 w-3 -translate-y-1/2 rounded-full border-2 border-[#059669] bg-white" />

              {/* Content */}
              <div className="relative z-10 flex items-start gap-6 pl-4">
                {/* Icon */}
                {layer.icon && (
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)]">
                    <layer.icon className="h-6 w-6 text-[#059669]" />
                  </div>
                )}

                {/* Text */}
                <div className="flex-1">
                  <h3 className="font-medium text-[#0f172a]">{layer.title}</h3>
                  <p className="mt-1 text-sm text-[#64748b]">
                    {layer.description}
                  </p>

                  {/* Components */}
                  {layer.components && layer.components.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {layer.components.map((comp, j) => (
                        <span
                          key={j}
                          className="rounded-full bg-[rgba(5,150,105,0.08)] px-3 py-1 text-xs font-medium text-[#059669]"
                        >
                          {comp}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
