"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * AIWorkflowSection — Seção visual que mostra workflow de AI com animações
 * Padrão: OpenAI, Anthropic
 */
export function AIWorkflowSection({
  title,
  description,
  steps = [],
  className = "",
}) {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.1,
      },
    },
  };

  const stepVariants = {
    hidden: { opacity: 0, x: -20 },
    show: {
      opacity: 1,
      x: 0,
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
          className="mb-12 text-center"
        >
          {title && (
            <h2 className="text-3xl font-medium text-[#0f172a]">{title}</h2>
          )}
          {description && (
            <p className="mt-4 text-lg text-[#64748b]">{description}</p>
          )}
        </motion.div>

        {/* Steps */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
          className="space-y-6"
        >
          {steps.map((step, i) => (
            <motion.div
              key={i}
              variants={stepVariants}
              className="group flex gap-6"
            >
              {/* Number circle */}
              <motion.div
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="relative flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full border border-[rgba(5,150,105,0.2)] bg-[rgba(5,150,105,0.05)]"
              >
                <span className="text-sm font-semibold text-[#059669]">
                  {i + 1}
                </span>

                {/* Connection line to next */}
                {i < steps.length - 1 && (
                  <div className="absolute top-12 left-1/2 h-6 w-px -translate-x-1/2 bg-gradient-to-b from-[rgba(5,150,105,0.2)] to-[rgba(5,150,105,0)]" />
                )}
              </motion.div>

              {/* Content */}
              <div className="flex-1 pt-1">
                <h3 className="font-medium text-[#0f172a]">{step.title}</h3>
                <p className="mt-2 text-[15px] text-[#64748b]">
                  {step.description}
                </p>

                {step.details && (
                  <ul className="mt-3 space-y-1 text-sm text-[#475569]">
                    {step.details.map((detail, j) => (
                      <li key={j} className="flex items-center gap-2">
                        <span className="h-1 w-1 rounded-full bg-[#059669]" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
