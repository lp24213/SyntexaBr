"use client";

import React from "react";
import { AppShell } from "../../components/shell";
import { getClientLocale, t } from "../../lib/i18n";

function getPHASES(locale) {
  return [
    {
      window: t("roadmapPhase1Window", locale),
      focus: t("roadmapPhase1Focus", locale),
      deliverables: [
        t("roadmapPhase1Item1", locale),
        t("roadmapPhase1Item2", locale),
        t("roadmapPhase1Item3", locale),
      ],
    },
    {
      window: t("roadmapPhase2Window", locale),
      focus: t("roadmapPhase2Focus", locale),
      deliverables: [
        t("roadmapPhase2Item1", locale),
        t("roadmapPhase2Item2", locale),
        t("roadmapPhase2Item3", locale),
      ],
    },
    {
      window: t("roadmapPhase3Window", locale),
      focus: t("roadmapPhase3Focus", locale),
      deliverables: [
        t("roadmapPhase3Item1", locale),
        t("roadmapPhase3Item2", locale),
        t("roadmapPhase3Item3", locale),
      ],
    },
    {
      window: t("roadmapPhase4Window", locale),
      focus: t("roadmapPhase4Focus", locale),
      deliverables: [
        t("roadmapPhase4Item1", locale),
        t("roadmapPhase4Item2", locale),
        t("roadmapPhase4Item3", locale),
      ],
    },
  ];
}

export default function RoadmapPage() {
  const locale = getClientLocale();
  const PHASES = getPHASES(locale);
  return (
    <AppShell>
    <main className="py-10">
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
    </AppShell>
  );
}
