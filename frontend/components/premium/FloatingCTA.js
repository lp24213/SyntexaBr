"use client";

import React from "react";
import { motion } from "framer-motion";

/**
 * FloatingCTA — CTA flutuante com animações elegantes
 * Fica visível enquanto scroll, com hover premium
 */
export function FloatingCTA({
  title,
  subtitle,
  primaryText = "Começar Agora",
  primaryHref = "/chat",
  secondaryText,
  secondaryHref,
  onPrimaryClick,
  onSecondaryClick,
  className = "",
}) {
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setIsVisible(window.scrollY > 400);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{
        opacity: isVisible ? 1 : 0,
        y: isVisible ? 0 : 20,
        pointerEvents: isVisible ? "auto" : "none",
      }}
      transition={{ duration: 0.3 }}
      className={`fixed bottom-8 right-8 z-50 ${className}`}
    >
      <motion.div
        animate={{
          y: [0, -8, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
        }}
        className="flex flex-col gap-3 rounded-2xl border border-[rgba(5,150,105,0.2)] bg-white/90 backdrop-blur-xl p-4 shadow-xl shadow-[rgba(5,150,105,0.2)]"
      >
        {title && (
          <div>
            <p className="text-sm font-medium text-[#0f172a]">{title}</p>
            {subtitle && (
              <p className="mt-0.5 text-xs text-[#64748b]">{subtitle}</p>
            )}
          </div>
        )}

        <div className="flex flex-col gap-2 sm:flex-row">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onPrimaryClick}
            as={primaryHref && !onPrimaryClick ? "a" : "button"}
            href={primaryHref}
            className="rounded-lg bg-[#059669] px-3 py-2 text-xs font-medium text-white transition-all duration-200 hover:bg-[#047857]"
          >
            {primaryText}
          </motion.button>

          {(secondaryText || secondaryHref) && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onSecondaryClick}
              as={secondaryHref && !onSecondaryClick ? "a" : "button"}
              href={secondaryHref}
              className="rounded-lg border border-[rgba(15,23,42,0.1)] px-3 py-2 text-xs font-medium text-[#0f172a] transition-all duration-200 hover:bg-[rgba(15,23,42,0.03)]"
            >
              {secondaryText}
            </motion.button>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
