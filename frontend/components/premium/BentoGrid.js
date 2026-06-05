"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * BentoGrid — Layout premium estilo Apple/Stripe com animações
 * Itens podem ter diferentes tamanhos (1x1, 2x1, 1x2, etc)
 */
export function BentoGrid({
  items = [],
  className = "",
}) {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    show: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.5,
        ease: "easeOut",
      },
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-100px" }}
      className={`grid gap-4 auto-rows-[300px] sm:grid-cols-2 lg:grid-cols-3 ${className}`}
    >
      {items.map((item, i) => (
        <motion.div
          key={i}
          variants={itemVariants}
          whileHover={{ y: -2, transition: { duration: 0.2 } }}
          className={`group relative overflow-hidden rounded-2xl border border-[rgba(15,23,42,0.06)] bg-gradient-to-br from-white/80 to-white/50 p-6 transition-all duration-300 hover:border-[rgba(5,150,105,0.2)] hover:shadow-[0_8px_32px_rgba(5,150,105,0.1)] ${
            item.colSpan ? `sm:col-span-${item.colSpan}` : ""
          } ${item.rowSpan ? `sm:row-span-${item.rowSpan}` : ""} ${
            item.className || ""
          }`}
        >
          {/* Background gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-[rgba(5,150,105,0.02)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

          {/* Content */}
          <div className="relative z-10 flex flex-col h-full">
            {/* Icon */}
            {item.icon && (
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)]">
                <item.icon className="h-5 w-5 text-[#059669]" />
              </div>
            )}

            {/* Text content */}
            <div className="flex-1">
              <h3 className="font-medium text-[#0f172a]">{item.title}</h3>
              <p className="mt-2 text-sm text-[#64748b]">{item.description}</p>
            </div>

            {/* Footer content or CTA */}
            {item.footer && (
              <div className="mt-auto pt-4">
                {item.footer}
              </div>
            )}
          </div>

          {/* Hover glow line */}
          <div className="absolute inset-0 rounded-2xl border border-[rgba(5,150,105,0)] group-hover:border-[rgba(5,150,105,0.1)] transition-all duration-300" />
        </motion.div>
      ))}
    </motion.div>
  );
}
