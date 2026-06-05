"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * EnterpriseBanner — Banner premium para seções importantes
 * Com CTA, ícone e animações elegantes
 */
export function EnterpriseBanner({
  title,
  subtitle,
  icon: Icon,
  ctaText = "Saiba Mais",
  ctaHref = "/",
  secondaryCtaText,
  secondaryCtaHref,
  className = "",
  glowColor = "emerald",
}) {
  const glowBackgrounds = {
    emerald: "from-[rgba(5,150,105,0.08)] to-[rgba(5,150,105,0.02)]",
    blue: "from-[rgba(59,130,246,0.08)] to-[rgba(59,130,246,0.02)]",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className={`relative overflow-hidden rounded-2xl border border-[rgba(5,150,105,0.1)] bg-gradient-to-br ${glowBackgrounds[glowColor]} p-8 md:p-12 ${className}`}
    >
      {/* Animated background elements */}
      <div className="absolute -right-20 -top-20 h-40 w-40 rounded-full bg-[rgba(5,150,105,0.1)] blur-3xl" />
      <div className="absolute -bottom-20 -left-20 h-40 w-40 rounded-full bg-[rgba(5,150,105,0.05)] blur-3xl" />

      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start gap-6">
          {Icon && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl bg-[rgba(5,150,105,0.12)]"
            >
              <Icon className="h-8 w-8 text-[#059669]" />
            </motion.div>
          )}

          <div className="flex-1">
            <h2 className="text-2xl font-medium text-[#0f172a] md:text-3xl">
              {title}
            </h2>
            {subtitle && (
              <p className="mt-3 text-[15px] text-[#64748b]">{subtitle}</p>
            )}

            {/* CTA Buttons */}
            <div className="mt-6 flex flex-wrap gap-3">
              <motion.a
                href={ctaHref}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="inline-flex rounded-lg bg-[#059669] px-6 py-3 font-medium text-white transition-colors hover:bg-[#047857]"
              >
                {ctaText}
              </motion.a>

              {secondaryCtaText && (
                <motion.a
                  href={secondaryCtaHref}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="inline-flex rounded-lg border border-[rgba(15,23,42,0.1)] px-6 py-3 font-medium text-[#0f172a] transition-colors hover:bg-[rgba(15,23,42,0.03)]"
                >
                  {secondaryCtaText}
                </motion.a>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
