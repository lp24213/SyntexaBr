"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import React from "react";
import { AppShell } from "../components/shell";
import { InfrastructureVisual } from "../components/infrastructure-visual";
import { DownloadSection } from "../components/download-section";
import { t } from "../lib/i18n";
import { useLanguage } from "../components/language-provider";
import { encryptedPath } from "../lib/routes";

const MODULES = [
  { titleKey: "moduleChatTitle", descKey: "moduleChatDesc", status: "active" },
  { titleKey: "moduleSpeedTitle", descKey: "moduleSpeedDesc", status: "active" },
  { titleKey: "moduleAgentsTitle", descKey: "moduleAgentsDesc", status: "active" },
  { titleKey: "moduleCreateTitle", descKey: "moduleCreateDesc", status: "active" },
  { titleKey: "moduleMemoryTitle", descKey: "moduleMemoryDesc", status: "active" },
  { titleKey: "moduleSpeechTitle", descKey: "moduleSpeechDesc", status: "active" },
  { titleKey: "moduleDocumentsTitle", descKey: "moduleDocumentsDesc", status: "active" },
  { titleKey: "modulePowerTitle", descKey: "modulePowerDesc", status: "active" },
  { titleKey: "moduleSecurityTitle", descKey: "moduleSecurityDesc", status: "active" },
  { titleKey: "moduleResearchTitle", descKey: "moduleResearchDesc", status: "standby" },
  { titleKey: "moduleExecutionTitle", descKey: "moduleExecutionDesc", status: "standby" },
  { titleKey: "moduleBusinessTitle", descKey: "moduleBusinessDesc", status: "standby" },
];

const PLANS = [
  { nameKey: "planFreeName", priceKey: "planFreePrice", descKey: "planFreeDesc" },
  { nameKey: "planBasicName", priceKey: "planBasicPrice", descKey: "planBasicDesc" },
  { nameKey: "planMidName", priceKey: "planMidPrice", descKey: "planMidDesc" },
  { nameKey: "planMasterName", priceKey: "planMasterPrice", descKey: "planMasterDesc" },
];

export default function HomePage() {
  const { locale } = useLanguage();
  return (
    <AppShell fullWidth={true}>
      <main className="relative min-h-[100dvh] w-full overflow-x-hidden overflow-y-auto bg-white text-[#0f172a] [scroll-behavior:smooth]">
        {/* Background infrastructure grid */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute inset-0 infrastructure-grid opacity-60" />
          <div className="hero-fog-a pointer-events-none absolute inset-0" />
        </div>

        {/* Hero Section — Clean Premium */}
        <section className="relative z-10 flex min-h-[100dvh] flex-col items-center justify-center px-5 pt-20 pb-16">
          <div className="mx-auto flex w-full max-w-[1200px] flex-col items-center text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="mb-6 flex items-center gap-2 rounded-full border border-[rgba(15,23,42,0.08)] bg-[rgba(15,23,42,0.03)] px-4 py-1.5"
            >
              <span className="h-[5px] w-[5px] rounded-full bg-[#059669]" />
              <span className="text-[11px] font-medium tracking-[0.12em] text-[#475569] uppercase">
                {t('aiMadeBrazilBadge', locale)}
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
              className="max-w-4xl text-[2.5rem] font-medium leading-[1.12] tracking-[-0.03em] text-[#0f172a] md:text-[3.5rem] lg:text-[4rem]"
            >
              {t('mainHeading', locale)}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.25 }}
              className="mt-6 max-w-2xl text-[16px] leading-relaxed text-[#64748b] md:text-[18px]"
            >
              {t('mainDescription', locale)}
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="mt-8 flex flex-wrap items-center justify-center gap-3"
            >
              <Link
                href={encryptedPath("/chat")}
                className="syntexa-btn-primary rounded-full px-7 py-3 text-[13px] font-medium"
              >
                {t('accessConsole', locale)}
              </Link>
              <Link
                href="#infraestrutura"
                className="syntexa-btn-outline rounded-full px-7 py-3 text-[13px] font-medium"
              >
                {t('exploreArchitecture', locale)}
              </Link>
            </motion.div>
          </div>

          {/* Infrastructure Visualization */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.2, delay: 0.6 }}
            className="mt-12 w-full max-w-[900px]"
          >
            <InfrastructureVisual />
          </motion.div>
        </section>

        {/* Platform Modules */}
        <section id="infraestrutura" className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-24">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <div className="mb-2 flex items-center gap-2">
            <span className="h-[1px] w-8 bg-[rgba(15,23,42,0.15)]" />
            <span className="text-[11px] font-medium tracking-[0.12em] text-[#475569] uppercase">{t('architectureLabel', locale)}</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
            {t('platformModules', locale)}
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#64748b]">
            {t('platformModulesDescription', locale)}
          </p>
        </motion.div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((mod, i) => (
            <motion.div
              key={mod.titleKey}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="syntexa-card group relative rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-6 transition-all duration-300 hover:border-[rgba(15,23,42,0.1)] hover:shadow-[0_4px_20px_rgba(15,23,42,0.05)]"
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(15,23,42,0.04)]">
                  <div className={`h-2 w-2 rounded-full ${
                    mod.status === "active" ? "status-active" : "status-standby"
                  }`} />
                </div>
                <span className="text-[10px] font-medium tracking-[0.1em] text-[#94a3b8] uppercase">
                  {mod.status === "active" ? t('statusOperational', locale) : t('statusStandby', locale)}
                </span>
              </div>
              <h3 className="text-[15px] font-medium text-[#0f172a]">{t(mod.titleKey, locale)}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-[#64748b]">{t(mod.descKey, locale)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* WhatsApp Business Section */}
      <section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-24">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <div className="mb-2 flex items-center gap-2">
            <span className="h-[1px] w-8 bg-[#25D366]" />
            <span className="text-[11px] font-medium tracking-[0.12em] text-[#25D366] uppercase">WhatsApp Business</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
            {t('whatsappTitle', locale)}
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#64748b]">
            {t('whatsappSubtitle', locale)}
          </p>
        </motion.div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { titleKey: "whatsappChatbot", descKey: "whatsappChatbotDesc" },
            { titleKey: "whatsappAttendants", descKey: "whatsappAttendantsDesc" },
            { titleKey: "whatsappNumbers", descKey: "whatsappNumbersDesc" },
            { titleKey: "whatsappAutomations", descKey: "whatsappAutomationsDesc" },
            { titleKey: "whatsappMemory", descKey: "whatsappMemoryDesc" },
            { titleKey: "whatsappAnalytics", descKey: "whatsappAnalyticsDesc" },
          ].map((mod, i) => (
            <motion.div
              key={mod.titleKey}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="syntexa-card rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-6"
            >
              <h3 className="text-[15px] font-semibold text-[#0f172a]">{t(mod.titleKey, locale)}</h3>
              <p className="mt-2 text-[13px] leading-[1.6] text-[#64748b]">{t(mod.descKey, locale)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Document Engine Section */}
      <section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-24">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <div className="mb-2 flex items-center gap-2">
            <span className="h-[1px] w-8 bg-[rgba(15,23,42,0.15)]" />
            <span className="text-[11px] font-medium tracking-[0.12em] text-[#475569] uppercase">{t('documentEngine', locale)}</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
            {t('documentEngineTitle', locale)}
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#64748b]">
            {t('documentEngineDesc', locale)}
          </p>
        </motion.div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { titleKey: "docPdf", descKey: "docPdfDesc" },
            { titleKey: "docExcel", descKey: "docExcelDesc" },
            { titleKey: "docWord", descKey: "docWordDesc" },
            { titleKey: "docCsv", descKey: "docCsvDesc" },
          ].map((mod, i) => (
            <motion.div
              key={mod.titleKey}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="syntexa-card rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-6"
            >
              <h3 className="text-[15px] font-semibold text-[#0f172a]">{t(mod.titleKey, locale)}</h3>
              <p className="mt-2 text-[13px] leading-[1.6] text-[#64748b]">{t(mod.descKey, locale)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Technical Specs Banner */}
      <section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-16">
        <div className="syntexa-card rounded-3xl border border-[rgba(15,23,42,0.06)] bg-[#f8fafc] p-8 md:p-12">
          <div className="grid gap-8 md:grid-cols-4">
            {[
              { value: "13B+", labelKey: "specModelParams", subKey: "specTransformer" },
              { value: "<200ms", labelKey: "specVoice", subKey: "specVoiceDesc" },
              { value: "GPU", labelKey: "specProcessing", subKey: "specProcessingDesc" },
              { value: "100%", labelKey: "specData", subKey: "specDataDesc" }
            ].map((stat, i) => (
              <motion.div
                key={stat.labelKey}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="text-center"
              >
                <div className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
                  {stat.value}
                </div>
                <div className="mt-1 text-[13px] font-medium text-[#334155]">{t(stat.labelKey, locale)}</div>
                <div className="text-[11px] text-[#94a3b8]">{t(stat.subKey, locale)}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Plans */}
      <section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-24">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <div className="mb-2 flex items-center gap-2">
            <span className="h-[1px] w-8 bg-[rgba(15,23,42,0.15)]" />
            <span className="text-[11px] font-medium tracking-[0.12em] text-[#475569] uppercase">{t('infrastructureLabel', locale)}</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
            {t('accessLayers', locale)}
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#64748b]">
            {t('accessLayersDesc', locale)}
          </p>
        </motion.div>

        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {PLANS.map((plan, i) => (
            <motion.div
              key={plan.nameKey}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="syntexa-card relative rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-6"
            >
              <h3 className="text-[15px] font-medium text-[#0f172a]">{t(plan.nameKey, locale)}</h3>
              <div className="mt-2 text-[12px] font-medium tracking-wide text-[#475569]">{t(plan.priceKey, locale)}</div>
              <p className="mt-4 text-[13px] leading-relaxed text-[#64748b]">{t(plan.descKey, locale)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Downloads */}
      <section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-16">
        <DownloadSection locale={locale} t={t} />
      </section>

    </main>
    </AppShell>
  );
}
