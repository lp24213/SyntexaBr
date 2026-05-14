import React from "react";
import { AppShell } from "../../components/shell";

export const metadata = {
  title: "Documentação Syntexa",
  description:
    "Documentação oficial da Syntexa AI: plataforma, roadmap, capacidade de escala, segurança, integrações e implantação institucional.",
  keywords: [
    "documentação syntexa",
    "syntexa ai",
    "roadmap syntexa",
    "capacidade 100 mil simultâneos",
    "implantação institucional",
    "api syntexa",
  ],
  alternates: {
    canonical: "/docs",
  },
};

const DOC_SECTIONS = [
  {
    title: "Visão geral da plataforma",
    body: "A Syntexa AI combina chat, geração multimodal e exportação de conteúdo para formatos profissionais. O objetivo é reduzir o tempo entre ideia e material final utilizável.",
  },
  {
    title: "Roadmap de execução",
    body: "O roadmap atual prioriza lançamento comercial, conversão de usuários ativos para planos pagos e escala progressiva com governança de custos.",
  },
  {
    title: "Capacidade de escala",
    body: "A meta de capacidade operacional da plataforma é suportar até 100 mil usuários simultâneos com estratégia de escala por camadas, testes de stress e monitorização contínua.",
  },
  {
    title: "Segurança e operação",
    body: "A operação inclui controles administrativos, políticas de acesso, observabilidade e gestão de risco para manter disponibilidade, estabilidade e segurança institucional.",
  },
  {
    title: "Implantação e adoção institucional",
    body: "A Syntexa oferece fluxos para educação, governo e organizações que demandam padronização de uso, controle de acesso e distribuição técnica assistida.",
  },
];

export default function DocsPage() {
  const ldJson = {
    "@context": "https://schema.org",
    "@type": "TechArticle",
    headline: "Documentação Oficial Syntexa AI",
    description:
      "Conteúdo técnico e institucional da plataforma Syntexa AI com foco em operação, roadmap e escala.",
    author: {
      "@type": "Organization",
      name: "SyntexaBR",
    },
    publisher: {
      "@type": "Organization",
      name: "SyntexaBR",
    },
    mainEntityOfPage: "https://syntexabr.com.br/docs",
    inLanguage: "pt-BR",
  };

  return (
    <AppShell>
    <main className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ldJson) }} />

      <header className="rounded-3xl border border-white/80 bg-white/75 p-6 shadow-[0_20px_65px_rgba(148,163,184,0.2)] backdrop-blur-xl">
        <p className="inline-flex rounded-full border border-violet-200/70 bg-violet-50/80 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-violet-700">
          Documentação oficial
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-zinc-900">Syntexa AI</h1>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600">
          Central de documentação pública da Syntexa para facilitar indexação orgânica, consulta institucional e
          comunicação de capacidade técnica da plataforma.
        </p>
      </header>

      <section className="mt-6 grid gap-4">
        {DOC_SECTIONS.map((section) => (
          <article key={section.title} className="rounded-2xl border border-white/85 bg-white/75 p-5 shadow-[0_12px_36px_rgba(148,163,184,0.16)]">
            <h2 className="text-lg font-semibold text-zinc-900">{section.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-700">{section.body}</p>
          </article>
        ))}
      </section>
      <section className="mt-6 rounded-2xl border border-emerald-200/80 bg-emerald-50/85 p-5">
        <h2 className="text-lg font-semibold text-zinc-900">Roadmap público para SEO</h2>
        <p className="mt-2 text-sm text-zinc-700">
          A versão pública do roadmap de lançamento está disponível para indexação em{" "}
          <a href="/roadmap" className="font-semibold text-emerald-700 underline underline-offset-2">
            /roadmap
          </a>
          .
        </p>
      </section>
    </main>
    </AppShell>
  );
}
