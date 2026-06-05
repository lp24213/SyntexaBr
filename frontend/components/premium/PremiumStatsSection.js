"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * PremiumStatsSection — Seção de estatísticas com números animados
 * Padrão: Stripe, Vercel
 */
export function PremiumStatsSection({
  title,
  description,
  stats = [],
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
      <div className="mx-auto max-w-6xl px-5">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16 text-center"
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

        {/* Stats Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
          className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4"
        >
          {stats.map((stat, i) => (
            <motion.div
              key={i}
              variants={itemVariants}
              className="group relative rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-8 text-center transition-all duration-300 hover:border-[rgba(5,150,105,0.2)] hover:shadow-[0_8px_24px_rgba(5,150,105,0.1)]"
            >
              {/* Background glow */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[rgba(5,150,105,0.02)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {/* Content */}
              <div className="relative z-10">
                <motion.div
                  initial={{ scale: 0.5, opacity: 0 }}
                  whileInView={{ scale: 1, opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className="text-3xl font-bold text-[#059669] md:text-4xl"
                >
                  {stat.value}
                </motion.div>
                <p className="mt-2 text-sm text-[#64748b]">{stat.label}</p>
                {stat.description && (
                  <p className="mt-2 text-xs text-[#94a3b8]">
                    {stat.description}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
