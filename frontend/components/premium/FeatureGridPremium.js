"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * FeatureGridPremium — Grid de features com reveal on scroll e stagger
 * Padrão: Apple, Vercel, Linear
 */
export function FeatureGridPremium({
  features = [],
  columns = 3,
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

  const columnClass = {
    2: "sm:grid-cols-2",
    3: "sm:grid-cols-2 lg:grid-cols-3",
    4: "sm:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-100px" }}
      className={`grid gap-6 ${columnClass[columns] || columnClass[3]} ${className}`}
    >
      {features.map((feature, i) => (
        <motion.div key={i} variants={itemVariants} className="group">
          <div className="relative rounded-2xl border border-[rgba(15,23,42,0.06)] bg-gradient-to-br from-white to-white/50 p-6 transition-all duration-300 hover:border-[rgba(5,150,105,0.2)] hover:shadow-[0_4px_30px_rgba(5,150,105,0.1)]">
            {/* Glow overlay on hover */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[rgba(5,150,105,0.02)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

            {/* Icon */}
            {feature.icon && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.05 + 0.1 }}
                className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)]"
              >
                <feature.icon className="h-5 w-5 text-[#059669]" />
              </motion.div>
            )}

            {/* Content */}
            <div className="relative z-10">
              <h3 className="font-medium text-[#0f172a]">{feature.title}</h3>
              <p className="mt-2 text-sm text-[#64748b]">{feature.description}</p>

              {feature.badge && (
                <div className="mt-3 inline-flex rounded-full bg-[rgba(5,150,105,0.08)] px-2.5 py-0.5 text-[11px] font-medium text-[#059669]">
                  {feature.badge}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
