"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import React from "react";
import { InfrastructureVisual } from "../components/infrastructure-visual";

const MODULES = [
  { title: "Runtime Infrastructure", desc: "Motor neural proprietário com inferência quantizada 4-bit e execução distribuída em GPU clusters.", status: "active" },
  { title: "Distributed Inference", desc: "Orquestração de tensores em múltiplos nós com roteamento inteligente e balanceamento de carga.", status: "active" },
  { title: "Autonomous Agents", desc: "Sistemas de agentes autônomos com capacidade de orquestração, planejamento e execução de tarefas.", status: "active" },
  { title: "Multimodal Systems", desc: "Processamento integrado de texto, imagem, áudio e documentos em pipeline unificado.", status: "active" },
  { title: "Cognitive Orchestration", desc: "Camada de orquestração cognitiva que gerencia contexto, memória e raciocínio em tempo real.", status: "active" },
  { title: "Voice Intelligence", desc: "Transcrição neural em tempo real e síntese de voz com latência inferior a 200ms.", status: "active" },
  { title: "Document Intelligence", desc: "Análise semântica de PDF, DOCX, XLSX com extração estruturada e compreensão contextual.", status: "active" },
  { title: "GPU Runtime", desc: "Infraestrutura de GPU otimizada para inferência de modelos 20B+ parâmetros com escalabilidade automática.", status: "active" },
  { title: "Secure Sovereign Architecture", desc: "Arquitetura soberana com execução local, criptografia end-to-end e isolamento de dados.", status: "active" },
  { title: "Quantum Research Layer", desc: "Camada experimental de pesquisa com QPanda3 para otimização probabilística e simulações computacionais.", status: "standby" },
  { title: "Edge Execution", desc: "Deploy de modelos em edge nodes Cloudflare para execução distribuída global com latência mínima.", status: "standby" },
  { title: "Enterprise Infrastructure", desc: "Infraestrutura enterprise-grade com SLA, audit trails e compliance para operações institucionais.", status: "standby" },
];

const PLANS = [
  { name: "Syntexa Core", price: "Acesso Controlado", desc: "Rollout controlado de infraestrutura cognitiva. Acesso early-access com capacidades fundamentais de inferência neural." },
  { name: "Syntexa Studio", price: "Acesso Controlado", desc: "Ambiente de desenvolvimento com APIs multimodais, voice intelligence e document processing avançado." },
  { name: "Syntexa Nexus", price: "Acesso Controlado", desc: "Orquestração distribuída, agentes autônomos e deploy em GPU clusters com escalabilidade dinâmica." },
  { name: "Syntexa Enterprise", price: "Contato", desc: "Infraestrutura dedicada, compliance enterprise, SLA garantido e integração com sistemas institucionais." },
];

export default function HomePage() {
  return (
    <main className="relative min-h-[100dvh] w-full overflow-x-hidden overflow-y-auto bg-[#0a0a0b] text-[#e8e8ec] [scroll-behavior:smooth]">
      {/* Background infrastructure grid */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 infrastructure-grid opacity-30" />
        <div className="hero-fog-a pointer-events-none absolute inset-0" />
      </div>

      {/* Navigation — Dark Glass */}
      <header className="home-nav-float fixed left-1/2 top-4 z-40 w-[min(94%,1280px)] -translate-x-1/2 rounded-[20px] border border-[rgba(255,255,255,0.06)] px-5 py-3 shadow-[0_4px_32px_rgba(0,0,0,0.3)] backdrop-blur-[24px]">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#6366f1] to-[#4f46e5]">
              <span className="text-[11px] font-bold text-white">SX</span>
            </div>
            <span className="text-[13px] font-medium tracking-[0.15em] text-[#e8e8ec]">SYNTEXA</span>
          </Link>
          <nav className="hidden items-center gap-1 lg:flex">
            {["Runtime", "Infraestrutura", "Documentos", "Voz", "Chat"].map((item) => (
              <Link
                key={item}
                href={item === "Chat" ? "/chat" : `#${item.toLowerCase()}`}
                className="rounded-lg px-3 py-1.5 text-[12.5px] text-[#9a9aa0] transition-colors duration-200 hover:bg-[rgba(255,255,255,0.04)] hover:text-[#e8e8ec]"
              >
                {item}
              </Link>
            ))}
          </nav>
          <div className="flex shrink-0 items-center gap-3">
            <Link
              href="/chat"
              className="rounded-full bg-gradient-to-r from-[#6366f1] to-[#4f46e5] px-5 py-2 text-[12px] font-medium tracking-wide text-white shadow-[0_0_16px_rgba(99,102,241,0.2)] transition-all duration-200 hover:shadow-[0_0_24px_rgba(99,102,241,0.3)]"
            >
              Console
            </Link>
            <div className="flex items-center gap-1.5 rounded-full border border-[rgba(255,255,255,0.06)] bg-[rgba(16,185,129,0.1)] px-2.5 py-1">
              <span className="h-[5px] w-[5px] rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.4)]" />
              <span className="text-[10px] font-medium text-emerald-400 tracking-wide">SOBERANA</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section — Cinematic Infrastructure */}
      <section className="relative z-10 flex min-h-[100dvh] flex-col items-center justify-center px-5 pt-20">
        <div className="mx-auto flex w-full max-w-[1200px] flex-col items-center text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="mb-6 flex items-center gap-2 rounded-full border border-[rgba(99,102,241,0.15)] bg-[rgba(99,102,241,0.05)] px-4 py-1.5"
          >
            <span className="h-[6px] w-[6px] rounded-full bg-[#6366f1] shadow-[0_0_8px_rgba(99,102,241,0.4)]" />
            <span className="text-[11px] font-medium tracking-[0.15em] text-[#818cf8] uppercase">
              Infraestrutura Cognitiva Soberana
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
            className="max-w-4xl text-[2.5rem] font-medium leading-[1.1] tracking-[-0.04em] text-[#e8e8ec] md:text-[4rem] lg:text-[4.5rem] text-glow"
          >
            Infraestrutura Cognitiva para{" "}
            <span className="text-gradient">Inteligência Soberana</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.25 }}
            className="mt-6 max-w-2xl text-[16px] leading-relaxed text-[#9a9aa0] md:text-[18px]"
          >
            Runtime neural distribuído com inferência híbrida, orquestração autônoma e 
            processamento multimodal. Proprietário. Escalável. Institucional.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-8 flex flex-wrap items-center justify-center gap-3"
          >
            <Link
              href="/chat"
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
          className="mt-8 w-full max-w-[1000px]"
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
            <span className="h-[1px] w-8 bg-[rgba(99,102,241,0.4)]" />
            <span className="text-[11px] font-medium tracking-[0.15em] text-[#6366f1] uppercase">Arquitetura</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.03em] text-[#e8e8ec] md:text-[2.5rem]">
            Módulos da Plataforma
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#9a9aa0]">
            Sistema modular de inteligência computacional com runtime neural proprietário,
            orquestração distribuída e processamento multimodal integrado.
          </p>
        </motion.div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((mod, i) => (
            <motion.div
              key={mod.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="syntexa-card group relative rounded-2xl border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] p-6 transition-all duration-300 hover:border-[rgba(99,102,241,0.15)] hover:bg-[rgba(255,255,255,0.03)]"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(99,102,241,0.08)]">
                  <div className={`h-2 w-2 rounded-full ${
                    mod.status === "active" ? "status-active" : "status-standby"
                  }`} />
                </div>
                <span className="text-[10px] font-medium tracking-[0.1em] text-[#6a6a70] uppercase">
                  {mod.status === "active" ? "Operacional" : "Standby"}
                </span>
              </div>
              <h3 className="text-[15px] font-medium text-[#e8e8ec]">{mod.title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-[#9a9aa0]">{mod.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Technical Specs Banner */}
      <section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-16">
        <div className="syntexa-card rounded-3xl border border-[rgba(99,102,241,0.1)] bg-gradient-to-br from-[rgba(99,102,241,0.04)] to-[rgba(139,92,246,0.02)] p-8 md:p-12">
          <div className="grid gap-8 md:grid-cols-4">
            {[
              { value: "32B+", label: "Parâmetros Neurais", sub: "Quantização 4-bit NF4" },
              { value: "<200ms", label: "Latência de Voz", sub: "Streaming em tempo real" },
              { value: "GPU", label: "Execução Distribuída", sub: "Multi-node orchestration" },
              { value: "100%", label: "Runtime Soberano", sub: "Sem dependência externa" },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="text-center"
              >
                <div className="text-[2rem] font-medium tracking-[-0.03em] text-[#e8e8ec] md:text-[2.5rem]">
                  {stat.value}
                </div>
                <div className="mt-1 text-[13px] font-medium text-[#9a9aa0]">{stat.label}</div>
                <div className="text-[11px] text-[#6a6a70]">{stat.sub}</div>
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
            <span className="h-[1px] w-8 bg-[rgba(99,102,241,0.4)]" />
            <span className="text-[11px] font-medium tracking-[0.15em] text-[#6366f1] uppercase">Infraestrutura</span>
          </div>
          <h2 className="text-[2rem] font-medium tracking-[-0.03em] text-[#e8e8ec] md:text-[2.5rem]">
            Camadas de Acesso
          </h2>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#9a9aa0]">
            Rollout controlado de early-access à infraestrutura cognitiva. 
            Escalabilidade modular conforme necessidade operacional.
          </p>
        </motion.div>

        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {PLANS.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="syntexa-card relative rounded-2xl border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] p-6"
            >
              <h3 className="text-[15px] font-medium text-[#e8e8ec]">{plan.name}</h3>
              <div className="mt-2 text-[12px] font-medium tracking-wide text-[#6366f1]">{plan.price}</div>
              <p className="mt-4 text-[13px] leading-relaxed text-[#9a9aa0]">{plan.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-[rgba(255,255,255,0.05)] bg-[#0a0a0b] px-5 py-12">
        <div className="mx-auto flex w-full max-w-[1200px] flex-col items-center justify-between gap-6 md:flex-row">
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-[#6366f1] to-[#4f46e5]">
              <span className="text-[10px] font-bold text-white">SX</span>
            </div>
            <span className="text-[13px] font-medium tracking-[0.1em] text-[#9a9aa0]">SYNTEXA</span>
          </div>
          <p className="text-[12px] text-[#6a6a70]">
            Infraestrutura Cognitiva Soberana — Runtime Neural Distribuído
          </p>
          <div className="flex items-center gap-4">
            <span className="h-[5px] w-[5px] rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.4)]" />
            <span className="text-[11px] text-[#6a6a70]">Todos os sistemas operacionais</span>
          </div>
        </div>
      </footer>
    </main>
  );
}

