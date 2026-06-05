"use client";

import React from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { AppShell } from "../../components/shell";
import {
  EnterpriseBanner,
  FeatureGridPremium,
  GlassPanel,
  AnimatedIntegrationCards,
  NeonDivider,
  FloatingCTA,
  GradientBorderCard,
  PremiumStatsSection,
} from "../../components/premium";

/**
 * PÁGINA /parcerias — EXEMPLO DE NOVA PÁGINA PREMIUM
 * 
 * FILOSOFIA:
 * - Use componentes premium de forma natural
 * - Mantenha estrutura limpa e responsiva
 * - Respeite identidade visual SyntexaBR
 * - Teste em mobile/tablet/desktop
 */

export default function PartnershipsPage() {
  return (
    <AppShell>
      <main className="relative w-full overflow-x-hidden bg-white text-[#0f172a]">
        
        {/* ===== HERO ===== */}
        <section className="relative min-h-screen flex items-center justify-center px-5 py-24">
          <div className="mx-auto w-full max-w-4xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="mb-6 inline-flex rounded-full border border-[rgba(5,150,105,0.2)] bg-[rgba(5,150,105,0.05)] px-4 py-1.5"
            >
              <svg
                className="w-4 h-4 text-[#059669] mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707l-2-2A1 1 0 0015 7h-1z" />
              </svg>
              <span className="text-sm font-medium text-[#059669]">
                Parcerias Estratégicas
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              className="text-4xl md:text-5xl font-medium leading-tight"
            >
              Crescer Juntos em IA
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-6 text-xl text-[#64748b] max-w-2xl mx-auto"
            >
              Integre a plataforma SyntexaBR em seu produto e ganhe acesso a um modelo de IA enterprise, diferenciado e otimizado para Portugal e Brasil.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="mt-8 flex flex-wrap gap-4 justify-center"
            >
              <a
                href="#programas"
                className="rounded-lg bg-[#059669] px-6 py-3 font-medium text-white hover:bg-[#047857] transition-colors"
              >
                Ver Programas
              </a>
              <a
                href="#contato"
                className="rounded-lg border border-[rgba(15,23,42,0.1)] px-6 py-3 font-medium hover:bg-[rgba(15,23,42,0.03)] transition-colors"
              >
                Fale Conosco
              </a>
            </motion.div>
          </div>
        </section>

        {/* ===== TIPO DE PARCERIAS ===== */}
        <section className="relative py-24 px-5">
          <NeonDivider variant="medium" />
          
          <div className="mx-auto max-w-6xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="mb-12 text-center"
            >
              <h2 className="text-3xl font-medium">Programas de Parceria</h2>
              <p className="mt-4 text-lg text-[#64748b] max-w-2xl mx-auto">
                Escolha o modelo que melhor se encaixa em seu negócio
              </p>
            </motion.div>

            {/* Cards Premium */}
            <FeatureGridPremium
              columns={3}
              features={[
                {
                  icon: StarIcon,
                  title: "Integração Técnica",
                  description: "API completa para integrar SyntexaBR em seu produto",
                  badge: "Popular",
                },
                {
                  icon: BuggsIcon,
                  title: "Reseller",
                  description: "Revenda a plataforma e ganhe margem em cada cliente",
                  badge: "Lucro",
                },
                {
                  icon: BuildingIcon,
                  title: "Enterprise",
                  description: "Solução customizada para grandes organizações",
                  badge: "Dedicado",
                },
              ]}
            />
          </div>
        </section>

        {/* ===== STATS ===== */}
        <section className="relative py-24 px-5 bg-[#f8fafc]">
          <PremiumStatsSection
            title="Crescimento de Parcerias"
            description="Números reais de nossos parceiros"
            stats={[
              {
                value: "—",
                label: "Parceiros Ativos",
                description: "Dados reais em breve",
              },
              {
                value: "—",
                label: "Usuários Mensais",
                description: "Dados reais em breve",
              },
              {
                value: "—",
                label: "Uptime SLA",
                description: "Dados reais em breve",
              },
              {
                value: "—",
                label: "Latência Média",
                description: "Dados reais em breve",
              },
            ]}
          />
        </section>

        {/* ===== INTEGRAÇÕES ===== */}
        <section id="programas" className="relative py-24 px-5">
          <NeonDivider />
          
          <div className="mx-auto max-w-6xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="mb-12 text-center"
            >
              <h2 className="text-3xl font-medium">Integrações Disponíveis</h2>
              <p className="mt-4 text-lg text-[#64748b]">
                Conecte facilmente com seus sistemas
              </p>
            </motion.div>

            <AnimatedIntegrationCards
              integrations={[
                { title: "REST API", badge: "Production Ready" },
                { title: "GraphQL", badge: "Beta" },
                { title: "Webhooks", badge: "Production Ready" },
                { title: "SDK Node.js", badge: "Production Ready" },
                { title: "SDK Python", badge: "Production Ready" },
                { title: "Zapier", badge: "Connected" },
                { title: "n8n", badge: "Connected" },
                { title: "Make", badge: "Coming Soon" },
              ]}
            />
          </div>
        </section>

        {/* ===== BANNER ===== */}
        <section className="relative py-24 px-5">
          <div className="mx-auto max-w-6xl">
            <EnterpriseBanner
              title="Programa Enterprise Premium"
              subtitle="Para organizações que precisam de suporte dedicado, SLA garantido e customizações específicas."
              ctaText="Solicitar Demonstração"
              ctaHref="#contato"
              secondaryCtaText="Ver Documentação"
              secondaryCtaHref="/docs"
            />
          </div>
        </section>

        {/* ===== BENEFÍCIOS COM GLASSPANEL ===== */}
        <section className="relative py-24 px-5 bg-[#f8fafc]">
          <div className="mx-auto max-w-6xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true 
              }}
              transition={{ duration: 0.5 }}
              className="mb-12 text-center"
            >
              <h2 className="text-3xl font-medium">Por que Parceiros Escolhem SyntexaBR</h2>
            </motion.div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  title: "Modelo Proprietário",
                  description: "IA diferenciada otimizada para contexto português e brasileiro",
                },
                {
                  title: "Latência Ultra-Baixa",
                  description: "< 200ms garantido com infraestrutura distribuída",
                },
                {
                  title: "99.9% SLA",
                  description: "Uptime garantido com suporte técnico 24/7",
                },
                {
                  title: "Integração Simples",
                  description: "APIs modernas, SDKs completos, documentação excelente",
                },
                {
                  title: "Escalabilidade",
                  description: "Suporta milhões de requisições simultâneas",
                },
                {
                  title: "Segurança Premium",
                  description: "Compliance LGPD, GDPR, HIPAA certified",
                },
              ].map((benefit, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                >
                  <GlassPanel
                    title={benefit.title}
                    subtitle={benefit.description}
                    border={true}
                    glowIntensity="subtle"
                  />
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== CONTACT CTA ===== */}
        <section id="contato" className="relative py-24 px-5">
          <div className="mx-auto max-w-4xl text-center">
            <GradientBorderCard
              title="Vamos Conversar?"
              description="Entre em contato com nosso time de parcerias"
            >
              <div className="flex flex-col gap-3 sm:flex-row justify-center">
                <a
                  href="mailto:parceiros@syntexabr.com.br"
                  className="rounded-lg bg-[#059669] px-6 py-3 font-medium text-white hover:bg-[#047857] transition-colors"
                >
                  parceiros@syntexabr.com.br
                </a>
                <a
                  href="https://calendly.com/syntexabr"
                  className="rounded-lg border border-[rgba(15,23,42,0.1)] px-6 py-3 font-medium hover:bg-[rgba(15,23,42,0.03)] transition-colors"
                >
                  Agendar Reunião
                </a>
              </div>
            </GradientBorderCard>
          </div>
        </section>

        {/* ===== FLOATING CTA ===== */}
        <FloatingCTA
          title="Interessado em Parceria?"
          subtitle="Entre em contato conosco agora"
          primaryText="Enviar E-mail"
          secondaryText="Agendar Reunião"
        />

      </main>
    </AppShell>
  );
}

// Ícones placeholder (substitua com ícones reais)
function StarIcon(props) {
  return (
    <svg {...props} fill="currentColor" viewBox="0 0 20 20">
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  );
}

function BuggsIcon(props) {
  return (
    <svg {...props} fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 11.894 1.789l-1.33.665 2.331 2.331a1 1 0 11-1.414 1.414L15.88 9.117l.665 1.33a1 1 0 11-1.789.894l-.8-1.599L11 14.677V17a1 1 0 11-2 0v-2.323l-3.954-1.582-1.599.8a1 1 0 11-.894-1.789l1.33-.665-2.331-2.331a1 1 0 111.414-1.414L4.12 10.883l-.665-1.33a1 1 0 111.789-.894l.8 1.599L9 5.323V3a1 1 0 011-1zm0 5.823l-3.58 1.79a1 1 0 100 1.776L10 12.977l3.58-1.789a1 1 0 000-1.776L10 7.823z" clipRule="evenodd" />
    </svg>
  );
}

function BuildingIcon(props) {
  return (
    <svg {...props} fill="currentColor" viewBox="0 0 20 20">
      <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
    </svg>
  );
}
