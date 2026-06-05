"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * AnimatedIntegrationCards — Cards animados para integrações
 * Com efeito de hover flutuante e ícone animado
 */
export function AnimatedIntegrationCards({
  integrations = [],
  className = "",
}) {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.15,
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
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-100px" }}
      className={`grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 ${className}`}
    >
      {integrations.map((integration, i) => (
        <motion.div
          key={i}
          variants={itemVariants}
          whileHover={{
            y: -4,
            transition: { duration: 0.3 },
          }}
          className="group relative"
        >
          <div className="relative flex flex-col items-center justify-center rounded-xl border border-[rgba(15,23,42,0.08)] bg-white p-6 transition-all duration-300 hover:border-[rgba(5,150,105,0.2)] hover:shadow-[0_8px_24px_rgba(5,150,105,0.12)]">
            {/* Background glow */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-[rgba(5,150,105,0.02)] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            {/* Icon container with floating animation */}
            <motion.div
              animate={{
                y: [0, -4, 0],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                delay: i * 0.2,
              }}
              className="relative z-10 mb-3"
            >
              {integration.icon ? (
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)]">
                  <integration.icon className="h-6 w-6 text-[#059669]" />
                </div>
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)] text-sm font-semibold text-[#059669]">
                  {integration.title.charAt(0)}
                </div>
              )}
            </motion.div>

            {/* Text */}
            <h4 className="relative z-10 text-center text-sm font-medium text-[#0f172a]">
              {integration.title}
            </h4>

            {/* Badge */}
            {integration.badge && (
              <span className="relative z-10 mt-2 inline-flex rounded-full bg-[rgba(5,150,105,0.08)] px-2 py-0.5 text-[10px] font-medium text-[#059669]">
                {integration.badge}
              </span>
            )}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
