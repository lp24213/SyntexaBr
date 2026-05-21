# SYNTEXA — Plano de Negócios Institucional

## Infraestrutura Cognitiva Soberana para Execução Distribuída de Inteligência Artificial

---

## 1. Visão Executiva

A SYNTEXA desenvolve **infraestrutura cognitiva operacional** — uma camada de software que transforma modelos de linguagem em entregas profissionais prontas (documentos, planilhas, relatórios, áudio e imagem) para o mercado brasileiro.

Diferentemente de chatbots genéricos, a SYNTEXA orquestra **workflow completo**: o usuário faz uma pergunta, a plataforma estrutura a resposta, formata e exporta em PDF, Excel, Word ou Markdown — tudo em português nativo, com contexto local e sem depender de copy-paste manual.

A arquitetura é **modular e preparada para escalar progressivamente conforme validação de mercado**:
- **Soberania operacional** — dados não saem da infraestrutura do cliente (opção on-premise)
- **Otimizações proprietárias** — pipeline de inferência quantizada e orquestração híbrida para reduzir dependência de terceiros ao longo do tempo
- **Latência otimizada** — edge deployment e inferência local quando aplicável
- **Compliance institucional** — audit trails, isolamento de tenants, preparação para certificações

---

## 2. Posicionamento de Mercado

### 2.1 O Que a SYNTEXA NÃO É

- Não é apenas um wrapper de API externa
- Não é um chatbot de consumo casual
- Não é um SaaS de templates genéricos
- Não depende exclusivamente de modelos de terceiros — desenvolvemos otimizações proprietárias para reduzir essa dependência ao longo do tempo

### 2.2 O Que a SYNTEXA É

- **Camada operacional de IA** — transforma prompts em entregas profissionais estruturadas (PDF, Excel, Word, Markdown)
- **Plataforma multimodal integrada** — texto, imagem, áudio, documentos e planilhas em workflow único
- **Arquitetura híbrida** — modelos open-source avançados (LLaMA 13B) como base operacional, integrados a camadas proprietárias de orquestração, exportação e contexto PT-BR; modelo próprio "Syntexa Foundation Model" (~50M parâmetros) em estágio experimental de treinamento
- **Infraestrutura enterprise-ready** — preparada para SLA, compliance e isolamento de tenants
- **Arquitetura modular** — permite execução local, cloud híbrida ou edge, conforme necessidade do cliente

### 2.3 Diferenciais Competitivos

| Aspecto | SYNTEXA | Concorrência |
|---------|---------|--------------|
| Entrega | Documento pronto (PDF/Excel/Word) a partir de prompt | Resposta em chat — copy-paste manual |
| Workflow | Pipeline completo: pergunta → estrutura → exporta | Ferramentas fragmentadas (chat + editor + conversor) |
| Português | Contexto local, jurídico e técnico nativo PT-BR | Genérico, traduzido ou com sotaque estrangeiro |
| Soberania | Opção on-premise / VPC — dados não saem | Dados processados em cloud de terceiros |
| Custo | Otimização por quantização e cache; escala sob demanda | Taxação por token + infraestrutura separada |
| Multimodal | STT, TTS, documentos, imagem em uma plataforma | Serviços de vários vendors com integração manual |

---

## 2.4 Posicionamento da IA Própria (Syntexa Foundation Model)

> **Nota institucional**: A Syntexa não se posiciona atualmente como uma "nova OpenAI" nem afirma possuir um modelo fundacional competitivo em escala global neste estágio. O posicionamento correto é: **infraestrutura própria em evolução, foco em workflow profissional e independência tecnológica progressiva**.

### Arquitetura Híbrida Atual

A arquitetura atual utiliza **modelos open-source avançados como base operacional** — incluindo variantes do LLaMA 13B — integrados a uma **camada proprietária de orquestração, exportação, automação documental e contexto em português brasileiro**.

Paralelamente, a Syntexa desenvolve internamente seu próprio modelo experimental (**"Syntexa Foundation Model"**), atualmente em estágio inicial de treinamento e pesquisa, com aproximadamente **50 milhões de parâmetros**. O objetivo estratégico de longo prazo é reduzir dependência de provedores externos e construir uma stack nacional de IA cada vez mais independente.

### Limitação Principal: Capacidade Computacional

Neste momento, a limitação principal não é software — é **capacidade computacional**.

O treinamento avançado do modelo proprietário exige infraestrutura significativamente superior à disponível hoje, especialmente em:

- GPU dedicada de alto desempenho;
- Memória RAM expandida;
- Armazenamento NVMe de alta velocidade;
- Capacidade distribuída de processamento;
- Infraestrutura própria ou colocation/datacenter.

### Tese de Investimento em Infraestrutura Própria

Parte central da tese de investimento da Syntexa é acelerar:

1. **Capacidade de treinamento**;
2. **Autonomia tecnológica**;
3. **Redução de custo marginal de inferência**;
4. **Construção de ativos proprietários de IA**.

Ainda assim, o foco operacional da empresa permanece pragmático:

- Validação de mercado;
- Aquisição de usuários;
- Retenção;
- Recorrência;
- Workflow profissional;
- Geração de documentos prontos via IA.

A Syntexa entende que **distribuição e produto vêm antes de escala de modelo fundacional**. O objetivo atual não é competir diretamente com gigantes globais em tamanho de modelo, mas construir uma **experiência verticalizada, eficiente e adaptada ao mercado brasileiro**.

### Frases-Recomendadas para Reuniões Institucionais

> **Opção A — Arquitetura Híbrida:**
> "A Syntexa utiliza arquitetura híbrida com modelos open-source avançados e camadas proprietárias de automação e workflow. Paralelamente, desenvolvemos nossa própria IA em estágio inicial, com foco em independência tecnológica progressiva conforme a infraestrutura evolui."

> **Opção B — Diferencial Operacional:**
> "O diferencial da Syntexa hoje não é afirmar que possui o maior modelo. É transformar IA em entrega profissional pronta, com automação, exportação estruturada e contexto operacional em português."

> **Opção C — Tese de Infraestrutura:**
> "O investimento buscado não serve apenas para crescimento comercial — ele também acelera capacidade computacional necessária para evolução da infraestrutura proprietária de IA."

---

## 2.5 Tração Inicial (Dados Reais)

**Status atual:** Produto em fase final de desenvolvimento (pre-launch público). A plataforma está operacional em ambiente de staging com beta testers internos e convidados. O **Syntexa Foundation Model** (~50M parâmetros) está em treinamento experimental contínuo com melhorias semanais de qualidade de resposta, enquanto a camada operacional utiliza modelos open-source avançados integrados às camadas proprietárias de orquestração e exportação.

| Métrica | Valor | Contexto |
|---------|-------|----------|
| Usuários cadastrados (beta) | ~45 | Equipe, advisors e beta testers convidados |
| Documentos exportados (teste) | ~120 | PDFs, Excel e Word gerados em validação interna |
| Sessões por semana (beta) | ~30 | Testes de uso real em cenários de documentos, educação e chat |
| Tempo médio de sessão | ~8 min | Testes focados; sessões longas em modo educação (~22 min) |
| Estados com acesso | 3 | São Paulo (sede), Minas Gerais, Rio de Janeiro |
| Usuários pagantes | 0 | **Ainda não iniciamos cobrança.** Foco atual: validar retenção e qualidade de exportação antes de monetizar. |

> **Próximo marco (Q2 2026):** Lançamento freemium público. Meta: 1.000 usuários ativos em 90 dias e primeiros 50 pagantes com retenção mensal > 40%.

---

## 2.6 Demo Visual

**Fluxo real da plataforma (3 passos):**

1. **Pergunta do usuário** — "Elabore um parecer jurídico sobre LGPD para uma fintech"
2. **IA estrutura** — A Syntexa gera o conteúdo com formatação profissional, citações e estrutura de capítulos
3. **Exporta pronto** — Download em PDF, Word ou Excel com identidade visual da empresa

**Screenshots sugeridos para incluir no deck:**
- Tela de chat com pergunta complexa
- Painel de exportação (PDF/Excel/Word)
- Documento final gerado (antes/depois)
- Modo educação com conteúdo estruturado
- Interface multimodal (imagem + texto)

---

## 2.7 Moat (Barreiras Competitivas)

A defesa da SYNTEXA não está em "ter um LLM próprio", mas em:

| Barreira | Descrição |
|----------|-----------|
| **UX de workflow** | Pipeline integrado: pergunta → estrutura → exporta. Nenhum concorrente entrega documento pronto em um clique. |
| **Contexto PT-BR** | Treinamento e fine-tuning em português jurídico, técnico e corporativo. |
| **Automação de export** | Motor de templates + engine de documentos proprietário (PDF/DOCX/XLSX). |
| **Pipeline de custo** | Quantização 4-bit, cache de respostas e roteamento híbrido reduzem custo por sessão em até 70%. |
| **Velocidade de execução** | Time enxuto com iteração rápida — novos modos de exportação em dias, não em quarters. |

---

## 3. Arquitetura Tecnológica

### 3.1 Stack Proprietário

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                    │
│         Next.js · React · Framer Motion · WebGL            │
├─────────────────────────────────────────────────────────────┤
│                   CAMADA DE ORQUESTRAÇÃO                     │
│  SovereignOrchestrator · Circuit Breaker · Health Checker  │
│  Retry Exponencial · Model Fallback Chain · Métricas         │
├─────────────────────────────────────────────────────────────┤
│                     MOTOR NEURAL                             │
│  NeuralEngine · Transformers · Quantização 4-bit (NF4)     │
│  LLaMA 13B + camada proprietária · Syntexa Foundation      │
│  Model (~50M params, experimental) · Streaming Token      │
├─────────────────────────────────────────────────────────────┤
│                   MULTIMODAL ENGINE                          │
│  STT (Whisper) · TTS (Piper/Coqui) · Document Engine      │
│  PDF · DOCX · XLSX · Markdown · HTML · Imagem              │
├─────────────────────────────────────────────────────────────┤
│                  INFRAESTRUTURA DISTRIBUÍDA                  │
│  AWS GPU Cluster · Cloudflare Edge · Railway Services      │
│  Kubernetes · Docker · Terraform · Prometheus · Grafana    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Camada Experimental

**QPanda3 Research Layer**: Integração experimental com QPanda3 para pesquisa em otimização probabilística, simulações computacionais híbridas e experimentação de execução distribuída.

> *Nota institucional: A camada QPanda3 é posicionada como pesquisa experimental em otimização probabilística, não como supremacia quântica ou hardware quântico proprietário.*

---

## 4. Modelo de Negócios

### 4.1 Camadas de Acesso

| Plano | Descrição | Público-Alvo |
|-------|-----------|--------------|
| **Syntexa Core** | Acesso gratuito com limites. Chat, exportações básicas e modelos fundamentais. | Estudantes, freelancers, early adopters |
| **Syntexa Pro** | Exportações ilimitadas, templates premium, voz e documentos. | Profissionais liberais, pequenas empresas |
| **Syntexa Team** | Múltiplos usuários, KB personalizada, relatórios de uso. | Escritórios, agências, equipes de produto |
| **Syntexa Enterprise** | Infraestrutura dedicada, SLA, on-premise, compliance, integração institucional. | Bancos, governos, healthcare, defesa |

### 4.2 Estrutura de Preços

- **Core**: Freemium com limites diários (acesso imediato)
- **Pro**: Assinatura mensal (R$ 49–89) com trial de 7 dias
- **Team**: Assinatura mensal por usuário (R$ 39) com gestor de licenças
- **Enterprise**: Contrato anual sob demanda com SLA e implementação dedicada

> Modelo freemium acelera adoção e gera dados de uso para iterar no produto antes de escalar vendas B2B.

### 4.3 Custo de Aquisição vs. Lifetime Value

| Métrica | Projeção Ano 1 |
|---------|------------------|
| CAC (Custo de Aquisição) | R$ 1.200 (B2B outbound) |
| LTV (Lifetime Value) | R$ 45.000 (Enterprise médio) |
| Churn Rate (mensal) | < 2% (sticky infraestrutura) |
| Payback Period | 4-6 meses |

---

## 5. Mercado-Alvo

### 5.1 Segmentos Primários

1. **Instituições Financeiras** (Itaú, Bradesco, XP)
   - Necessidade: compliance, dados sensíveis não podem sair
   - Valor: redução de 70% em custos de inferência vs. OpenAI

2. **Setor Público e Defesa**
   - Necessidade: soberania digital, execução em govcloud
   - Valor: infraestrutura auditável e isolada

3. **Healthcare e Pharma**
   - Necessidade: LGPD/HIPAA, processamento de documentos clínicos
   - Valor: pipeline multimodal para análise de laudos, receitas, prontuários

4. **Operadoras de Telecom**
   - Necessidade: atendimento escalável com voz em tempo real
   - Valor: STT/TTS com latência < 200ms em português

### 5.2 Tamanho de Mercado (TAM/SAM/SOM)

| Métrica | Valor | Base |
|---------|-------|------|
| TAM (Total Addressable Market) | US$ 200B | Mercado global de infraestrutura AI |
| SAM (Serviceable Addressable Market) | US$ 8B | LATAM + enterprise sovereign AI |
| SOM (Serviceable Obtainable Market) | US$ 120M | Brasil enterprise + scale-ups |

---

## 6. Estratégia Go-to-Market

### 6.1 Fase 1: Validação de Produto (0-6 meses)

- Lançamento freemium público (Syntexa Core) para captar usuários reais
- Meta: 1.000 usuários ativos e 50–100 pagantes
- Coleta de feedback iterativo sobre exportações, templates e UX
- Desenvolvimento dos primeiros case studies com usuários reais

### 6.2 Fase 2: Crescimento e Monetização (6-18 meses)

- Lançamento dos planos Pro e Team com funcionalidades premium
- Expansão de infraestrutura híbrida (cloud + on-premise option)
- Programa de parceiros de canal para revenda enterprise
- Meta: R$ 30k MRR

### 6.3 Fase 3: Escala Institucional (18-36 meses)

- Syntexa Enterprise com certificações SOC 2, ISO 27001
- Contratos governamentais e institucionais
- Expansão para LATAM (México, Colômbia, Chile) com contexto local

---

## 7. Roadmap Técnico

| Trimestre | Entrega |
|-----------|---------|
| Q1 2026 | Motor neural Syntexa production-grade · Circuit breaker · Health checks |
| Q2 2026 | Multimodal pipeline completo · Voice intelligence · Document engine |
| Q3 2026 | GPU cluster auto-scaling · Distributed inference · Edge deployment |
| Q4 2026 | Enterprise compliance · SOC 2 · Agentes autônomos v1 |
| Q1 2027 | QPanda3 integration v1 · Quantum-inspired optimization |
| Q2 2027 | Expansão LATAM · Partnerships estratégicos |

---

## 8. Time e Estrutura Organizacional

### 8.1 Estrutura Recomendada (36 meses)

```
CEO / Founder
├── CTO — Arquitetura e Runtime Neural
├── VP Engineering — Infraestrutura e DevOps
├── VP Product — Plataforma e APIs
├── VP Sales — Enterprise e Channels
└── Head of Research — QPanda3 e Otimização
```

### 8.2 Time Inicial (12 meses)

| Função | Headcount |
|--------|-----------|
| Deep Learning Engineers | 4 |
| Distributed Systems Engineers | 3 |
| Frontend / UX Engineers | 2 |
| DevOps / SRE | 2 |
| Product / Growth | 2 |
| Enterprise Sales | 2 |
| **Total** | **15** |

---

## 9. Projeções Financeiras

### 9.1 Receita Projetada (R$ milhões)

| Ano | Core/Studio | Nexus | Enterprise | Total |
|-----|-----------|-------|------------|-------|
| 1 | 0.3 | 0.5 | 1.2 | 2.0 |
| 2 | 0.8 | 2.5 | 5.0 | 8.3 |
| 3 | 1.5 | 6.0 | 15.0 | 22.5 |

### 9.2 Investimento Necessário

| Rodada | Valor | Uso |
|--------|-------|-----|
| Seed | R$ 2.5M | Time técnico, GPU infraestrutura, validação mercado |
| Series A | R$ 12M | Expansão de cluster, enterprise sales, compliance |
| Series B | R$ 35M | Expansão LATAM, QPanda3 research, aquisições |

---

## 10. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Escassez de GPU AWS | Média | Alto | Multi-cloud (Azure, GCP) + contratos reservados |
| Concorrência de big tech | Alta | Médio | Diferenciação por soberania e preço |
| Regulação de IA | Média | Médio | Compliance preemptivo, engajamento regulatório |
| Talento técnico escasso | Média | Alto | Parcerias com universidades, stock options |

---

## 11. Conclusão

A SYNTEXA posiciona-se como **a camada operacional que transforma IA em entrega profissional pronta** — não como mais um chatbot, mas como workflow completo de pergunta → estrutura → exporta.

O diferencial competitivo é a **execução**: entregar documentos, planilhas e relatórios formatados em português nativo, com contexto local brasileiro, de forma automatizada. A arquitetura modular permite evoluir de SaaS cloud para on-premise enterprise conforme a demanda do mercado valida cada camada.

O modelo de negócios prioriza B2B com alto LTV e baixo churn, sustentado por produto real, métricas de uso e iteração rápida com usuários pagantes. Paralelamente, o desenvolvimento do **Syntexa Foundation Model** avança conforme a infraestrutura computacional permite — reforçando a tese de independência tecnológica progressiva e construção de ativos proprietários de IA.

---

*Documento confidencial — SYNTEXA Infraestrutura Cognitiva*
*Versão 1.1 — Maio 2026*
