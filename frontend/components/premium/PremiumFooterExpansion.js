"use client";

import React from "react";
import { motion } from "framer-motion";
import Link from "next/link";

/**
 * PremiumFooterExpansion — Footer premium com links organizados e newsletter
 * Mantém footer existente, apenas expande com novos elementos
 */
export function PremiumFooterExpansion({
  newsletter = true,
  sections = [],
  className = "",
}) {
  const [email, setEmail] = React.useState("");
  const [subscribed, setSubscribed] = React.useState(false);

  const handleSubscribe = (e) => {
    e.preventDefault();
    setSubscribed(true);
    setTimeout(() => setSubscribed(false), 2000);
  };

  return (
    <section className={`border-t border-[rgba(15,23,42,0.06)] bg-white py-12 ${className}`}>
      <div className="mx-auto max-w-6xl px-5">
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
          {/* Newsletter Section */}
          {newsletter && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <h3 className="text-sm font-medium tracking-wider text-[#0f172a] uppercase">
                Newsletter
              </h3>
              <p className="mt-2 text-sm text-[#64748b]">
                Receba as últimas notícias e atualizações
              </p>

              <form onSubmit={handleSubscribe} className="mt-4">
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="seu@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="flex-1 rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-3 py-2 text-sm text-[#0f172a] placeholder-[#94a3b8] transition-all duration-200 focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)]"
                  />
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit"
                    className="rounded-lg bg-[#059669] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#047857]"
                  >
                    {subscribed ? "✓" : "→"}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          )}

          {/* Link Sections */}
          {sections.map((section, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            >
              <h3 className="text-sm font-medium tracking-wider text-[#0f172a] uppercase">
                {section.title}
              </h3>
              <ul className="mt-4 space-y-2">
                {section.links.map((link, j) => (
                  <li key={j}>
                    <Link
                      href={link.href}
                      className="text-sm text-[#64748b] transition-colors hover:text-[#059669]"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
