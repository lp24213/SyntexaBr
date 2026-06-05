"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

/**
 * ModernFAQ — Seção FAQ com animações suaves e accordion premium
 */
export function ModernFAQ({
  title,
  description,
  faqs = [],
  className = "",
}) {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section className={`py-20 ${className}`}>
      <div className="mx-auto max-w-2xl px-5">
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

        {/* FAQ Items */}
        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="overflow-hidden rounded-lg border border-[rgba(15,23,42,0.06)] bg-white transition-all duration-300 hover:border-[rgba(5,150,105,0.1)]"
            >
              <button
                onClick={() => setOpenIndex(openIndex === i ? -1 : i)}
                className="flex w-full items-center justify-between px-6 py-4 text-left"
              >
                <span className="font-medium text-[#0f172a]">
                  {faq.question}
                </span>
                <motion.svg
                  animate={{ rotate: openIndex === i ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="h-5 w-5 flex-shrink-0 text-[#059669]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 14l-7 7m0 0l-7-7m7 7V3"
                  />
                </motion.svg>
              </button>

              <AnimatePresence>
                {openIndex === i && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="border-t border-[rgba(15,23,42,0.06)]"
                  >
                    <p className="px-6 py-4 text-[15px] text-[#64748b]">
                      {faq.answer}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
