"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * SecurityHighlights — Seção de segurança com cards e ícones animados
 */
export function SecurityHighlights({
  title,
  description,
  highlights = [],
  className = "",
}) {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut",
      },
    },
  };

  return (
    <section className={`py-20 ${className}`}>
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-12"
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

        {/* Highlights grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
        >
          {highlights.map((highlight, i) => (
            <motion.div
              key={i}
              variants={itemVariants}
              whileHover={{ y: -4 }}
              className="group relative rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-6 transition-all duration-300 hover:border-[rgba(5,150,105,0.2)] hover:shadow-[0_8px_24px_rgba(5,150,105,0.1)]"
            >
              {/* Background glow */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[rgba(5,150,105,0.02)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {/* Icon */}
              {highlight.icon && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  whileInView={{ scale: 1, opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.05 + 0.1 }}
                  className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)]"
                >
                  <highlight.icon className="h-6 w-6 text-[#059669]" />
                </motion.div>
              )}

              {/* Content */}
              <div className="relative z-10">
                <h3 className="font-medium text-[#0f172a]">{highlight.title}</h3>
                <p className="mt-2 text-sm text-[#64748b]">
                  {highlight.description}
                </p>

                {highlight.badge && (
                  <div className="mt-3 inline-flex rounded-full bg-[rgba(5,150,105,0.08)] px-2.5 py-0.5 text-[11px] font-medium text-[#059669]">
                    {highlight.badge}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
