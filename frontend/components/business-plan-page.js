"use client";

import React, { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "./ui/button";
import { t } from "../lib/i18n";
import { useLanguage } from "./language-provider";

/* ────────────────────────────────────────────────────────────────────────── */
/*  Ícones inline (SVG) — sem dependências externas                            */
/* ────────────────────────────────────────────────────────────────────────── */

function Icon({ d, size = 18, stroke = 1.6, className = "" }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {d}
    </svg>
  );
}

const I = {
  spark: <path d="M12 3v3M12 18v3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M3 12h3M18 12h3M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1" />,
  rocket: (
    <>
      <path d="M5 19c0-3 1-5 3-7l7-7 4 4-7 7c-2 2-4 3-7 3z" />
      <path d="M14 5l5 5" />
      <path d="M9 15l-3 3" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
    </>
  ),
  layers: (
    <>
      <path d="M12 3l9 5-9 5-9-5 9-5z" />
      <path d="M3 13l9 5 9-5" />
      <path d="M3 17l9 5 9-5" />
    </>
  ),
  table: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M3 10h18M9 4v16" />
    </>
  ),
  chart: (
    <>
      <path d="M3 3v18h18" />
      <path d="M7 14l4-4 3 3 5-7" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6l8-3z" />
      <path d="M9 12l2 2 4-4" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20c0-3.5 3-6 6.5-6s6.5 2.5 6.5 6" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M21.5 19c0-2.5-2-4.5-4.5-4.5" />
    </>
  ),
  cash: (
    <>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <circle cx="12" cy="12" r="2.5" />
      <path d="M6 6v12M18 6v12" />
    </>
  ),
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18" />
    </>
  ),
  alert: (
    <>
      <path d="M12 3l10 18H2L12 3z" />
      <path d="M12 10v5M12 18v.01" />
    </>
  ),
  signature: (
    <>
      <path d="M3 17c2-1 4-3 6-6s4-5 6-5c1.5 0 2 1 1 3s-3 5-3 7c0 1 1 2 2 2 2 0 4-2 5-4" />
      <path d="M3 21h18" />
    </>
  ),
  download: (
    <>
      <path d="M12 3v12" />
      <path d="M7 10l5 5 5-5" />
      <path d="M4 21h16" />
    </>
  ),
  printer: (
    <>
      <path d="M6 9V3h12v6" />
      <rect x="3" y="9" width="18" height="9" rx="2" />
      <rect x="7" y="14" width="10" height="6" rx="1" />
    </>
  ),
  word: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M7 8l2 9 3-7 3 7 2-9" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 4-7 8-7s8 3 8 7" />
    </>
  ),
  bot: (
    <>
      <rect x="4" y="7" width="16" height="12" rx="3" />
      <path d="M12 3v4" />
      <circle cx="9" cy="13" r="1.2" fill="currentColor" />
      <circle cx="15" cy="13" r="1.2" fill="currentColor" />
      <path d="M9 17h6" />
    </>
  ),
  check: <path d="M5 12l5 5 9-11" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  send: (
    <>
      <path d="M3 12l18-9-7 18-3-7-8-2z" />
    </>
  ),
};

/* ────────────────────────────────────────────────────────────────────────── */
/*  Dados do plano (preservados para export PDF/Word — pipeline existente)    */
/* ────────────────────────────────────────────────────────────────────────── */

const PLAN_DOCUMENT = {
  title: "Syntexa — Plano de Negócios",
  get subtitle() {
    return (
      "Documento operativo · " +
      new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })
    );
  },
  meta: {
    chapters: "14 capítulos operativos",
    plans: "Planos R$ 0–199",
    icp: "ICP: Prosumer BR",
    stage: "Estágio: Seed",
  },
  letter: [
    "Construí a Syntexa porque me cansei de ver gente boa perdendo tarde inteira formatando o que a IA já tinha respondido. A pergunta vinha rápida, a resposta vinha rápida, e aí começava a parte triste: copia, cola, ajusta espaçamento, vira tabela, exporta PDF, manda pro cliente.",
    "Esse documento não é um deck. É o plano operacional que eu uso pra decidir o que fazer essa semana. Os números são reais — alguns bons, alguns ruins. Os capítulos foram escritos na ordem em que penso: primeiro o que existe hoje, depois quem está atendendo, depois como vamos crescer e, por fim, onde podemos quebrar.",
    "Se você é investidor lendo isso: bem-vindo. Aviso que não vou aumentar número pra ficar bonito. Se você é usuário: obrigado por chegar até aqui — você é a razão de a Syntexa existir.",
    "— Luis Paulo",
  ],
  demo: {
    title: "Da pergunta à planilha pronta — sem etapa intermediária",
    description: "Mesma resposta que o cliente paga consultor pra montar. Aqui sai do chat já formatada, com gráfico e botões de export. Esse é o produto.",
    chatLabel: "syntexa.app · chat ao vivo",
    userPrompt: "Monta uma planilha de fluxo de caixa do meu negócio nos últimos 6 meses, com receita, custo e lucro. Quero exportar pro Excel.",
    aiResponse: "Pronto. Montei o fluxo de caixa Jan-Jun com receita, custo e lucro. Receita total R$ 189.100, lucro acumulado R$ 99.300 (margem ~53%).",
    sheet: [
      ["Jan", "R$ 18.500", "R$ 11.200", "R$ 7.300"],
      ["Fev", "R$ 22.300", "R$ 12.100", "R$ 10.200"],
      ["Mar", "R$ 28.800", "R$ 14.400", "R$ 14.400"],
      ["Abr", "R$ 33.500", "R$ 15.800", "R$ 17.700"],
      ["Mai", "R$ 39.200", "R$ 17.200", "R$ 22.000"],
      ["Jun", "R$ 46.800", "R$ 19.100", "R$ 27.700"],
    ],
    total: { receita: "R$ 189.100", custo: "R$ 89.800", lucro: "R$ 99.300" },
    sheetCaption: "resposta gerada em 8.4s · 6 fontes consultadas",
  },
  plans: [
    {
      name: "Gratuito",
      price: "R$ 0/mês",
      description: "120 mensagens por dia para experimentar. Chat, pesquisa na web e respostas inteligentes — sem cartão.",
      features: [
        "120 mensagens por dia",
        "Chat com pesquisa na web",
        "Respostas com contexto e citações",
        "Sem cartão de crédito",
      ],
    },
    {
      name: "Básico",
      price: "R$ 39/mês (estudante: R$ 19,50)",
      description: "500 mensagens/mês, upload de arquivos e respostas mais completas. Ideal para estudantes e freelancers.",
      features: [
        "500 mensagens/mês",
        "Upload de PDF, Word, Excel e imagens",
        "Respostas detalhadas com fontes",
        "Exportação para PDF e Word",
      ],
    },
    {
      name: "Médio",
      price: "R$ 99/mês (estudante: R$ 49,50)",
      description: "Mensagens ilimitadas, geração de imagem/vídeo/áudio, código e contexto estendido. Para profissionais.",
      features: [
        "Mensagens ilimitadas (uso justo)",
        "Geração de imagem, vídeo e áudio",
        "Análise de código e dados",
        "Contexto estendido para projetos longos",
      ],
    },
    {
      name: "Master",
      price: "R$ 199/mês (estudante: R$ 99,50)",
      description: "Tudo ilimitado + agentes avançados, suporte prioritário, múltiplos usuários e ferramentas empresariais.",
      features: [
        "Tudo do plano Médio, sem limites",
        "Agentes autônomos e automações",
        "Múltiplos usuários e SSO",
        "Suporte prioritário e SLA dedicado",
      ],
    },
  ],
  footer: "Gerado pelo Syntexa — " + new Date().toLocaleDateString("pt-BR"),
  chapters: [
    {
      id: "intro",
      number: "01",
      icon: "spark",
      title: "Onde a Syntexa está hoje",
      lead: "Produto no ar, validação em curso, foco absoluto em primeiros pagantes recorrentes.",
      paragraphs: [
        "A Syntexa é uma plataforma brasileira de IA generativa com chat, multimodal, exportações em PDF/Word/Excel e infraestrutura própria. Saímos do modo construção: o produto está publicado em syntexabr.com.br, autenticação real, pagamentos integrados e desktop instalável para Windows e Linux.",
        "O foco mudou. Os próximos meses não são sobre adicionar features — são sobre converter o que já existe em receita previsível. Cada decisão técnica passa por um filtro: isto move ativação, retenção ou pagamento?",
      ],
      bullets: [
        "Plataforma web + desktop publicadas, com instaladores oficiais distribuídos via release.",
        "Pipeline de exportação real: respostas viram PDF, Word, Excel ou CSV em um clique.",
        "Próxima meta: entrar nos primeiros R$ 10 mil/mês de MRR com no máximo 2 canais.",
      ],
    },
    {
      id: "founder",
      number: "02",
      icon: "user",
      title: "Quem está construindo",
      lead: "Founder solo, perfil técnico, vivendo dentro do produto todos os dias.",
      paragraphs: [
        "Sou o Luis Paulo de Oliveira, 24 anos, fundador da Syntexa. Construí toda a stack que está no ar — frontend em Next.js, backend em FastAPI, gateway na Cloudflare, infra em Railway/AWS — e mantenho o roadmap operacional sozinho, com apoio intensivo de ferramentas de desenvolvimento assistido para multiplicar throughput.",
        "Não acredito em time grande no estágio errado. A próxima contratação só acontece depois que eu provar repetibilidade em aquisição. Até lá, prefiro a velocidade de iteração de uma operação enxuta a um time bonito de slide.",
      ],
      bullets: [
        "Founder-led, técnico, sem dependência de fornecedor único.",
        "Burn mensal em centenas de reais, não milhares — runway estendido por design.",
        "Próxima vaga: engenharia full-stack sênior, gatilho = 100 pagantes ativos.",
      ],
    },
    {
      id: "problem",
      number: "03",
      icon: "alert",
      title: "O problema que decidimos resolver",
      lead: "Conversa boa não é entregável. E é entregável que paga conta.",
      paragraphs: [
        "Quem usa IA generativa para trabalhar passa metade do tempo formatando: copia do chat, cola no Word, ajusta espaçamento, vira tabela no Excel, exporta PDF, manda pro cliente. O ChatGPT te dá texto. O resto é serviço braçal.",
        "No Brasil isso é pior: a maioria dos materiais profissionais ainda nasce em PDF e Excel, não em ferramentas com IA embarcada. Existe um buraco entre \"a IA respondeu bem\" e \"o material está pronto pro cliente\". Esse buraco é onde a Syntexa mora.",
      ],
      bullets: [
        "Dor central: tempo entre resposta da IA e material apresentável.",
        "Dor secundária: inconsistência visual quando o material passa por várias mãos.",
        "Quem paga: profissional que cobra por hora e perde tempo em formatação.",
      ],
    },
    {
      id: "solution",
      number: "04",
      icon: "rocket",
      title: "O que a Syntexa entrega",
      lead: "Conversa que vira documento. Sem etapa intermediária.",
      paragraphs: [
        "O usuário pede uma análise, um relatório, um cronograma, uma planilha — e recebe não só a resposta, mas o arquivo final pronto pra abrir no Excel ou anexar num e-mail. Tabela financeira, plano de aulas, resumo jurídico, fluxo de caixa, cronograma de estudos: tudo sai estruturado, com cabeçalhos, formatação e identidade visual.",
        "Por baixo, o motor já suporta multimodal (texto, imagem, áudio), pesquisa na web em tempo real com citações, análise de documentos enviados (PDF, DOCX, XLSX) e geração de código. O que parece magia é só pipeline bem desenhado: a resposta nunca é texto cru — é estrutura.",
      ],
      bullets: [
        "Exportação direta: PDF, Word (.docx), Excel (.xlsx), CSV, TXT.",
        "Multimodal real: lê PDFs longos, descreve imagens, transcreve áudio, gera planilhas.",
        "Pesquisa na web com fontes citadas — o usuário sabe de onde veio cada afirmação.",
      ],
    },
    {
      id: "tech",
      number: "05",
      icon: "layers",
      title: "Tecnologia proprietária e infraestrutura",
      lead: "Stack inteira sob nosso controle. Zero dependência crítica de fornecedor único.",
      paragraphs: [
        "Toda a aplicação — interface, backend, gateway, sistema de exportação, autenticação, integrações — é código autoral, mantido em monorepo próprio. O motor de IA roda em arquitetura híbrida: serviço próprio para tarefas críticas, com fallback inteligente para provedores externos quando necessário, sempre escondendo essa decisão do usuário final.",
        "A inferência opera em infraestrutura sob nosso controle (Railway para gateway, AWS para GPU, Cloudflare na borda). A camada de fallback existe para garantir disponibilidade enquanto a infraestrutura proprietária de IA continua em desenvolvimento — quando estiver pronta, é troca de configuração, não rewrite.",
      ],
      bullets: [
        "Frontend Next.js + Cloudflare Pages, deploy global na borda.",
        "Backend FastAPI + Postgres + Redis em Railway, com healthchecks ativos.",
        "Gateway Cloudflare Worker com rate limiting, HMAC e proteção edge.",
      ],
    },
    {
      id: "scale",
      number: "06",
      icon: "chart",
      title: "Capacidade técnica e meta de escala",
      lead: "A arquitetura foi desenhada de forma modular para escalar progressivamente conforme validação de mercado e crescimento da base de usuários.",
      paragraphs: [
        "A infraestrutura utiliza escalonamento horizontal por camadas — aplicação, fila assíncrona, cache distribuído e banco com leitura otimizada — permitindo que cada camada cresça independente conforme o gargalo aparece. Não otimizamos para problemas que ainda não existem; expandimos sob demanda, protegendo margem e runway.",
        "Validação acontece com testes de stress recorrentes em ambiente de produção espelhado. O custo unitário por mensagem cai conforme o volume sobe (cache, batching, modelos quantizados), o que protege margem em escala.",
      ],
      table: {
        rows: [
          ["Camada", "Estratégia", "Meta operacional"],
          ["Aplicação web", "Escala horizontal + load balancer edge", "Latência P95 < 800ms"],
          ["Inferência IA", "Filas assíncronas + cache de resposta", "Throughput estável em pico"],
          ["Banco de dados", "Read replicas + cache em Redis", "Suportar alto QPS de leitura"],
          ["Observabilidade", "Métricas, logs e alertas em tempo real", "MTTR < 15min em incidentes"],
        ],
      },
      bullets: [
        "Custo marginal por mensagem decrescente conforme o volume cresce.",
        "Stress tests semanais simulando 10x a carga atual de produção.",
        "Plano de continuidade com fallback multi-provider para inferência.",
      ],
    },
    {
      id: "icp",
      number: "07",
      icon: "users",
      title: "Para quem estamos vendendo agora",
      lead: "Prosumer educacional brasileiro. Antes de pensar em enterprise, vamos provar aqui.",
      paragraphs: [
        "ICP inicial é deliberadamente estreito: estudante avançado (concursos, vestibular pesado, pós-graduação), professor independente, criador de conteúdo educacional e profissional liberal que produz material toda semana. Brasileiros, falando português, dispostos a pagar entre R$ 39 e R$ 99 por mês para ganhar 4-6 horas de formatação.",
        "Enterprise e instituições estão no roadmap, mas como segunda onda. Tentar atacar os dois ao mesmo tempo é o erro clássico de startup pré-tração: vira uma empresa que faz tudo mal, em vez de uma coisa bem feita.",
      ],
      table: {
        rows: [
          ["Segmento", "Necessidade central", "Sinal de validação"],
          ["Estudante de concurso", "Resumir editais, montar cronogramas, gerar simulados", "Uso semanal de exportações"],
          ["Professor independente", "Criar planos de aula e relatórios em volume", "Conversão de free para Básico"],
          ["Profissional liberal", "Análises e relatórios para clientes em PDF/Excel", "Upgrade para Médio"],
          ["Criador de conteúdo", "Roteiros, scripts, planilhas de campanha", "Frequência de uso > 3x/semana"],
        ],
      },
      bullets: [
        "ICP em uma frase: brasileiro que paga por hora e gasta tempo em Word/Excel.",
        "Antes de expandir: 100 pagantes recorrentes no nicho atual.",
      ],
    },
    {
      id: "gtm",
      number: "08",
      icon: "target",
      title: "Como vamos chegar nos primeiros usuários",
      lead: "Aquisição manual antes de mídia paga. Sempre.",
      paragraphs: [
        "Primeiros 100 pagantes virão de canais orgânicos: conteúdo de demonstração no YouTube e TikTok mostrando casos reais (\"da pergunta à planilha pronta em 12 segundos\"), comunidades de concurso e estudo no Telegram/Discord, indicação direta e SEO técnico em buscas longas.",
        "Mídia paga só entra depois de provar retenção: se 30% dos free convertem para pago em 30 dias e o LTV/CAC orgânico estiver acima de 3x, abrimos torneira de Meta Ads e Google. Antes disso, mídia paga tende a gerar crescimento pouco sustentável.",
      ],
      bullets: [
        "Fase 1 (0-60 dias): conteúdo orgânico + outreach manual em comunidades.",
        "Fase 2 (60-120 dias): loops de indicação com bônus para indicador e indicado.",
        "Fase 3 (120+ dias): performance paga apenas com canais que provarem CAC viável.",
      ],
    },
    {
      id: "metrics",
      number: "09",
      icon: "chart",
      title: "Métricas que importam neste estágio",
      lead: "Sem vaidade. Métrica seed é coorte de comportamento.",
      paragraphs: [
        "Não rastreamos pageviews. Rastreamos: quem ativou no D1 (concluiu primeira sessão útil), quem voltou na W1, quem voltou na W4, quem pagou, e quem cancelou. Tudo por coorte semanal — sem média ponderada que esconde problema.",
        "A meta para os próximos 90 dias é estabelecer baseline real e mover dois ponteiros: ativação D1 e retenção W4. Tudo o mais é consequência. MRR não é meta primária — é resultado.",
      ],
      table: {
        rows: [
          ["Métrica", "O que significa", "Meta seed (90 dias)"],
          ["Ativação D1", "Usuário que conclui 1ª sessão útil", "≥ 45% dos cadastros"],
          ["Retenção W4", "Volta a usar 4 semanas depois", "≥ 25% das coortes"],
          ["Free → Pago", "Conversão de gratuito para Básico/Médio", "≥ 4% em 30 dias"],
          ["Uso de export", "Sessões que geram PDF/Word/Excel", "≥ 35% das pagantes"],
        ],
      },
    },
    {
      id: "pricing",
      number: "10",
      icon: "cash",
      title: "Modelo de receita e estrutura de planos",
      lead: "SaaS por assinatura. Quatro planos. Estudante paga metade. Sem letras miúdas.",
      paragraphs: [
        "O modelo é direto: Gratuito (R$ 0, captação), Básico (R$ 39, individual), Médio (R$ 99, profissional) e Master (R$ 199, equipes). Estudante com e-mail .edu paga 50% em qualquer plano pago — política permanente, não promoção.",
        "Não há plano enterprise público. Empresa que precisa de SLA, SSO ou volume customizado fala com a gente direto e sai com proposta sob medida. Isso protege margem na base e abre upside no topo.",
      ],
      bullets: [
        "Cobrança recorrente em BRL via Stripe — sem dolarização escondida.",
        "Estudante 50% OFF permanente com validação de e-mail .edu/.edu.br.",
        "Cancelamento self-service na própria conta. Sem ligação de retenção.",
      ],
    },
    {
      id: "roadmap",
      number: "11",
      icon: "rocket",
      title: "Roadmap de execução: o que vai acontecer quando",
      lead: "Ciclos quinzenais. Cada ciclo entrega algo que move métrica.",
      paragraphs: [
        "Roadmap aqui não é wishlist — é cronograma operacional. Tudo o que está abaixo já tem responsável, data e métrica de saída. O que não tinha métrica clara, foi cortado.",
      ],
      table: {
        rows: [
          ["Janela", "Prioridade", "Entrega", "Status"],
          ["Sprint atual", "Onboarding e ativação", "Reduzir fricção do cadastro, primeira mensagem em < 30s", "Em execução"],
          ["+30 dias", "Conversão Free → Pago", "Paywall contextual quando o limite acaba, com prova de valor", "Próximo"],
          ["+60 dias", "Loops de retenção", "Notificações úteis, lembrança de uso, exportação programada", "Planejado"],
          ["+90 dias", "Canal de aquisição", "Dobrar o canal vencedor, abandonar os outros", "Condicional"],
          ["6 meses", "Infraestrutura proprietária de IA", "Reduzir gradualmente dependência de terceiros", "Em desenvolvimento"],
          ["12 meses", "Expansão B2B/Edu", "Primeira instituição de ensino contratando sob proposta", "Roadmap"],
        ],
      },
    },
    {
      id: "capital",
      number: "12",
      icon: "cash",
      title: "Uso do capital e estrutura de custos",
      lead: "Cada real entra em produto, aquisição ou runway. Nada em escritório bonito.",
      paragraphs: [
        "Rodada seed alvo: R$ 800 mil a R$ 1,5 milhão para 18 meses de operação com folga e dois novos contratados (engenharia + growth). Sem co-working caro, sem viagem de feira, sem MVP de hardware. Tudo o que não construir produto ou trazer usuário fica fora.",
        "Burn target: R$ 35-50 mil/mês na fase atual (founder + infra), subindo para R$ 90-120 mil/mês depois das duas contratações. Esse é o teto. Excesso de caixa fica reservado para emergência ou para dobrar canal vencedor — nunca para aumentar headcount sem motivo.",
      ],
      table: {
        rows: [
          ["Frente", "% do capital", "O que entrega"],
          ["Engenharia (1-2 contratações)", "45-55%", "Velocidade de produto + cobertura de risco solo"],
          ["Aquisição e growth", "20-30%", "Descoberta e validação de canal repetível"],
          ["Infraestrutura e operação", "10-15%", "Disponibilidade, custo unitário, suporte"],
          ["Reserva tática", "10-15%", "Caixa para dobrar canal vencedor ou cobrir imprevisto"],
        ],
      },
    },
    {
      id: "risks",
      number: "13",
      icon: "shield",
      title: "Riscos reais e o que estamos fazendo a respeito",
      lead: "Sem otimismo de pitch. Aqui é onde podemos quebrar.",
      paragraphs: [
        "Risco 1 — Bandwidth do founder. Se eu travar, a empresa trava. Mitigação: documentação operacional de tudo, automação agressiva, contratação por gatilho de tração. Plano B: handover técnico parcial após primeira contratação.",
        "Risco 2 — Distribuição. Se nenhum canal orgânico provar CAC viável, a tese inteira fica em xeque. Mitigação: 2-3 canais testados em paralelo com cortes rápidos, métrica clara de sucesso por canal, sem vínculo emocional com canal específico.",
        "Risco 3 — Diferenciação. Modelos genéricos comoditizam. Mitigação: foco no que ninguém entrega bem em português — exportação profissional, contexto brasileiro, pagamento em BRL, suporte em PT-BR de verdade.",
      ],
      bullets: [
        "Risco operacional: dependência de provedores externos durante o desenvolvimento da infraestrutura proprietária. Mitigação: arquitetura multi-provider com fallback automático.",
        "Risco financeiro: burn sem tração. Mitigação: revisão mensal de runway com gatilho de corte automático em 3 meses de baseline.",
        "Risco regulatório: LGPD e direito do consumidor. Mitigação: política de dados desde o dia 1, compliance leve mas presente.",
      ],
    },
    {
      id: "thesis",
      number: "14",
      icon: "target",
      title: "Tese de investimento e próximo passo",
      lead: "Empresa enxuta, produto no ar, founder técnico, mercado claro. Vamos conversar?",
      paragraphs: [
        "Investir na Syntexa hoje é entrar antes da inflexão de tração. Produto pronto, custo de operação mínimo, infraestrutura proprietária em desenvolvimento, mercado brasileiro pouco atendido por IA com saída profissional em português. O que falta é capital e tempo para encontrar o canal.",
        "Próximo passo concreto: conversa de 45 minutos para diligência objetiva sobre métricas reais (não slides), demonstração ao vivo do produto, e discussão de termos. Sem pitch deck inflado. Sem hype.",
      ],
      bullets: [
        "Pedido: cheque seed + acompanhamento tático mensal de GTM.",
        "Compromisso: relatório mensal de métricas reais, com bons e maus números.",
        "Resultado em 12 meses: primeira coorte de 1.000 pagantes recorrentes ou pivot honesto.",
      ],
    },
    {
      id: "cubo",
      number: "15",
      icon: "signature",
      title: "O que levar para a primeira conversa",
      lead: "Demo ao vivo vale mais que vinte slides. Métricas reais, por menores que sejam, valem mais que projeções.",
      paragraphs: [
        "A Syntexa transforma IA em entrega profissional pronta. Não vendemos apenas respostas — vendemos workflow, automação e documentos finalizados para o mercado brasileiro.",
        "Leve para a reunião: uma demonstração ao vivo de menos de 2 minutos (pergunta → geração → export PDF → export Excel → abrir documento pronto). Mais importante que o PDF do plano. E métricas reais do produto, por menores que sejam — 30 usuários, 200 exports, tempo médio de sessão, custo de inferência — porque número pequeno real é melhor que número aspiracional gigante.",
      ],
      bullets: [
        "Demo obrigatória: pergunta → planilha/relatório → export → arquivo pronto em < 2 min.",
        "Métricas reais: cadastros, exports, sessões, retenção, tempo médio, custo inferência.",
        "Frase definitiva: transformamos IA em entrega profissional pronta para o mercado brasileiro.",
      ],
    },
  ],
};

/* ────────────────────────────────────────────────────────────────────────── */
/*  Helpers de export (mantém pipeline existente PDF/Word)                     */
/* ────────────────────────────────────────────────────────────────────────── */

function chapterToPdfSection(ch) {
  const parts = [];
  if (ch.lead) parts.push(String(ch.lead).trim());
  for (const p of ch.paragraphs || []) parts.push(String(p).trim());
  if (ch.bullets && ch.bullets.length) {
    parts.push(ch.bullets.map((b) => "• " + String(b).trim()).join("\n"));
  }
  const sec = {
    heading: `${ch.number}. ${ch.title}`,
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

/* ─────────────────────────────────────────────────────────────
 * Geração 100% client-side do Plano de Negócios (sem API).
 *  - PDF: usa o motor de impressão do navegador via popup com
 *    HTML formatado + auto-print → "Salvar como PDF".
 *  - DOCX: HTML compatível com Microsoft Word (mime msword,
 *    extensão .doc — abre nativamente no Word/LibreOffice).
 * Evita dependência de api.syntexabr.com.br para o board.
 * ──────────────────────────────────────────────────────────── */
function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function buildPlanHtml(doc) {
  const head =
    "<style>" +
    "body{font-family:'Segoe UI',-apple-system,Roboto,Arial,sans-serif;color:#0f172a;line-height:1.55;max-width:780px;margin:36px auto;padding:0 28px;}" +
    "h1{font-size:28px;margin:0 0 6px;letter-spacing:-0.02em;}" +
    "h2{font-size:18px;margin:28px 0 8px;color:#1e293b;border-bottom:1px solid #e2e8f0;padding-bottom:4px;}" +
    ".subtitle{color:#64748b;font-size:13px;margin-bottom:24px;}" +
    "p{margin:0 0 10px;font-size:13px;}" +
    "ul{margin:6px 0 14px 18px;padding:0;font-size:13px;}" +
    "table{border-collapse:collapse;width:100%;margin:10px 0 14px;font-size:12px;}" +
    "td,th{border:1px solid #cbd5e1;padding:6px 8px;text-align:left;}" +
    "th{background:#f1f5f9;}" +
    ".footer{margin-top:32px;border-top:1px solid #e2e8f0;padding-top:10px;color:#94a3b8;font-size:11px;}" +
    "@media print{body{margin:0;padding:0 24px;}h2{page-break-after:avoid;}section{page-break-inside:avoid;}}" +
    "</style>";
  let body = "<h1>" + escapeHtml(doc.title) + "</h1>";
  if (doc.subtitle) body += '<p class="subtitle">' + escapeHtml(doc.subtitle) + "</p>";
  for (const ch of doc.chapters) {
    body += "<section>";
    body += "<h2>" + escapeHtml(ch.number + ". " + ch.title) + "</h2>";
    if (ch.lead) body += "<p><em>" + escapeHtml(ch.lead) + "</em></p>";
    for (const p of ch.paragraphs || []) body += "<p>" + escapeHtml(p) + "</p>";
    if (ch.bullets && ch.bullets.length) {
      body += "<ul>";
      for (const b of ch.bullets) body += "<li>" + escapeHtml(b) + "</li>";
      body += "</ul>";
    }
    if (ch.table && Array.isArray(ch.table.rows) && ch.table.rows.length) {
      body += "<table>";
      ch.table.rows.forEach((row, idx) => {
        body += "<tr>";
        const tag = idx === 0 ? "th" : "td";
        row.forEach((c) => {
          body += "<" + tag + ">" + escapeHtml(c) + "</" + tag + ">";
        });
        body += "</tr>";
      });
      body += "</table>";
    }
    body += "</section>";
  }
  body +=
    '<div class="footer">Gerado offline pelo Syntexa — ' +
    new Date().toLocaleDateString("pt-BR") +
    "</div>";
  return (
    "<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"/><title>" +
    escapeHtml(doc.title) +
    "</title>" +
    head +
    "</head><body>" +
    body +
    "</body></html>"
  );
}

function buildRichPlanHtml(doc) {
  // V53 — HTML enriquecido para PDF, usando apenas cores hex/rgb (não oklab)
  // para compatibilidade com html2canvas/jsPDF.
  const head =
    "<style>" +
    "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');" +
    "body{font-family:'Inter','Segoe UI',Arial,sans-serif;color:#1e293b;line-height:1.6;max-width:800px;margin:0 auto;padding:32px 28px;background:#fff;}" +
    "h1{font-size:32px;font-weight:700;color:#0f172a;margin:0 0 8px;letter-spacing:-0.02em;}" +
    "h2{font-size:20px;font-weight:600;color:#1e293b;margin:32px 0 12px;padding-bottom:6px;border-bottom:2px solid #10b981;}" +
    "h3{font-size:15px;font-weight:600;color:#334155;margin:20px 0 8px;}" +
    ".subtitle{color:#64748b;font-size:14px;margin-bottom:28px;}" +
    ".meta{display:flex;gap:24px;flex-wrap:wrap;margin:20px 0;color:#475569;font-size:13px;}" +
    ".meta-item{display:flex;align-items:center;gap:6px;}" +
    ".meta-dot{width:8px;height:8px;border-radius:50%;background:#10b981;}" +
    "p{margin:0 0 12px;font-size:14px;color:#334155;}" +
    "ul{margin:8px 0 16px 20px;padding:0;font-size:14px;color:#334155;}" +
    "li{margin-bottom:6px;}" +
    "strong{color:#0f172a;font-weight:600;}" +
    "em{color:#475569;font-style:italic;}" +
    "table{border-collapse:collapse;width:100%;margin:12px 0 16px;font-size:13px;}" +
    "td,th{border:1px solid #cbd5e1;padding:8px 10px;text-align:left;}" +
    "th{background:#f8fafc;font-weight:600;color:#1e293b;}" +
    "tr:nth-child(even){background:#f8fafc;}" +
    ".demo-box{border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin:16px 0;background:#f8fafc;}" +
    ".demo-title{font-size:13px;font-weight:600;color:#10b981;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.05em;}" +
    ".sheet-table{width:100%;border-collapse:collapse;font-size:12px;margin:8px 0;}" +
    ".sheet-table td,.sheet-table th{border:1px solid #cbd5e1;padding:6px 8px;text-align:right;font-family:'Segoe UI',monospace;}" +
    ".sheet-table th{background:#ecfdf5;color:#065f46;text-align:left;}" +
    ".sheet-total{background:#ecfdf5;font-weight:600;color:#065f46;}" +
    ".footer{margin-top:40px;padding-top:12px;border-top:1px solid #e2e8f0;color:#94a3b8;font-size:12px;text-align:center;}" +
    ".section{page-break-inside:avoid;margin-bottom:24px;}" +
    "</style>";

  let body = "<div class='section'>";
  body += "<h1>" + escapeHtml(doc.title) + "</h1>";
  if (doc.subtitle) body += '<p class="subtitle">' + escapeHtml(doc.subtitle) + "</p>";
  if (doc.meta) {
    body += '<div class="meta">';
    if (doc.meta.chapters) body += '<div class="meta-item"><span class="meta-dot"></span>' + escapeHtml(doc.meta.chapters) + "</div>";
    if (doc.meta.plans) body += '<div class="meta-item"><span class="meta-dot"></span>' + escapeHtml(doc.meta.plans) + "</div>";
    if (doc.meta.icp) body += '<div class="meta-item"><span class="meta-dot"></span>' + escapeHtml(doc.meta.icp) + "</div>";
    if (doc.meta.stage) body += '<div class="meta-item"><span class="meta-dot"></span>' + escapeHtml(doc.meta.stage) + "</div>";
    body += "</div>";
  }
  body += "</div>";

  if (doc.letter && doc.letter.length) {
    body += "<div class='section'>";
    body += "<h2>Carta do Fundador</h2>";
    for (const p of doc.letter) body += "<p>" + escapeHtml(p) + "</p>";
    body += "</div>";
  }

  if (doc.demo) {
    body += "<div class='section'>";
    body += "<h2>Demonstração</h2>";
    if (doc.demo.title) body += "<p><strong>" + escapeHtml(doc.demo.title) + "</strong></p>";
    if (doc.demo.description) body += "<p>" + escapeHtml(doc.demo.description) + "</p>";
    if (doc.demo.sheet && doc.demo.sheet.length) {
      body += '<div class="demo-box">';
      if (doc.demo.chatLabel) body += '<div class="demo-title">' + escapeHtml(doc.demo.chatLabel) + "</div>";
      if (doc.demo.userPrompt) body += "<p><strong>Usuário:</strong> " + escapeHtml(doc.demo.userPrompt) + "</p>";
      if (doc.demo.aiResponse) body += "<p><strong>Syntexa:</strong> " + escapeHtml(doc.demo.aiResponse) + "</p>";
      body += '<table class="sheet-table">';
      body += "<tr><th>Mês</th><th>Receita</th><th>Custo</th><th>Lucro</th></tr>";
      for (const row of doc.demo.sheet) {
        body += "<tr><td>" + escapeHtml(row[0]) + "</td><td>" + escapeHtml(row[1]) + "</td><td>" + escapeHtml(row[2]) + "</td><td>" + escapeHtml(row[3]) + "</td></tr>";
      }
      if (doc.demo.total) {
        body += '<tr class="sheet-total"><td>Total</td><td>' + escapeHtml(doc.demo.total.receita) + "</td><td>" + escapeHtml(doc.demo.total.custo) + "</td><td>" + escapeHtml(doc.demo.total.lucro) + "</td></tr>";
      }
      body += "</table>";
      if (doc.demo.sheetCaption) body += "<p><em>" + escapeHtml(doc.demo.sheetCaption) + "</em></p>";
      body += "</div>";
    }
    body += "</div>";
  }

  if (doc.chapters && doc.chapters.length) {
    body += "<div class='section'>";
    body += "<h2>Índice</h2>";
    body += "<ul>";
    for (const ch of doc.chapters) {
      body += "<li><strong>" + escapeHtml(ch.number) + "</strong> — " + escapeHtml(ch.title) + "</li>";
    }
    body += "</ul>";
    body += "</div>";

    for (const ch of doc.chapters) {
      body += "<div class='section'>";
      body += "<h2>CAPÍTULO " + escapeHtml(ch.number) + "</h2>";
      body += "<h3>" + escapeHtml(ch.title) + "</h3>";
      if (ch.lead) body += "<p><em>" + escapeHtml(ch.lead) + "</em></p>";
      for (const p of ch.paragraphs || []) body += "<p>" + escapeHtml(p) + "</p>";
      if (ch.bullets && ch.bullets.length) {
        body += "<ul>";
        for (const b of ch.bullets) body += "<li>" + escapeHtml(b) + "</li>";
        body += "</ul>";
      }
      if (ch.table && Array.isArray(ch.table.rows) && ch.table.rows.length) {
        body += "<table>";
        ch.table.rows.forEach((row, idx) => {
          body += "<tr>";
          const tag = idx === 0 ? "th" : "td";
          row.forEach((c) => {
            body += "<" + tag + ">" + escapeHtml(c) + "</" + tag + ">";
          });
          body += "</tr>";
        });
        body += "</table>";
      }
      body += "</div>";
    }
  }

  if (doc.plans && doc.plans.length) {
    body += "<div class='section'>";
    body += "<h2>Planos Ativos</h2>";
    for (const pl of doc.plans) {
      body += "<h3>" + escapeHtml(pl.name) + " — " + escapeHtml(pl.price) + "</h3>";
      if (pl.description) body += "<p><em>" + escapeHtml(pl.description) + "</em></p>";
      if (pl.features && pl.features.length) {
        body += "<ul>";
        for (const f of pl.features) body += "<li>" + escapeHtml(f) + "</li>";
        body += "</ul>";
      }
    }
    body += "</div>";
  }

  body += '<div class="footer">' + escapeHtml(doc.footer || "Gerado pelo Syntexa — " + new Date().toLocaleDateString("pt-BR")) + "</div>";

  return "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'/><title>" + escapeHtml(doc.title) + "</title>" + head + "</head><body>" + body + "</body></html>";
}

async function downloadPlanAsPdf() {
  // V59 — PDF real via html2pdf.js com buildRichPlanHtml (cores hex, sem oklab).
  // O buildRichPlanHtml gera HTML autônomo com TODO o conteúdo do PLAN_DOCUMENT.
  const html2pdf = (await import("html2pdf.js")).default;

  const container = document.createElement("div");
  container.innerHTML = buildRichPlanHtml(PLAN_DOCUMENT);
  document.body.appendChild(container);

  const opt = {
    margin: [10, 10, 10, 10],
    filename: "Syntexa-Plano-de-Negocios.pdf",
    image: { type: "jpeg", quality: 0.96 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      backgroundColor: "#ffffff",
      logging: false,
    },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    pagebreak: { mode: ["css", "legacy"], avoid: ".section, table, h2, h3" },
  };

  try {
    await html2pdf().set(opt).from(container).save();
  } finally {
    document.body.removeChild(container);
  }
}

function downloadPlanAsDoc(doc) {
  const html = buildPlanHtml(doc);
  // Word/LibreOffice abrem HTML com este mime nativamente.
  const wordHeader =
    '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">';
  const full = wordHeader + html.replace(/^<!doctype html>\s*<html[^>]*>/i, "");
  const blob = new Blob(["\ufeff", full], {
    type: "application/msword;charset=utf-8",
  });
  downloadBlob(blob, "syntexa-plano-de-negocios.doc");
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Componentes visuais                                                        */
/* ────────────────────────────────────────────────────────────────────────── */

function GradientHero({ children }) {
  return (
    <div className="relative overflow-hidden rounded-[28px] border border-emerald-100/60 bg-white">
      {/* Mesh decorativo */}
      <svg
        className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.55]"
        viewBox="0 0 800 400"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="g1" cx="20%" cy="0%" r="60%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="g2" cx="80%" cy="100%" r="55%">
            <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.16" />
            <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0" />
          </radialGradient>
          <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#0f172a" strokeOpacity="0.04" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="800" height="400" fill="url(#grid)" />
        <rect width="800" height="400" fill="url(#g1)" />
        <rect width="800" height="400" fill="url(#g2)" />
      </svg>
      <div className="relative z-10 px-6 py-10 sm:px-10 sm:py-14">{children}</div>
    </div>
  );
}

function KpiTile({ label, value, sub, icon }) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white/80 p-4 backdrop-blur transition hover:border-emerald-200 hover:shadow-sm">
      <div className="flex items-center gap-2 text-emerald-700">
        <Icon d={I[icon] || I.spark} size={16} />
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-700/80">{label}</p>
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-zinc-900">{value}</p>
      {sub ? <p className="mt-1 text-xs text-zinc-500">{sub}</p> : null}
    </div>
  );
}

function ChapterCard({ ch }) {
  return (
    <motion.section
      id={ch.id}
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="plan-chapter relative scroll-mt-24 rounded-[22px] border border-zinc-200/80 bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-8 print:break-inside-avoid print:shadow-none"
    >
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-linear-to-br from-emerald-50 to-emerald-100/70 text-emerald-700 ring-1 ring-emerald-200/60">
          <Icon d={I[ch.icon] || I.spark} size={20} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[11px] tracking-[0.2em] text-zinc-400">CAPÍTULO {ch.number}</p>
          <h2 className="mt-1 text-[1.35rem] font-semibold tracking-tight text-zinc-900 sm:text-[1.55rem]">
            {ch.title}
          </h2>
          {ch.lead ? (
            <p className="mt-2 text-[15px] font-medium leading-snug text-emerald-800/90">{ch.lead}</p>
          ) : null}
        </div>
      </div>

      <div className="mt-5 space-y-4 text-[15px] leading-[1.7] text-zinc-700">
        {(ch.paragraphs || []).map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>

      {ch.bullets && ch.bullets.length ? (
        <ul className="mt-5 space-y-2">
          {ch.bullets.map((b) => (
            <li key={b} className="flex items-start gap-3 text-[14.5px] text-zinc-700">
              <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {ch.table && ch.table.rows && ch.table.rows.length ? (
        <div className="mt-6 overflow-hidden rounded-xl border border-zinc-200">
          <table className="min-w-full text-left text-[13.5px]">
            <tbody>
              {ch.table.rows.map((row, ri) => (
                <tr
                  key={ri}
                  className={
                    ri === 0
                      ? "bg-linear-to-r from-emerald-50 to-emerald-50/40 text-emerald-900"
                      : "border-t border-zinc-100 odd:bg-zinc-50/40"
                  }
                >
                  {row.map((cell, ci) => (
                    <td
                      key={ci}
                      className={
                        "px-4 py-3 align-top " +
                        (ri === 0 ? "font-semibold tracking-tight" : "text-zinc-700")
                      }
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </motion.section>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Mockup ao vivo: chat → planilha estruturada (provando a tese visualmente)  */
/* ────────────────────────────────────────────────────────────────────────── */

function ChatPreviewMockup() {
  const sheet = [
    { mes: "Jan", receita: 18500, custo: 11200, lucro: 7300 },
    { mes: "Fev", receita: 22300, custo: 12100, lucro: 10200 },
    { mes: "Mar", receita: 28800, custo: 14400, lucro: 14400 },
    { mes: "Abr", receita: 33500, custo: 15800, lucro: 17700 },
    { mes: "Mai", receita: 39200, custo: 17200, lucro: 22000 },
    { mes: "Jun", receita: 46800, custo: 19100, lucro: 27700 },
  ];
  const totalReceita = sheet.reduce((a, b) => a + b.receita, 0);
  const totalLucro = sheet.reduce((a, b) => a + b.lucro, 0);
  const fmt = (n) => "R$ " + n.toLocaleString("pt-BR");

  return (
    <div className="overflow-hidden rounded-[24px] border border-zinc-200 bg-linear-to-br from-zinc-50 via-white to-emerald-50/30 p-1 shadow-[0_8px_30px_rgba(15,23,42,0.06)]">
      <div className="rounded-[20px] bg-white p-5 sm:p-7">
        {/* Cabeçalho mock janela */}
        <div className="mb-5 flex items-center justify-between border-b border-zinc-100 pb-3">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-400/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
          </div>
          <p className="font-mono text-[11px] tracking-wide text-zinc-400">syntexa.app · chat ao vivo</p>
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 ring-1 ring-emerald-200">
            ● online
          </span>
        </div>

        {/* Bolha do usuário */}
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-zinc-600">
            <Icon d={I.user} size={16} />
          </div>
          <div className="max-w-[80%] rounded-2xl rounded-tl-sm bg-zinc-100 px-4 py-2.5 text-[14px] text-zinc-800">
            Monta uma planilha de fluxo de caixa do meu negócio nos últimos 6 meses, com receita, custo e lucro. Quero exportar pro Excel.
          </div>
        </div>

        {/* Bolha da IA */}
        <div className="mt-4 flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
            <Icon d={I.bot} size={16} />
          </div>
          <div className="flex-1">
            <div className="rounded-2xl rounded-tl-sm bg-linear-to-br from-emerald-50/70 to-white px-4 py-3 text-[14px] text-zinc-800 ring-1 ring-emerald-100">
              <p className="mb-2">
                Pronto. Montei o fluxo de caixa Jan-Jun com receita, custo e lucro. Receita total{" "}
                <strong className="text-emerald-800">{fmt(totalReceita)}</strong>, lucro acumulado{" "}
                <strong className="text-emerald-800">{fmt(totalLucro)}</strong>{" "}
                (margem ~{Math.round((totalLucro / totalReceita) * 100)}%).
              </p>

              {/* Planilha embedada */}
              <div className="mt-3 overflow-hidden rounded-lg border border-zinc-200 bg-white">
                <div className="flex items-center justify-between border-b border-zinc-100 bg-zinc-50/70 px-3 py-1.5">
                  <div className="flex items-center gap-2">
                    <Icon d={I.table} size={13} className="text-emerald-700" />
                    <p className="font-mono text-[11px] text-zinc-500">fluxo-caixa-2026.xlsx</p>
                  </div>
                  <p className="font-mono text-[10px] text-zinc-400">7 linhas · 4 colunas</p>
                </div>
                <table className="w-full text-left text-[12.5px]">
                  <thead>
                    <tr className="bg-emerald-50/60 text-emerald-900">
                      <th className="px-3 py-1.5 font-semibold">Mês</th>
                      <th className="px-3 py-1.5 text-right font-semibold">Receita</th>
                      <th className="px-3 py-1.5 text-right font-semibold">Custo</th>
                      <th className="px-3 py-1.5 text-right font-semibold">Lucro</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sheet.map((r, i) => (
                      <tr key={r.mes} className={i % 2 ? "bg-zinc-50/40" : ""}>
                        <td className="px-3 py-1.5 font-medium text-zinc-800">{r.mes}</td>
                        <td className="px-3 py-1.5 text-right font-mono text-zinc-700">{fmt(r.receita)}</td>
                        <td className="px-3 py-1.5 text-right font-mono text-zinc-700">{fmt(r.custo)}</td>
                        <td className="px-3 py-1.5 text-right font-mono font-semibold text-emerald-700">
                          {fmt(r.lucro)}
                        </td>
                      </tr>
                    ))}
                    <tr className="border-t-2 border-emerald-200 bg-emerald-50/40 font-semibold text-emerald-900">
                      <td className="px-3 py-1.5">Total</td>
                      <td className="px-3 py-1.5 text-right font-mono">{fmt(totalReceita)}</td>
                      <td className="px-3 py-1.5 text-right font-mono">
                        {fmt(sheet.reduce((a, b) => a + b.custo, 0))}
                      </td>
                      <td className="px-3 py-1.5 text-right font-mono">{fmt(totalLucro)}</td>
                    </tr>
                  </tbody>
                </table>

                {/* Mini gráfico SVG (lucro mês a mês) */}
                <div className="border-t border-zinc-100 bg-zinc-50/40 px-3 py-3">
                  <div className="mb-1 flex items-center justify-between">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                      Lucro mês a mês
                    </p>
                    <p className="font-mono text-[10px] text-emerald-700">+{Math.round((sheet[5].lucro / sheet[0].lucro - 1) * 100)}% no semestre</p>
                  </div>
                  <svg viewBox="0 0 240 60" className="h-12 w-full">
                    <defs>
                      <linearGradient id="lineFill" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
                        <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    {(() => {
                      const max = Math.max(...sheet.map((r) => r.lucro));
                      const step = 240 / (sheet.length - 1);
                      const pts = sheet.map((r, i) => [i * step, 55 - (r.lucro / max) * 45]);
                      const path = pts.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(" ");
                      const area = `${path} L240,60 L0,60 Z`;
                      return (
                        <>
                          <path d={area} fill="url(#lineFill)" />
                          <path d={path} fill="none" stroke="#10b981" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
                          {pts.map((p, i) => (
                            <circle key={i} cx={p[0]} cy={p[1]} r="2.5" fill="#10b981" />
                          ))}
                        </>
                      );
                    })()}
                  </svg>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <button className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-[12px] font-semibold text-white shadow-sm">
                  <Icon d={I.download} size={13} /> Baixar .xlsx
                </button>
                <button className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-[12px] font-semibold text-zinc-700">
                  <Icon d={I.word} size={13} /> Word (.docx)
                </button>
                <button className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-[12px] font-semibold text-zinc-700">
                  <Icon d={I.printer} size={13} /> PDF
                </button>
              </div>
            </div>
            <p className="mt-1 ml-1 text-[11px] text-zinc-400">resposta gerada em 8.4s · 6 fontes consultadas</p>
          </div>
        </div>

        {/* Caixa de input fake */}
        <div className="mt-5 flex items-center gap-2 rounded-2xl border border-zinc-200 bg-zinc-50/60 px-3 py-2">
          <div className="flex-1 text-[13px] text-zinc-400">Pergunte qualquer coisa — eu entrego o arquivo pronto.</div>
          <button className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600 text-white">
            <Icon d={I.send} size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Cards de planos                                                            */
/* ────────────────────────────────────────────────────────────────────────── */

export function PlanCard({ plan, onSubscribe, locale }) {
  const isFree = plan.key === "free";
  const isPro = plan.highlighted;
  return (
    <article
      className={
        "relative flex h-full flex-col rounded-[20px] border p-6 transition " +
        (isPro
          ? "border-emerald-300 bg-linear-to-b from-emerald-50/80 to-white shadow-[0_10px_30px_-12px_rgba(16,185,129,0.35)] ring-1 ring-emerald-200/60"
          : "border-zinc-200 bg-white hover:border-zinc-300")
      }
    >
      {isPro ? (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-emerald-600 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-white shadow-sm">
          {t('planMostChosen', locale)}
        </span>
      ) : null}

      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">{plan.tag}</p>
        {isFree ? (
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600">{t('planFreeBadge', locale)}</span>
        ) : null}
      </div>
      <h3 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-900">{plan.name}</h3>
      <p className="mt-1 min-h-[60px] text-[13.5px] leading-relaxed text-zinc-600">{plan.description}</p>

      <div className="mt-4 flex items-baseline gap-1">
        <span className="text-4xl font-semibold tracking-tight text-zinc-900">{plan.price}</span>
        <span className="text-sm text-zinc-500">{plan.priceLabel}</span>
      </div>

      {!isFree ? (
        <p className="mt-1 text-[12px] text-emerald-700">
          {t('planStudentLabel', locale)} <span className="font-semibold">{plan.priceStudent}</span>{" "}
          <span className="text-zinc-500">{t('planStudentMonth', locale)}</span>
        </p>
      ) : (
        <p className="mt-1 text-[12px] text-zinc-500">{t('planNoCard', locale)}</p>
      )}

      <ul className="mt-5 space-y-2.5 text-[13.5px] text-zinc-700">
        {plan.features.map((f) => (
          <li key={f} className="flex items-start gap-2.5">
            <span
              className={
                "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full " +
                (isPro ? "bg-emerald-600 text-white" : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200")
              }
            >
              <Icon d={I.check} size={11} stroke={2.4} />
            </span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        <Button
          variant={isPro ? "primary" : "outline"}
          className="w-full justify-center rounded-xl"
          onClick={() => onSubscribe(plan.key || "basic")}
        >
          {isFree ? t('planStartFree', locale) : t('planSubscribe', locale) + " " + plan.name}
        </Button>
      </div>
    </article>
  );
}

/* ────────────────────────────────────────────────────────────────────────── */
/*  Página principal                                                            */
/* ────────────────────────────────────────────────────────────────────────── */

export function BusinessPlanPage({ plans, onSubscribe, showBusinessPlan = true }) {
  const { locale } = useLanguage();
  const [exportBusy, setExportBusy] = useState(null);

  const runExport = useCallback(
    async (kind) => {
      if (typeof window === "undefined") return;
      setExportBusy(kind);
      try {
        if (kind === "pdf") {
          downloadPlanAsPdf(locale);
        } else {
          downloadPlanAsDoc(PLAN_DOCUMENT, locale);
        }
      } catch (e) {
        const text = PLAN_DOCUMENT.chapters.map((ch) => {
          const parts = [`${ch.number}. ${ch.title}`, "", ch.lead || ""];
          ch.paragraphs.forEach((p) => parts.push(p));
          if (ch.bullets) ch.bullets.forEach((b) => parts.push("• " + b));
          return parts.filter(Boolean).join("\n\n");
        }).join("\n\n---\n\n");
        const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
        downloadBlob(blob, "syntexa-plano-de-negocios.txt");
      } finally {
        setExportBusy(null);
      }
    },
    [locale]
  );

  const handlePrint = useCallback(() => {
    if (typeof window !== "undefined") window.print();
  }, []);

  return (
    <div id="business-plan-root" className="mx-auto flex w-full max-w-[1180px] flex-col gap-10 px-4 py-8 sm:px-6 sm:py-12">
      <style
        dangerouslySetInnerHTML={{
          __html: `
@media print {
  .no-print { display: none !important; }
  body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .plan-chapter { page-break-inside: avoid; }
}`,
        }}
      />

      {/* HERO */}
      <GradientHero>
        <div className="grid items-center gap-8 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/70 bg-white/70 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-800 backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Plano de Negócios · 2026
            </div>
            <h1 className="mt-4 font-serif text-[2.4rem] font-semibold leading-[1.05] tracking-tight text-zinc-900 sm:text-[3.1rem]">
              {PLAN_DOCUMENT.title.split(" — ")[0]}
              <span className="block text-emerald-700">{PLAN_DOCUMENT.title.split(" — ")[1]}</span>
            </h1>
            <p className="mt-4 max-w-xl text-[15.5px] leading-relaxed text-zinc-600">
              Documento operativo da Syntexa — não é pitch deck, não é placeholder. É o plano que estamos executando esta semana.
              Lê em 12 minutos, baixa em PDF/Word em 1 clique.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button
                variant="primary"
                className="rounded-xl shadow-sm"
                disabled={exportBusy !== null}
                onClick={() => void runExport("pdf")}
              >
                <Icon d={I.download} size={15} className="mr-1.5" />
                {exportBusy === "pdf" ? "Gerando PDF…" : "Baixar PDF"}
              </Button>
              <Button
                variant="outline"
                className="rounded-xl"
                disabled={exportBusy !== null}
                onClick={() => void runExport("docx")}
              >
                <Icon d={I.word} size={15} className="mr-1.5" />
                {exportBusy === "docx" ? "Gerando Word…" : "Word (.docx)"}
              </Button>
              <Button variant="outline" className="rounded-xl" onClick={handlePrint}>
                <Icon d={I.printer} size={15} className="mr-1.5" />
                Imprimir
              </Button>
            </div>

            <div className="mt-6 flex items-center gap-3 text-[13px] text-zinc-600">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-900 text-[12px] font-bold text-white">
                LP
              </div>
              <div>
                <p className="font-medium text-zinc-800">Luis Paulo de Oliveira</p>
                <p className="text-[12px] text-zinc-500">Fundador · escreveu este documento à mão</p>
              </div>
            </div>
          </div>

          {/* Logo + cartão lateral */}
          <div className="relative">
            <div className="mx-auto flex h-36 w-36 items-center justify-center rounded-3xl border border-emerald-200 bg-white shadow-[0_10px_30px_-12px_rgba(16,185,129,0.35)]">
              <img
                src="/LOGOTIPO.png?v=blue3"
                alt="Logotipo Syntexa"
                className="h-28 w-28 rounded-xl object-contain"
              />
            </div>
            <div className="mx-auto mt-5 max-w-sm rounded-2xl border border-zinc-200 bg-white/80 p-4 backdrop-blur">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500">Status atual</p>
              <p className="mt-2 text-[14px] leading-relaxed text-zinc-700">
                Produto no ar em <strong className="text-zinc-900">syntexabr.com.br</strong>, com chat multimodal,
                desktop instalável e exportação real para PDF, Word e Excel. Próximo marco:{" "}
                <strong className="text-emerald-700">100 pagantes recorrentes</strong>.
              </p>
            </div>
          </div>
        </div>
      </GradientHero>

      {/* KPI bar */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiTile icon="layers" label="Capítulos" value="14" sub="Operativos, sem enchimento" />
        <KpiTile icon="cash" label="Planos" value="R$ 0–199" sub="4 faixas · estudante 50% OFF" />
        <KpiTile icon="users" label="ICP" value="Prosumer BR" sub="Estudante, professor, liberal" />
        <KpiTile icon="rocket" label="Estágio" value="Seed" sub="Produto no ar · primeiros pagantes" />
      </div>

      {/* CARTA DO FUNDADOR */}
      <section className="rounded-[22px] border border-zinc-200 bg-linear-to-br from-white to-emerald-50/40 p-6 sm:p-8 print:break-inside-avoid">
        <div className="flex items-center gap-2 text-emerald-700">
          <Icon d={I.signature} size={18} />
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em]">Carta do fundador</p>
        </div>
        <div className="mt-4 max-w-3xl space-y-4 text-[15.5px] leading-[1.75] text-zinc-700">
          <p>
            Construí a Syntexa porque me cansei de ver gente boa perdendo tarde inteira formatando o que a IA já tinha
            respondido. A pergunta vinha rápida, a resposta vinha rápida, e aí começava a parte triste: copia, cola,
            ajusta espaçamento, vira tabela, exporta PDF, manda pro cliente.
          </p>
          <p>
            Esse documento não é um deck. É o plano operacional que eu uso pra decidir o que fazer essa semana. Os
            números são reais — alguns bons, alguns ruins. Os capítulos foram escritos na ordem em que penso:
            primeiro o que existe hoje, depois quem está atendendo, depois como vamos crescer e, por fim, onde podemos
            quebrar.
          </p>
          <p>
            Se você é investidor lendo isso: bem-vindo. Aviso que não vou aumentar número pra ficar bonito. Se você é
            usuário: obrigado por chegar até aqui — você é a razão de a Syntexa existir.
          </p>
          <p className="font-serif text-[1.2rem] italic text-zinc-800">— Luis Paulo</p>
        </div>
      </section>

      {/* MOCKUP "PROVA VIVA" */}
      <section className="no-print">
        <div className="mb-5 flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-end">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-700">Demonstração</p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900 sm:text-[1.7rem]">
              Da pergunta à planilha pronta — sem etapa intermediária
            </h2>
          </div>
          <p className="max-w-md text-[13.5px] leading-relaxed text-zinc-500">
            Mesma resposta que o cliente paga consultor pra montar. Aqui sai do chat já formatada, com gráfico e
            botões de export. Esse é o produto.
          </p>
        </div>
        <ChatPreviewMockup />
      </section>

      {/* ÍNDICE */}
      <nav className="no-print rounded-[22px] border border-zinc-200 bg-white p-5 sm:p-6">
        <div className="flex items-center gap-2 text-zinc-700">
          <Icon d={I.layers} size={16} className="text-emerald-700" />
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em]">Índice</p>
        </div>
        <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {PLAN_DOCUMENT.chapters.map((ch) => (
            <li key={ch.id}>
              <a
                href={"#" + ch.id}
                className="group flex items-center gap-3 rounded-xl border border-transparent px-2 py-1.5 text-[13.5px] text-zinc-700 transition hover:border-emerald-200 hover:bg-emerald-50/60 hover:text-emerald-900"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-zinc-100 font-mono text-[10px] font-semibold text-zinc-600 group-hover:bg-emerald-100 group-hover:text-emerald-800">
                  {ch.number}
                </span>
                <span className="truncate">{ch.title}</span>
              </a>
            </li>
          ))}
        </ol>
      </nav>

      {/* CAPÍTULOS */}
      <div className="flex flex-col gap-5">
        {PLAN_DOCUMENT.chapters.map((ch) => (
          <ChapterCard key={ch.id} ch={ch} />
        ))}
      </div>

      {/* PLANOS COMERCIAIS */}
      <section id="planos" className="rounded-[22px] border border-zinc-200 bg-white p-6 sm:p-8">
        <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-700">Planos ativos</p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900 sm:text-[1.75rem]">
              Quanto custa usar a Syntexa
            </h2>
            <p className="mt-2 max-w-2xl text-[14.5px] leading-relaxed text-zinc-600">
              Quatro planos diretos, sem letra miúda. Estudante com e-mail .edu paga metade em qualquer plano pago — política permanente.
            </p>
          </div>
          <a
            href="#thesis"
            className="hidden rounded-xl border border-zinc-200 px-3 py-2 text-[12.5px] text-zinc-600 transition hover:border-emerald-300 hover:text-emerald-800 sm:inline-flex sm:items-center sm:gap-1"
          >
            Como cada plano encaixa na tese
            <Icon d={I.arrow} size={13} />
          </a>
        </div>

        <div className="mt-7 grid gap-5 sm:grid-cols-2 lg:grid-cols-4 no-print">
          {plans.map((plan) => (
            <PlanCard key={plan.key} plan={plan} onSubscribe={onSubscribe} />
          ))}
        </div>

        <p className="mt-6 text-center text-[12.5px] text-zinc-500">
          Pagamento via Stripe em BRL · cancelamento self-service · sem fidelidade
        </p>
      </section>

      {/* RODAPÉ ASSINADO */}
      <footer className="rounded-[22px] border border-zinc-200 bg-linear-to-br from-zinc-50 to-white p-6 text-center sm:p-8">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-900 text-white">
          <Icon d={I.signature} size={22} />
        </div>
        <p className="mt-4 text-[15px] leading-relaxed text-zinc-700">
          Construído no Brasil, em código próprio, com cuidado de quem usa o produto todos os dias.
        </p>
        <p className="mt-1 font-serif text-[18px] italic text-zinc-900">Luis Paulo de Oliveira</p>
        <p className="mt-1 text-[12px] text-zinc-500">
          Fundador da Syntexa · contato direto:{" "}
          <a href="mailto:contato@syntexabr.com.br" className="font-medium text-emerald-700 hover:underline">
            contato@syntexabr.com.br
          </a>
        </p>
      </footer>
    </div>
  );
}
