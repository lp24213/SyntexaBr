"use client";

import React, { useCallback, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "./ui/button";
import { multimodalExportDocx, multimodalExportPdf } from "../lib/api";

function Section({ id, title, children }) {
  return (
    <section
      id={id}
      className="plan-chapter rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm sm:p-6 print:break-inside-avoid print:shadow-none"
    >
      <h2 className="text-xl font-semibold text-zinc-900">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-relaxed text-zinc-700">{children}</div>
    </section>
  );
}

function MetricCard({ label, value, note }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 print:break-inside-avoid">
      <p className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-zinc-900">{value}</p>
      {note ? <p className="mt-1 text-xs text-zinc-600">{note}</p> : null}
    </div>
  );
}

/** Conteúdo único: usado na página e na exportação PDF/Word (seed deck estendido). */
const PLAN_DOCUMENT = {
  title: "Syntexa — Plano de Negócios e Roadmap de Execução",
  get subtitle() {
    return (
      "Plano vivo para execução e lançamento · " +
      new Date().toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      })
    );
  },
  chapters: [
    {
      id: "intro",
      title: "1. Contexto atual e foco de lançamento",
      paragraphs: [
        "A Syntexa está em fase early-stage com produto no ar, melhorias contínuas e stack operacional ativa. Este plano foi ajustado para acelerar lançamento comercial com disciplina de execução.",
        "O objetivo agora é transformar evolução técnica em receita previsível: foco em aquisição inicial, retenção e conversão dos primeiros usuários pagantes com ciclos curtos de entrega.",
      ],
      bullets: [
        "Status atual: produto no ar, com funcionalidades críticas já entregues.",
        "Foco imediato: converter capacidade técnica em tração comercial real.",
        "Roadmap é operacional e executado no sistema, sem dependência de documento externo.",
      ],
    },
    {
      id: "founder",
      title: "2. Fundador e capacidade de execução",
      paragraphs: [
        "Luis Paulo de Oliveira é o fundador solo e builder principal da Syntexa. Até o momento, a construção de produto, integração técnica, decisões de roadmap e execução operacional foram conduzidas majoritariamente por ele, com uso intensivo de ferramentas de desenvolvimento assistido para aumentar velocidade sem inflar estrutura de custos.",
        "A tese de equipe para a fase seed é iniciar com núcleo enxuto e altamente técnico, contratando por marcos: primeiro engenharia full-stack para throughput, depois produto/growth para aceleração de aquisição e, por fim, suporte/comercial conforme sinais de repetibilidade.",
      ],
      bullets: [
        "Perfil atual: founder-led, alto envolvimento técnico-operacional.",
        "Vantagem: velocidade de iteração e baixo burn no pré-tração.",
        "Risco conhecido: concentração de execução em uma pessoa; mitigação por contratação faseada.",
      ],
    },
    {
      id: "problem",
      title: "3. Problema que estamos resolvendo",
      paragraphs: [
        "Usuários em educação e produtividade intelectual lidam com fluxo fragmentado: pedem resposta em um chat, reorganizam manualmente em outro editor e depois convertem para formatos apresentáveis. Esse ciclo gera fricção, perda de tempo e inconsistência de qualidade no resultado final.",
        "No Brasil, há uma oportunidade clara para uma camada de IA em português com foco prático: transformar diálogo em entregável útil (texto estruturado, tabela, PDF, planilha, documento) com padrão visual profissional e menor esforço operacional.",
      ],
      bullets: [
        "Dor principal: tempo alto entre “resposta” e “material final utilizável”.",
        "Dor secundária: baixa padronização visual e retrabalho de formatação.",
        "Hipótese: usuários pagam por ganho real de tempo e qualidade final.",
      ],
    },
    {
      id: "solution",
      title: "4. Produto já lançado e proposta de valor",
      paragraphs: [
        "A Syntexa já está publicada com chat multimodal, renderização estruturada de conteúdo e exportação nativa para PDF, DOCX, XLSX, CSV e TXT. O produto foi desenhado para que o usuário saia da conversa com artefato pronto, sem depender de pós-edição extensa.",
        "Além do chat, a plataforma já possui superfícies administrativas, recursos de autenticação avançada (incluindo 2FA), módulo de integrações por token e páginas especializadas para cenários educacionais. Isso estabelece base tecnológica para escalar experimentos de mercado sem reescrita estrutural.",
      ],
      bullets: [
        "Produto no ar: funcional e utilizável em ambiente real.",
        "Diferencial: pipeline de conteúdo “conversa → formato final”.",
        "Próxima meta: provar valor repetível para o primeiro nicho.",
      ],
    },
    {
      id: "tech-stack",
      title: "5. Tecnologia proprietária, código próprio e infraestrutura SyntexaBr",
      paragraphs: [
        "A SyntexaBr opera sobre stack de software desenvolvido e mantido internamente: frontend, backend, módulos de exportação, autenticação, integrações e camadas de apresentação de conteúdo. A narrativa comercial e de investimento posiciona o núcleo como propriedade intelectual e execução técnica da empresa, não como agregação de produtos de terceiros.",
        "A inferência e os serviços críticos rodam em infraestrutura sob controlo da SyntexaBr (servidor próprio / ambiente dedicado), com desenho orientado a disponibilidade, custo previsível e evolução do roadmap sem dependência de marca externa na comunicação com utilizadores e instituições.",
        "Esta arquitetura suporta a tese seed: validar produto e mercado com base em entrega própria, capacidade de iterar rapidamente e, no médio prazo, aprofundar diferenciação (formato final, UX, governança) sem reorganizar completamente a base tecnológica.",
      ],
      bullets: [
        "IP e execução: código e integrações como ativos centrais da startup.",
        "Infraestrutura: ambiente próprio para serviços em produção.",
        "Roadmap: evolução contínua do motor de produto sob controlo da equipa fundadora.",
      ],
    },
    {
      id: "scale",
      title: "6. Capacidade de escala e meta de 100 mil simultâneos",
      paragraphs: [
        "A arquitetura operacional da Syntexa foi desenhada para escalar por camadas (aplicação, filas, cache e banco), com observabilidade e hardening contínuo. O objetivo técnico do roadmap é sustentar crescimento acelerado sem sacrificar estabilidade de resposta.",
        "A meta declarada de capacidade é suportar até 100 mil utilizadores simultâneos em cenários de pico, com escalonamento progressivo por marcos de carga e validação por testes de stress recorrentes.",
      ],
      table: {
        rows: [
          ["Eixo", "Diretriz de escala", "Meta operacional"],
          ["Aplicação", "Escala horizontal e balanceamento", "Crescer mantendo latência estável"],
          ["Processamento", "Filas e execução assíncrona", "Absorver picos sem degradar experiência"],
          ["Dados", "Cache + otimização de leitura/escrita", "Sustentar alto volume concorrente"],
          ["Confiabilidade", "Monitorização e resposta a incidentes", "Alta disponibilidade em produção"],
        ],
      },
      bullets: [
        "Meta de referência: até 100 mil sessões simultâneas com plano de capacidade faseado.",
        "Validação contínua via stress tests, métricas de latência e taxa de erro.",
        "Escala orientada a custo previsível e estabilidade de produto.",
      ],
    },
    {
      id: "who",
      title: "7. ICP inicial e estratégia de segmentação",
      paragraphs: [
        "Na fase atual, a Syntexa prioriza um ICP estreito para aprendizado rápido: usuários individuais que produzem materiais com alta frequência (estudantes avançados, criadores de conteúdo educacional, professores independentes e profissionais de preparação para concursos).",
        "Institucional e enterprise permanecem no roadmap, mas não são tratados como principal vetor no curto prazo até validação robusta de ativação e retenção no segmento inicial B2C/prosumer.",
      ],
      table: {
        rows: [
          ["Segmento", "Necessidade central", "Objetivo de validação"],
          ["Prosumer educacional", "Transformar ideias em material apresentável rápido", "Ativação e retenção semanal"],
          ["Professor independente", "Criar conteúdo e relatórios com menor esforço", "Uso recorrente de exportações"],
          ["Concurseiro / estudante intensivo", "Organizar estudo em planos e tabelas", "Conversão de uso gratuito para pago"],
        ],
      },
      bullets: [
        "Regra da fase: profundidade em 1-2 nichos antes de expandir.",
        "Métrica de sucesso: usuários que retornam por valor, não por curiosidade.",
      ],
    },
    {
      id: "gtm",
      title: "8. Go-to-market de validação (primeiros usuários)",
      paragraphs: [
        "A aquisição inicial será founder-led e orientada a aprendizado, não a escala publicitária. Canais prioritários: conteúdo orgânico de demonstração, comunidades de estudo, outreach direto e landing pages com casos de uso específicos (ex.: cronograma, tabela financeira, resumo acadêmico, relatório).",
        "Cada canal será medido por custo de aquisição incremental, taxa de ativação no primeiro dia e retenção em 7 e 30 dias. O objetivo é identificar rapidamente o canal com melhor relação CAC inicial / retenção antes de ampliar investimento.",
      ],
      bullets: [
        "Fase 1: aquisição manual + entrevistas curtas com usuários.",
        "Fase 2: loops de referência e conteúdo baseado em casos reais.",
        "Fase 3: performance paga apenas após sinal de retenção consistente.",
      ],
    },
    {
      id: "traction",
      title: "9. Métricas de tração que importam nesta fase",
      paragraphs: [
        "Como startup sem clientes consolidados, a Syntexa adota uma disciplina de tração adequada ao estágio: evidência de uso ativo, frequência de retorno, qualidade percebida e primeiros pagamentos recorrentes em pequena escala.",
        "As metas seed devem focar menos em volume bruto e mais em comportamento de coorte: quem ativa, quem retorna, quem paga e por quê. Isso reduz risco de crescimento artificial sem base real.",
      ],
      table: {
        rows: [
          ["Métrica", "Definição", "Meta de estágio seed"],
          ["Ativação D1", "Usuário que conclui primeira sessão útil", "Aumentar de forma contínua por sprint"],
          ["Retenção W1/W4", "Retorno semanal e mensal por coorte", "Sinal de hábito antes de escalar mídia"],
          ["Conversão inicial", "Uso ativo -> plano pago", "Primeiras dezenas de pagantes consistentes"],
          ["Engajamento de export", "Uso real de PDF/Word/Excel", "Validar valor prático do produto"],
        ],
      },
    },
    {
      id: "business-model",
      title: "10. Modelo de negócio e monetização inicial",
      paragraphs: [
        "O modelo principal é assinatura SaaS com planos públicos já definidos, iniciando por B2C/prosumer. Nesta fase, o objetivo da monetização é validar disposição de pagamento e elasticidade de preço, não maximizar receita de curto prazo.",
        "A camada de integrações por API e fluxo institucional continua como opcional de médio prazo. Só será priorizada comercialmente após sinais claros de repetibilidade no core B2C, evitando dispersão estratégica.",
      ],
      bullets: [
        "Receita inicial: assinaturas mensais com desconto estudantil quando aplicável.",
        "Teste contínuo: preço, limite de uso e proposta por plano.",
        "Disciplina: priorizar LTV potencial e retenção sobre desconto excessivo.",
      ],
    },
    {
      id: "roadmap",
      title: "11. Roadmap de execução para lançamento (0-90 dias + 12 meses)",
      paragraphs: [
        "O roadmap foi atualizado para ritmo de lançamento: consolidar o que já está funcional, remover gargalos de conversão e fechar o ciclo entre produto, aquisição e monetização.",
        "A lógica de execução é semanal: cada sprint deve gerar ganho mensurável em ativação, retenção ou conversão, com prioridade absoluta para funcionalidades que impactam receita.",
      ],
      table: {
        rows: [
          ["Janela", "Prioridade", "Entrega esperada", "Status"],
          ["0-30 dias", "Conversão e onboarding", "Melhorar fluxo de cadastro/login, reduzir abandono e acelerar primeira sessão útil", "Em execução"],
          ["31-60 dias", "Monetização inicial", "Ajustes de planos, oferta e CTAs para aumentar conversão de ativo para pagante", "Próximo ciclo"],
          ["61-90 dias", "Escala controlada", "Repetir canal de aquisição vencedor com custo previsível e retenção saudável", "Planejado"],
          ["4-12 meses", "Expansão com base em dados", "Crescer equipe por marcos e abrir frentes institucionais com risco controlado", "Condicional a tração"],
        ],
      },
      bullets: [
        "Prioridade absoluta: lançamento com estabilidade e conversão.",
        "Sem dispersão: backlog orientado a impacto em receita e retenção.",
        "Contratação e novos módulos só avançam com marcos batidos.",
      ],
    },
    {
      id: "capital",
      title: "12. Uso de capital seed e estrutura de custos",
      paragraphs: [
        "A rodada seed será usada para estender runway e acelerar o ciclo de aprendizado com foco em três alavancas: produto (qualidade e confiabilidade), aquisição (testes de canal) e operações essenciais (suporte, compliance mínimo, infraestrutura).",
        "A empresa manterá estrutura enxuta no curto prazo, com controle rigoroso de burn mensal. A lógica é preservar opcionalidade estratégica: crescer quando métricas validarem, não por pressão de headline.",
      ],
      table: {
        rows: [
          ["Frente", "Faixa de alocação", "Resultado esperado"],
          ["Produto e engenharia", "45%–55%", "Melhor ativação, retenção e confiabilidade"],
          ["Growth e aquisição inicial", "20%–30%", "Descoberta de canal repetível"],
          ["Operações e suporte", "10%–20%", "Base para escala sem quebra operacional"],
          ["Reserva e contingência", "5%–10%", "Proteção de runway e gestão de risco"],
        ],
      },
    },
    {
      id: "risks",
      title: "13. Riscos principais e mitigação",
      paragraphs: [
        "Risco de produto: não converter interesse em uso recorrente. Mitigação: ciclos curtos de release, instrumentação de métricas por coorte e entrevistas contínuas com usuários ativos/inativos.",
        "Risco de distribuição: canais iniciais não escalarem com CAC viável. Mitigação: portfólio enxuto de canais, testes comparáveis e cortes rápidos em canais sem retenção.",
        "Risco de founder bandwidth: execução concentrada em fundador solo. Mitigação: documentação de processos, automação e contratação incremental por prioridade crítica.",
      ],
      bullets: [
        "Risco operacional de infraestrutura e fornecedores de serviço: monitoramento, redundância e plano de continuidade.",
        "Risco financeiro: burn sem tração; mitigado por governança de runway mensal.",
        "Risco estratégico: dispersão de escopo; mitigado por foco em ICP inicial.",
      ],
    },
    {
      id: "closing",
      title: "14. Tese de investimento seed e próximos passos",
      paragraphs: [
        "A tese seed da Syntexa é investir em um produto já lançado, com execução founder-led comprovada e foco explícito em encontrar tração inicial com disciplina de capital. O diferencial está na capacidade de transformar respostas de IA em entregáveis úteis e visualmente profissionais para o usuário final.",
        "O próximo passo proposto para investidores é uma diligência objetiva orientada a dados de estágio: funil de ativação, retenção de coortes iniciais, experimentos de aquisição, estrutura de custos e plano de contratação por marcos.",
      ],
      bullets: [
        "Pedido: parceria de capital + acompanhamento tático de GTM early-stage.",
        "Entrega da empresa: transparência mensal de métricas e aprendizado.",
        "Objetivo: atingir base inicial de usuários recorrentes e primeiros pagantes consistentes.",
      ],
    },
  ],
};

function chapterToPdfSection(ch) {
  const parts = [];
  for (const p of ch.paragraphs || []) {
    parts.push(String(p).trim());
  }
  if (ch.bullets && ch.bullets.length) {
    parts.push(ch.bullets.map((b) => "• " + String(b).trim()).join("\n"));
  }
  const sec = {
    heading: ch.title,
    body: parts.filter(Boolean).join("\n\n"),
  };
  if (ch.table && Array.isArray(ch.table.rows) && ch.table.rows.length) {
    sec.table_rows = ch.table.rows.map((row) => row.map((c) => String(c ?? "")));
  }
  return sec;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function BusinessPlanPage({ plans, onSubscribe }) {
  const [exportBusy, setExportBusy] = useState(null);

  const pdfSections = useMemo(
    () => PLAN_DOCUMENT.chapters.map((c) => chapterToPdfSection(c)),
    []
  );

  const runExport = useCallback(
    async (kind) => {
      if (typeof window === "undefined") return;
      const token = window.localStorage.getItem("syntexa_token");
      setExportBusy(kind);
      try {
        if (kind === "pdf") {
          const blob = await multimodalExportPdf(
            {
              title: PLAN_DOCUMENT.title,
              subtitle: PLAN_DOCUMENT.subtitle,
              sections: pdfSections,
            },
            token || undefined
          );
          downloadBlob(blob, "syntexa-plano-de-negocios-completo.pdf");
        } else {
          const blob = await multimodalExportDocx(
            {
              title: PLAN_DOCUMENT.title,
              sections: pdfSections,
            },
            token || undefined
          );
          downloadBlob(blob, "syntexa-plano-de-negocios-completo.docx");
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        window.alert(
          "Não foi possível gerar o ficheiro agora. Pode tentar de novo ou usar Imprimir → Guardar como PDF.\n\n" +
            msg
        );
      } finally {
        setExportBusy(null);
      }
    },
    [pdfSections]
  );

  const handlePrint = useCallback(() => {
    if (typeof window !== "undefined") window.print();
  }, []);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 sm:py-10">
      <style
        dangerouslySetInnerHTML={{
          __html: `
@media print {
  .no-print { display: none !important; }
  body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
}`,
        }}
      />

      <div className="space-y-5">
        <div className="mx-auto mb-3 flex h-32 w-32 items-center justify-center rounded-2xl border border-emerald-200 bg-transparent shadow-sm">
          <img src="/LOGOTIPO.png?v=blue3" alt="Logotipo Syntexa Desktop" className="h-28 w-28 rounded-md object-contain" />
        </div>
        <p className="mx-auto mb-3 inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Plano de negócios completo
        </p>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 sm:text-4xl">{PLAN_DOCUMENT.title}</h1>
        <p className="mx-auto mt-3 max-w-3xl text-sm text-zinc-600 sm:text-base">{PLAN_DOCUMENT.subtitle}</p>
        <p className="mx-auto mt-2 max-w-3xl text-xs text-zinc-500 sm:text-sm">
          Plano operativo de negócio + roadmap de execução: foco em lançamento, primeiros pagantes e evolução contínua
          com métricas de produto.
        </p>
      </div>

      <div className="no-print flex flex-col gap-3 rounded-2xl border border-emerald-200 bg-linear-to-br from-emerald-50/90 to-white p-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:p-5">
        <div className="text-sm text-zinc-700">
          <p className="font-semibold text-zinc-900">Exportar para apresentação</p>
          <p className="text-xs text-zinc-600">Geração no servidor (mesma pipeline de relatórios do chat).</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="primary"
            className="rounded-xl"
            disabled={exportBusy !== null}
            onClick={() => void runExport("pdf")}
          >
            {exportBusy === "pdf" ? "A gerar PDF…" : "Baixar PDF completo"}
          </Button>
          <Button
            variant="outline"
            className="rounded-xl"
            disabled={exportBusy !== null}
            onClick={() => void runExport("docx")}
          >
            {exportBusy === "docx" ? "A gerar Word…" : "Baixar Word (.docx)"}
          </Button>
          <Button variant="outline" className="rounded-xl" onClick={handlePrint}>
            Imprimir / Guardar como PDF
          </Button>
        </div>
      </div>

      <nav className="no-print rounded-2xl border border-zinc-200 bg-zinc-50/80 p-4 text-sm">
        <p className="font-semibold text-zinc-900">Índice</p>
        <ol className="mt-2 grid gap-1 sm:grid-cols-2">
          {PLAN_DOCUMENT.chapters.map((ch, i) => (
            <li key={ch.id}>
              <a href={"#" + ch.id} className="text-emerald-800 underline-offset-2 hover:underline">
                {i + 1}. {ch.title}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 no-print">
        <MetricCard label="Capítulos" value="14 capítulos" note="Negócio, escala, lançamento e roadmap de execução" />
        <MetricCard label="Export" value="PDF + Word" note="Download direto ou impressão do browser" />
        <MetricCard label="Modelo" value="SaaS early-stage" note="Assinatura inicial + validação de preço" />
        <MetricCard label="Foco" value="Lançamento imediato" note="Ativação, conversão e primeiros pagantes" />
      </div>

      <div className="flex flex-col gap-5">
        {PLAN_DOCUMENT.chapters.map((ch) => (
          <Section key={ch.id} id={ch.id} title={ch.title}>
            {(ch.paragraphs || []).map((p, i) => (
              <p key={i}>{p}</p>
            ))}
            {ch.bullets && ch.bullets.length ? (
              <ul className="list-disc space-y-1 pl-5">
                {ch.bullets.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            ) : null}
            {ch.table && ch.table.rows && ch.table.rows.length ? (
              <div className="overflow-x-auto rounded-lg border border-zinc-200">
                <table className="min-w-full text-left text-xs text-zinc-800">
                  <tbody>
                    {ch.table.rows.map((row, ri) => (
                      <tr key={ri} className={ri === 0 ? "bg-emerald-50 font-semibold" : "border-t border-zinc-100"}>
                        {row.map((cell, ci) => (
                          <td key={ci} className="px-3 py-2 align-top">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </Section>
        ))}
      </div>

      <section className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm sm:p-6 print:break-inside-avoid">
        <h2 className="text-xl font-semibold text-zinc-900">Planos comerciais ativos</h2>
        <p className="mt-2 text-sm text-zinc-600">
          Preços públicos associados ao produto. O plano de negócios acima descreve como estes planos encaixam no modelo de
          receita e na estratégia institucional.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {plans.map((plan) => (
            <article
              key={plan.key}
              className={
                "relative flex h-full flex-col rounded-2xl border p-5 no-print " +
                (plan.highlighted
                  ? "border-emerald-300 bg-linear-to-b from-emerald-50 to-white"
                  : "border-zinc-200 bg-white")
              }
            >
              {plan.highlighted ? (
                <span className="absolute -top-2 right-4 rounded-full bg-emerald-600 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-white">
                  Recomendado
                </span>
              ) : null}
              <p className="text-xs font-medium text-zinc-500">{plan.tag}</p>
              <h3 className="mt-1 text-xl font-semibold text-zinc-900">{plan.name}</h3>
              <p className="mt-2 text-sm text-zinc-600">{plan.description}</p>
              <div className="mt-4 text-3xl font-semibold text-zinc-900">
                {plan.price}
                <span className="text-base font-normal text-zinc-600"> {plan.priceLabel}</span>
              </div>
              <div className="mb-4 text-xs text-emerald-700">
                Estudantes com 50% OFF: <span className="font-semibold">{plan.priceStudent}</span> {plan.studentLabel}
              </div>
              <ul className="mb-5 space-y-2 text-sm text-zinc-700">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <span className="mt-[6px] h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-auto">
                <Button
                  variant={plan.highlighted ? "primary" : "outline"}
                  className="w-full justify-center rounded-xl"
                  onClick={() => onSubscribe(plan.key || "basic")}
                >
                  Assinar plano
                </Button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
