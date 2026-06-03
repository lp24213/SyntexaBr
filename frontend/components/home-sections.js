"use client";

import React from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { encryptedPath } from "../lib/routes";
import { t } from "../lib/i18n";
import { useLanguage } from "./language-provider";

function FadeIn({ children, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, delay }}
    >
      {children}
    </motion.div>
  );
}

function SectionTitle({ overline, title, subtitle }) {
  return (
    <div className="mx-auto max-w-3xl text-center mb-12">
      <FadeIn>
        <span className="inline-block rounded-full bg-[#f0fdf4] text-[#16a34a] px-3 py-1 text-[11px] font-semibold tracking-wide uppercase mb-4">
          {overline}
        </span>
      </FadeIn>
      <FadeIn delay={0.1}>
        <h2 className="text-3xl md:text-4xl font-semibold text-[#0f172a] tracking-tight leading-tight">
          {title}
        </h2>
      </FadeIn>
      <FadeIn delay={0.2}>
        <p className="mt-4 text-[#64748b] text-base md:text-lg leading-relaxed">
          {subtitle}
        </p>
      </FadeIn>
    </div>
  );
}

export function HeroSection() {
  const { locale } = useLanguage();
  return (
    <section className="relative z-10 flex min-h-[92dvh] flex-col items-center justify-center px-5 pt-16 pb-12 overflow-hidden">
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-b from-[#f8fafc] via-white to-[#f8fafc]" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-[#25D366]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[400px] bg-[#34B7F1]/5 rounded-full blur-[100px]" />
      </div>

      <div className="mx-auto flex w-full max-w-[1140px] flex-col items-center text-center">
        <FadeIn>
          <div className="mb-6 flex items-center gap-2 rounded-full border border-[rgba(15,23,42,0.08)] bg-white/80 backdrop-blur-sm px-4 py-1.5 shadow-sm">
            <span className="h-[6px] w-[6px] rounded-full bg-[#25D366] animate-pulse" />
            <span className="text-[11px] font-medium tracking-[0.1em] text-[#475569] uppercase">
              {t('homeOverline', locale)}
            </span>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <h1 className="max-w-4xl text-[2.6rem] font-semibold leading-[1.1] tracking-[-0.03em] text-[#0f172a] md:text-[3.8rem] lg:text-[4.4rem]">
            {t('homeTitle', locale)}
          </h1>
        </FadeIn>

        <FadeIn delay={0.2}>
          <p className="mt-6 max-w-2xl text-[17px] leading-[1.7] text-[#64748b] md:text-[19px]">
            {t('homeSubtitle', locale)}
          </p>
        </FadeIn>

        <FadeIn delay={0.3}>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link
              href={encryptedPath("/chat")}
              className="inline-flex items-center rounded-full bg-[#0f172a] px-7 py-3.5 text-[14px] font-medium text-white shadow-lg shadow-[#0f172a]/15 hover:bg-[#1e293b] transition-all hover:-translate-y-0.5"
            >
              {t('homeTryAi', locale)}
            </Link>
            <Link
              href={encryptedPath("/whatsapp")}
              className="inline-flex items-center rounded-full bg-[#25D366] px-7 py-3.5 text-[14px] font-medium text-white shadow-lg shadow-[#25D366]/20 hover:bg-[#128C7E] transition-all hover:-translate-y-0.5"
            >
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.004 5.45-4.439 9.884-9.887 9.884m8.413-18.3A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
              {t('homeConnectWhatsapp', locale)}
            </Link>
            <Link
              href="#planos"
              className="inline-flex items-center rounded-full border border-[rgba(15,23,42,0.12)] bg-white px-7 py-3.5 text-[14px] font-medium text-[#475569] hover:bg-[#f8fafc] transition-all"
            >
              {t('homeViewPlans', locale)}
            </Link>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

export function WhatsAppSection() {
  const { t, locale } = useLanguage();
  
  const features = [
    { icon: "🤖", title: t("whatsappFeature1Title", locale), desc: t("whatsappFeature1Desc", locale) },
    { icon: "👥", title: t("whatsappFeature2Title", locale), desc: t("whatsappFeature2Desc", locale) },
    { icon: "📱", title: t("whatsappFeature3Title", locale), desc: t("whatsappFeature3Desc", locale) },
    { icon: "⚡", title: t("whatsappFeature4Title", locale), desc: t("whatsappFeature4Desc", locale) },
    { icon: "🧠", title: t("whatsappFeature5Title", locale), desc: t("whatsappFeature5Desc", locale) },
    { icon: "📊", title: t("whatsappFeature6Title", locale), desc: t("whatsappFeature6Desc", locale) },
  ];

  return (
    <section className="relative py-24 px-5 bg-white">
      <div className="mx-auto max-w-[1140px]">
        <SectionTitle
          overline="WhatsApp Business"
          title={t("whatsappSectionTitle", locale)}
          subtitle={t("whatsappSectionSubtitle", locale)}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <FadeIn key={f.title} delay={i * 0.08}>
              <div className="group rounded-2xl border border-[rgba(20,24,30,0.06)] bg-[#fafbfc] p-6 hover:bg-white hover:shadow-lg hover:shadow-[rgba(15,23,42,0.04)] hover:border-[rgba(37,211,102,0.2)] transition-all duration-300">
                <div className="w-11 h-11 rounded-xl bg-[#25D366]/10 flex items-center justify-center text-xl mb-4 group-hover:scale-110 transition-transform">
                  {f.icon}
                </div>
                <h3 className="text-[15px] font-semibold text-[#0f172a] mb-1.5">{f.title}</h3>
                <p className="text-[13px] text-[#64748b] leading-relaxed">{f.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.4}>
          <div className="mt-10 flex justify-center">
            <Link
              href={encryptedPath("/whatsapp")}
              className="inline-flex items-center rounded-full bg-[#25D366] px-6 py-3 text-[13px] font-medium text-white hover:bg-[#128C7E] transition-colors"
            >
              {t("homeAttendButton", locale)}
              <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
            </Link>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

export function DocumentsSection() {
  const { t, locale } = useLanguage();
  
  const docs = [
    { icon: "📄", title: t("documentsFeature1Title", locale), desc: t("documentsFeature1Desc", locale) },
    { icon: "📊", title: t("documentsFeature2Title", locale), desc: t("documentsFeature2Desc", locale) },
    { icon: "📝", title: t("documentsFeature3Title", locale), desc: t("documentsFeature3Desc", locale) },
    { icon: "📑", title: t("documentsFeature4Title", locale), desc: t("documentsFeature4Desc", locale) },
  ];

  return (
    <section className="relative py-24 px-5 bg-[#f8fafc]">
      <div className="mx-auto max-w-[1140px]">
        <SectionTitle
          overline="Document Engine"
          title={t("documentsSectionTitle", locale)}
          subtitle={t("documentsSectionSubtitle", locale)}
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {docs.map((d, i) => (
            <FadeIn key={d.title} delay={i * 0.1}>
              <div className="rounded-2xl border border-[rgba(20,24,30,0.06)] bg-white p-6 hover:shadow-lg hover:shadow-[rgba(15,23,42,0.04)] hover:-translate-y-1 transition-all duration-300">
                <div className="text-3xl mb-4">{d.icon}</div>
                <h3 className="text-[15px] font-semibold text-[#0f172a] mb-1.5">{d.title}</h3>
                <p className="text-[13px] text-[#64748b] leading-relaxed">{d.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.5}>
          <div className="mt-12 rounded-2xl border border-[rgba(20,24,30,0.06)] bg-white p-8 md:p-10">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-[#0f172a] mb-3">
                  {t("documentsProTitle", locale)}
                </h3>
                <ul className="space-y-2.5">
                  {[
                    t("documentsProFeature1", locale),
                    t("documentsProFeature2", locale),
                    t("documentsProFeature3", locale),
                    t("documentsProFeature4", locale),
                    t("documentsProFeature5", locale),
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-[14px] text-[#475569]">
                      <svg className="w-5 h-5 text-[#25D366] shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/></svg>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="w-full md:w-auto md:min-w-[280px] rounded-xl bg-[#f8fafc] border border-[rgba(20,24,30,0.06)] p-5 text-center">
                <div className="text-[13px] text-[#8e9094] uppercase tracking-wide mb-2">{t("documentsExampleLabel", locale)}</div>
                <div className="space-y-2">
                  <div className="h-3 bg-[#e2e8f0] rounded w-[90%] mx-auto" />
                  <div className="h-3 bg-[#e2e8f0] rounded w-[75%] mx-auto" />
                  <div className="h-3 bg-[#e2e8f0] rounded w-[85%] mx-auto" />
                  <div className="mt-3 h-16 bg-[#f1f5f9] rounded border border-dashed border-[#cbd5e1] flex items-center justify-center text-[11px] text-[#94a3b8]">
                    {t("documentsExamplePlaceholder", locale)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

export function AutomationSection() {
  const { t, locale } = useLanguage();
  
  const steps = [
    { num: "01", title: t("automationStep1Title", locale), desc: t("automationStep1Desc", locale) },
    { num: "02", title: t("automationStep2Title", locale), desc: t("automationStep2Desc", locale) },
    { num: "03", title: t("automationStep3Title", locale), desc: t("automationStep3Desc", locale) },
    { num: "04", title: t("automationStep4Title", locale), desc: t("automationStep4Desc", locale) },
  ];

  return (
    <section className="relative py-24 px-5 bg-white">
      <div className="mx-auto max-w-[1140px]">
        <SectionTitle
          overline="Automações"
          title={t("automationSectionTitle", locale)}
          subtitle={t("automationSectionSubtitle", locale)}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((s, i) => (
            <FadeIn key={s.num} delay={i * 0.1}>
              <div className="relative rounded-2xl border border-[rgba(20,24,30,0.06)] bg-[#fafbfc] p-6">
                <span className="text-[32px] font-bold text-[#e2e8f0] leading-none">{s.num}</span>
                <h3 className="mt-3 text-[15px] font-semibold text-[#0f172a] mb-1.5">{s.title}</h3>
                <p className="text-[13px] text-[#64748b] leading-relaxed">{s.desc}</p>
                {i < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-8 -right-3 w-6 h-[1px] bg-[#e2e8f0]" />
                )}
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

export function SecuritySection() {
  const { t, locale } = useLanguage();
  
  const features = [
    { title: t("securityFeature1Title", locale), desc: t("securityFeature1Desc", locale) },
    { title: t("securityFeature2Title", locale), desc: t("securityFeature2Desc", locale) },
    { title: t("securityFeature3Title", locale), desc: t("securityFeature3Desc", locale) },
    { title: t("securityFeature4Title", locale), desc: t("securityFeature4Desc", locale) },
    { title: t("securityFeature5Title", locale), desc: t("securityFeature5Desc", locale) },
    { title: t("securityFeature6Title", locale), desc: t("securityFeature6Desc", locale) },
  ];
  
  return (
    <section className="relative py-24 px-5 bg-[#0f172a]">
      <div className="mx-auto max-w-[1140px]">
        <div className="mx-auto max-w-3xl text-center mb-12">
          <FadeIn>
            <span className="inline-block rounded-full bg-[#1e293b] text-[#94a3b8] px-3 py-1 text-[11px] font-semibold tracking-wide uppercase mb-4">
              {t("securitySectionLabel", locale)}
            </span>
          </FadeIn>
          <FadeIn delay={0.1}>
            <h2 className="text-3xl md:text-4xl font-semibold text-white tracking-tight leading-tight">
              {t("securitySectionTitle", locale)}
            </h2>
          </FadeIn>
          <FadeIn delay={0.2}>
            <p className="mt-4 text-[#94a3b8] text-base md:text-lg leading-relaxed">
              {t("securitySectionSubtitle", locale)}
            </p>
          </FadeIn>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((item, i) => (
            <FadeIn key={item.title} delay={i * 0.08}>
              <div className="rounded-xl bg-[#1e293b]/50 border border-[#334155]/50 p-5">
                <h3 className="text-[14px] font-semibold text-white mb-1">{item.title}</h3>
                <p className="text-[13px] text-[#94a3b8] leading-relaxed">{item.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

export function PlansHomeSection() {
  const { t, locale } = useLanguage();
  
  const plans = [
    {
      name: "Starter",
      price: "R$ 97",
      period: "/mês",
      desc: "Ideal para pequenas empresas começando com IA no WhatsApp.",
      features: [
        "1 número WhatsApp",
        "500 mensagens/mês",
        "IA contextual básica",
        "PDF e CSV simples",
        "1 usuário",
        "Suporte por email",
      ],
      cta: "Começar agora",
      highlight: false,
    },
    {
      name: "Business",
      price: "R$ 297",
      period: "/mês",
      desc: "Para empresas que querem atendimento automatizado de verdade.",
      features: [
        "3 números WhatsApp",
        "Mensagens ilimitadas",
        "IA com memória avançada",
        "PDF, Excel e Word",
        "5 usuários",
        "Automações e workflows",
        "Analytics dashboard",
        "Suporte prioritário",
      ],
      cta: "Escolher Business",
      highlight: true,
    },
    {
      name: "Enterprise",
      price: "R$ 997",
      period: "/mês",
      desc: "Para operações de grande volume com necessidades específicas.",
      features: [
        "Números ilimitados",
        "Mensagens ilimitadas",
        "IA customizada treinada",
        "Todos os formatos + API",
        "Usuários ilimitados",
        "Workflows avançados",
        "White-label disponível",
        "Suporte dedicado SLA",
      ],
      cta: "Falar com vendas",
      highlight: false,
    },
  ];

  return (
    <section id="planos" className="relative py-24 px-5 bg-[#f8fafc]">
      <div className="mx-auto max-w-[1140px]">
        <SectionTitle
          overline="Planos"
          title="Escolha o tamanho da sua operação"
          subtitle="Comece pequeno e escale conforme cresce. Sem taxa de setup, sem multa de cancelamento."
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-[1000px] mx-auto">
          {plans.map((plan, i) => (
            <FadeIn key={plan.name} delay={i * 0.15}>
              <div
                className={`relative rounded-2xl p-6 h-full flex flex-col ${
                  plan.highlight
                    ? "bg-[#0f172a] text-white shadow-xl shadow-[#0f172a]/15 border-2 border-[#25D366]"
                    : "bg-white border border-[rgba(20,24,30,0.08)]"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#25D366] px-3 py-0.5 text-[11px] font-semibold text-white">
                    Mais popular
                  </div>
                )}

                <h3 className={`text-[15px] font-semibold mb-1 ${plan.highlight ? "text-white/80" : "text-[#64748b]"}`}>
                  {plan.name}
                </h3>
                <div className="flex items-baseline gap-1 mb-3">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className={`text-[13px] ${plan.highlight ? "text-white/60" : "text-[#8e9094]"}`}>{plan.period}</span>
                </div>
                <p className={`text-[13px] mb-5 ${plan.highlight ? "text-white/70" : "text-[#64748b]"}`}>
                  {plan.desc}
                </p>

                <ul className="space-y-2.5 mb-6 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-[13px]">
                      <svg className={`w-4 h-4 shrink-0 mt-0.5 ${plan.highlight ? "text-[#25D366]" : "text-[#25D366]"}`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/></svg>
                      <span className={plan.highlight ? "text-white/90" : "text-[#475569]"}>{f}</span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full rounded-xl py-2.5 text-[13px] font-medium transition-colors ${
                    plan.highlight
                      ? "bg-[#25D366] text-white hover:bg-[#128C7E]"
                      : "bg-[#f1f5f9] text-[#0f172a] hover:bg-[#e2e8f0]"
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
