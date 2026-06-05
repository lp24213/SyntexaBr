# 🎨 GUIA DE INTEGRAÇÃO — COMPONENTES PREMIUM SyntexaBR

## FILOSOFIA
- ✅ Adicionar gradualmente SEM quebrar o site
- ✅ Usar como overlays/expandidores, não como replacements
- ✅ Manter identidade visual existente
- ✅ Testar responsividade em cada passo

## COMPONENTES DISPONÍVEIS

### TIER 1 — Base Visual Premium
1. **PremiumCanvas** — Grid animado leve com glow
   - Use em: `<div className="relative h-96"><PremiumCanvas /></div>`
   - Coloque ATRÁS de conteúdo com `pointer-events-none`

2. **FeatureGridPremium** — Grid de features com reveal on scroll
   - Substitui grids simples por versão premium

3. **EnterpriseCard** — Card elegante com glow
   - Use em: Seções de módulos, features, integrações

4. **BentoGrid** — Layout Apple-style
   - Use em: Sections que listam múltiplos items

5. **GlassPanel** — Glassmorphism leve
   - Use em: Destaques, citações, call-to-actions

### TIER 2 — Funcionalidades Especializadas
1. **AnimatedIntegrationCards** — Cards com floating animation
2. **GradientBorderCard** — Cards com bordas gradiente
3. **FloatingCTA** — CTA flutuante ao scroll
4. **AIWorkflowSection** — Workflow visual com passos
5. **SecurityHighlights** — Grid de segurança

### TIER 3 — Seções Completas
1. **ModernFAQ** — FAQ com accordion premium
2. **PremiumFooterExpansion** — Footer expandido
3. **EnterpriseBanner** — Banner destaque premium
4. **InfrastructureSection** — Seção arquitetura
5. **PremiumStatsSection** — Stats com números animados
6. **APIShowcase** — Showcase de API com examples

## EXEMPLO DE INTEGRAÇÃO — PÁGINA HOME

```jsx
"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { AppShell } from "../components/shell";
import {
  PremiumCanvas,
  FeatureGridPremium,
  EnterpriseCard,
  FloatingCTA,
  NeonDivider,
} from "../components/premium";

export default function HomePage() {
  return (
    <AppShell fullWidth={true}>
      <main className="relative min-h-[100dvh] bg-white">
        
        {/* HERO — Mantém existente, apenas adiciona Canvas */}
        <section className="relative z-10 flex min-h-[100dvh] flex-col items-center justify-center px-5 pt-20 pb-16">
          
          {/* Canvas ATRÁS do conteúdo */}
          <div className="fixed inset-0 pointer-events-none">
            <PremiumCanvas variant="grid" />
          </div>

          {/* Conteúdo existente continua igual... */}
          <div className="relative z-20 mx-auto w-full max-w-[1200px]">
            {/* Hero content */}
          </div>
        </section>

        {/* MÓDULOS — Expandir com FeatureGridPremium */}
        <section id="modules" className="relative z-10 py-24">
          <div className="mx-auto max-w-[1200px] px-5">
            <h2>Plataforma Modular</h2>
            
            {/* OPÇÃO A: Manter cards simples existentes */}
            {/* <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">... */}
            
            {/* OPÇÃO B: Expandir com componente premium (gradual) */}
            <FeatureGridPremium
              columns={3}
              features={[
                {
                  icon: ChatBubbleIcon,
                  title: "Chat Avançado",
                  description: "IA conversacional em tempo real",
                  badge: "Production Ready"
                },
                // ... mais features
              ]}
            />
          </div>
        </section>

        {/* NOVO: Adicionar seção com GlassPanel */}
        <section className="relative z-10 py-24">
          <div className="mx-auto max-w-[1200px] px-5">
            <NeonDivider />
            <GlassPanel
              title="Por que SyntexaBR"
              subtitle="Infraestrutura de IA enterprise"
            >
              <ul className="space-y-2">
                <li>✓ Modelo proprietário otimizado</li>
                <li>✓ Latência ultra-baixa</li>
                <li>✓ 99.9% uptime garantido</li>
              </ul>
            </GlassPanel>
          </div>
        </section>

        {/* FLOATING CTA — Adiciona automaticamente */}
        <FloatingCTA
          title="Pronto para começar?"
          subtitle="Acesse o console agora"
          primaryText="Acessar"
          primaryHref="/chat"
          secondaryText="Saiba Mais"
          secondaryHref="#about"
        />
      </main>
    </AppShell>
  );
}
```

## PASSO-A-PASSO DE INTEGRAÇÃO

### Fase 1: Fundação Visual
- [ ] Integrar PremiumCanvas no hero
- [ ] Testar em desktop/mobile
- [ ] Verificar FPS (deve estar 60+)

### Fase 2: Componentes Simples
- [ ] Expandir grids simples com FeatureGridPremium
- [ ] Adicionar GlassPanel em seções destacadas
- [ ] Testar responsive

### Fase 3: Interatividade
- [ ] Integrar FloatingCTA
- [ ] Adicionar AnimatedIntegrationCards
- [ ] Testar cliques e scroll

### Fase 4: Seções Completas
- [ ] Criar novo arquivo para /enterprise
- [ ] Usar EnterpriseBanner
- [ ] Integrar SecurityHighlights

### Fase 5: Novas Páginas
- [ ] /parcerias (use BentoGrid)
- [ ] /fale-conosco (use GlassPanel)
- [ ] /sobre (use AIWorkflowSection)
- [ ] /api (use APIShowcase)
- [ ] /docs (use ModernFAQ)

## BOAS PRÁTICAS

### ✅ FAÇA
- Teste cada integração
- Mantenha canvas ATRÁS do conteúdo
- Use `whileInView` para animations (economiza GPU)
- Importe apenas componentes que vai usar
- Respeite tamanhos de fonte existentes

### ❌ NÃO FAÇA
- Não refatore componentes existentes
- Não altere o hero principal
- Não use animations pesadas simultaneamente
- Não crie novos componentes TSX (use JS)
- Não mude o backend/APIs

## IMPORTS

```jsx
// Importar tudo
import * as Premium from "@/components/premium";

// Usar
<Premium.FeatureGridPremium ... />

// Ou importar seletivo
import { EnterpriseCard, GlassPanel } from "@/components/premium";
```

## PERFORMANCE CHECKLIST

- [ ] Lighthouse score > 90
- [ ] Sem memory leaks (DevTools)
- [ ] Sem hydration mismatch
- [ ] FPS consistent 60+ (sem jank)
- [ ] Mobile Safari OK
- [ ] Chat funciona normalmente
- [ ] STT/TTS funciona normalmente

## SUPORTE

Para cada componente, veja JSDoc no topo do arquivo para:
- Props disponíveis
- Valores padrão
- Exemplos de uso
- Padrões de design

Todos os componentes são agnósticos — funcionam com dados simples, sem dependências complexas.
