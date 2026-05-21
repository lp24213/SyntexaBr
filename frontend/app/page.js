"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import React from "react";
import { AppShell } from "../components/shell";
import { InfrastructureVisual } from "../components/infrastructure-visual";
import { DownloadSection } from "../components/download-section";
import { getClientLocale, t } from "../lib/i18n";
import { encryptedPath } from "../lib/routes";

const MODULES = [
  { title: "Chat Inteligente", desc: "Converse sobre qualquer assunto. A Syntexa entende contexto, memória e pode pesquisar na web em tempo real.", status: "active" },
  { title: "Respostas na Velocidade da Luz", desc: "Processamento distribuído em servidores de alta performance para que você não espere por nada.", status: "active" },
  { title: "Agentes Inteligentes", desc: "Crie assistentes especializados que executam tarefas complexas sozinhos, do planejamento à execução.", status: "active" },
  { title: "Crie com IA", desc: "Gere imagens, vídeos, músicas e áudio com descrições em português. Sua criatividade é o limite.", status: "active" },
  { title: "Memória e Contexto", desc: "A Syntexa lembra das conversas, entende nuances e mantém o fio da meada em diálogos longos.", status: "active" },
  { title: "Fale com Ela", desc: "Dite suas perguntas e ouça as respostas. Reconhecimento e síntese de voz em português brasileiro.", status: "active" },
  { title: "Leitura de Documentos", desc: "Envie PDFs, planilhas e textos. A Syntexa resume, extrai informações e responde sobre o conteúdo.", status: "active" },
  { title: "Potência Real", desc: "Infraestrutura de última geração com GPUs dedicadas para processar bilhões de parâmetros em segundos.", status: "active" },
  { title: "Segurança & Privacidade", desc: "Seus dados ficam com você. Criptografia completa e nada enviado para empresas estrangeiras.", status: "active" },
  { title: "Pesquisa Avançada", desc: "Ferramentas de pesquisa científica e otimização para projetos complexos e inovação.", status: "standby" },
  { title: "Execução Rápida", desc: "Respostas instantâneas onde você estiver, com tecnologia de ponta em servidores distribuídos.", status: "standby" },
  { title: "Para Empresas", desc: "Contratos com garantia de funcionamento, relatórios completos e conformidade com a LGPD.", status: "standby" },
];

const PLANS = [
  { name: "Gratuito", price: "R$ 0/mês", desc: "120 mensagens por dia para experimentar. Chat, pesquisa na web e respostas inteligentes — sem cartão." },
  { name: "Básico", price: "R$ 39/mês", desc: "500 mensagens/mês, upload de arquivos e respostas mais completas. Ideal para estudantes e freelancers." },
  { name: "Médio", price: "R$ 99/mês", desc: "Mensagens ilimitadas, geração de imagem/vídeo/áudio, código e contexto estendido. Para profissionais." },
  { name: "Master", price: "R$ 199/mês", desc: "Tudo ilimitado + agentes avançados, suporte prioritário, múltiplos usuários e ferramentas empresariais." },
];

export default function HomePage() {
  const locale = getClientLocale();
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
                Inteligência Artificial Brasileira
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
              className="max-w-4xl text-[2.5rem] font-medium leading-[1.12] tracking-[-0.03em] text-[#0f172a] md:text-[3.5rem] lg:text-[4rem]"
            >
              Sua Assistente de IA, Feita no Brasil
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.25 }}
              className="mt-6 max-w-2xl text-[16px] leading-relaxed text-[#64748b] md:text-[18px]"
            >
              Uma assistente que entende português de verdade. Pode pesquisar na internet,
              gerar imagens, escrever códigos e ajudar em qualquer área — tudo de forma segura.
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
                Acessar Console
              </Link>
              <Link
                href="#infraestrutura"
                className="syntexa-btn-outline rounded-full px-7 py-3 text-[13px] font-medium"
              >
                Explorar Arquitetura
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
            <span className="text-[11px] font-medium tracking-[0.12em] text-[#475569] uppercase">Arquitetura</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
            Módulos da Plataforma
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#64748b]">
            Tudo o que você precisa em um só lugar: chat inteligente, criação de conteúdo,
            análise de documentos e assistência técnica — sempre em português.
          </p>
        </motion.div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((mod, i) => (
            <motion.div
              key={mod.title}
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
                  {mod.status === "active" ? "Operacional" : "Standby"}
                </span>
              </div>
              <h3 className="text-[15px] font-medium text-[#0f172a]">{mod.title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-[#64748b]">{mod.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Technical Specs Banner */}
      <section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-16">
        <div className="syntexa-card rounded-3xl border border-[rgba(15,23,42,0.06)] bg-[#f8fafc] p-8 md:p-12">
          <div className="grid gap-8 md:grid-cols-4">
            {[
              { value: "13B+", label: "Parâmetros do Modelo", sub: "Arquitetura Transformer própria" },
              { value: "<200ms", label: "Resposta por Voz", sub: "Fale com a Syntexa naturalmente" },
              { value: "GPU", label: "Processamento Rápido", sub: "Respostas em segundos, não minutos" },
              { value: "100%", label: "Dados Protegidos", sub: "Nenhuma informação vendida a terceiros" }
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="text-center"
              >
                <div className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
                  {stat.value}
                </div>
                <div className="mt-1 text-[13px] font-medium text-[#334155]">{stat.label}</div>
                <div className="text-[11px] text-[#94a3b8]">{stat.sub}</div>
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
            <span className="text-[11px] font-medium tracking-[0.12em] text-[#475569] uppercase">Infraestrutura</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.02em] text-[#0f172a] md:text-[2.5rem]">
            Camadas de Acesso
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#64748b]">
            Escolha o plano que faz sentido para você. Pode começar de graça e subir
            de nível conforme suas necessidades crescem.
          </p>
        </motion.div>

        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {PLANS.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="syntexa-card relative rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-6"
            >
              <h3 className="text-[15px] font-medium text-[#0f172a]">{plan.name}</h3>
              <div className="mt-2 text-[12px] font-medium tracking-wide text-[#475569]">{plan.price}</div>
              <p className="mt-4 text-[13px] leading-relaxed text-[#64748b]">{plan.desc}</p>
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

