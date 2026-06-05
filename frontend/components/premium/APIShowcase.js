"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * APIShowcase — Seção que showcasa API com exemplos de código e documentação
 * Padrão: Stripe, OpenAI
 */
export function APIShowcase({
  title,
  description,
  endpoints = [],
  className = "",
}) {
  const [selectedEndpoint, setSelectedEndpoint] = React.useState(0);

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
    hidden: { opacity: 0, x: -10 },
    show: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.3,
        ease: "easeOut",
      },
    },
  };

  return (
    <section className={`py-20 ${className}`}>
      <div className="mx-auto max-w-5xl px-5">
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
            <p className="mt-4 text-lg text-[#64748b]">{description}</p>
          )}
        </motion.div>

        {/* Content Grid */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Endpoint List */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            className="space-y-2"
          >
            {endpoints.map((endpoint, i) => (
              <motion.button
                key={i}
                variants={itemVariants}
                onClick={() => setSelectedEndpoint(i)}
                className={`w-full rounded-lg border-2 p-4 text-left transition-all duration-200 ${
                  selectedEndpoint === i
                    ? "border-[#059669] bg-[rgba(5,150,105,0.05)]"
                    : "border-[rgba(15,23,42,0.06)] hover:border-[rgba(5,150,105,0.2)]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      endpoint.method === "GET"
                        ? "bg-[rgba(59,130,246,0.1)] text-blue-600"
                        : endpoint.method === "POST"
                          ? "bg-[rgba(34,197,94,0.1)] text-green-600"
                          : "bg-[rgba(229,62,102,0.1)] text-red-600"
                    }`}
                  >
                    {endpoint.method}
                  </span>
                  <span className="font-medium text-[#0f172a]">
                    {endpoint.name}
                  </span>
                </div>
                {endpoint.description && (
                  <p className="mt-2 text-xs text-[#64748b]">
                    {endpoint.description}
                  </p>
                )}
              </motion.button>
            ))}
          </motion.div>

          {/* Code Preview */}
          {endpoints[selectedEndpoint] && (
            <motion.div
              key={selectedEndpoint}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className="rounded-lg border border-[rgba(15,23,42,0.06)] bg-[#0f172a] p-6 font-mono text-sm text-[#e2e8f0]"
            >
              <pre className="overflow-x-auto">
                <code>{endpoints[selectedEndpoint].example}</code>
              </pre>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}
