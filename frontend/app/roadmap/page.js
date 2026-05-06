import React from "react";

export const metadata = {
  title: "Roadmap Syntexa",
  description:
    "Roadmap oficial da Syntexa AI para lançamento, SEO, monetização inicial e escala progressiva da plataforma.",
  keywords: [
    "roadmap syntexa",
    "lançamento syntexa",
    "seo syntexa",
    "plano de execução",
    "100 mil simultâneos",
  ],
  alternates: { canonical: "/roadmap" },
};

const PHASES = [
  {
    window: "0-30 dias",
    focus: "Lançamento e conversão inicial",
    deliverables: [
      "Refino de onboarding e redução de abandono no primeiro uso",
      "CTAs comerciais em páginas estratégicas para acelerar upgrade",
      "Ajustes de SEO técnico (metadata, sitemap, docs e rota roadmap)",
    ],
  },
  {
    window: "31-60 dias",
    focus: "Monetização e retenção",
    deliverables: [
      "Aumento da conversão de usuário ativo para pagante",
      "Aprimoramento dos planos e proposta de valor por perfil",
      "Instrumentação de coortes de retenção semanal/mensal",
    ],
  },
  {
    window: "61-90 dias",
    focus: "Escala com previsibilidade",
    deliverables: [
      "Repetição de canal de aquisição vencedor com CAC controlado",
      "Hardening operacional e monitorização contínua de estabilidade",
      "Evidência de tração para expansão comercial e institucional",
    ],
  },
  {
    window: "4-12 meses",
    focus: "Expansão orientada a dados",
    deliverables: [
      "Evolução gradual da capacidade até referência de 100 mil simultâneos",
      "Contratação por marcos de receita, retenção e confiabilidade",
      "Escala nacional mantendo custo operacional previsível",
    ],
  },
];

export default function RoadmapPage() {
  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
      <header className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-700">
          Roadmap oficial
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-zinc-900">Roadmap Syntexa AI</h1>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600">
          Plano de execução para lançar rápido, subir no SEO, converter usuários e escalar a plataforma com estabilidade.
        </p>
      </header>

      <section className="mt-6 grid gap-4">
        {PHASES.map((phase) => (
          <article key={phase.window} className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-zinc-900">{phase.window}</h2>
              <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-700">{phase.focus}</span>
            </div>
            <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-zinc-700">
              {phase.deliverables.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>
    </main>
  );
}
