# 🎨 COMPONENTES PREMIUM — REFERÊNCIA

## Visão Geral

Todos os componentes aqui expandem o visual da SyntexaBR **sem quebrar o site existente**.

- ✅ Fully responsive (mobile-first)
- ✅ Framer Motion animations
- ✅ Tailwind CSS styling
- ✅ JavaScript (sem TSX)
- ✅ Zero breaking changes
- ✅ Production-ready

---

## 📚 Componentes

### Tier 1 — Base Visual

#### 1. **PremiumCanvas**
Grid animado leve com glow e partículas.

```jsx
import { PremiumCanvas } from "@/components/premium";

<div className="relative h-96">
  <PremiumCanvas variant="grid" />
</div>
```

**Props:**
- `variant`: "grid" | "connections" (default: "grid")
- `className`: string

**Uso:** Background em heróis, seções

---

#### 2. **FeatureGridPremium**
Grid de features com reveal on scroll.

```jsx
<FeatureGridPremium
  columns={3}
  features={[
    {
      icon: ChatIcon,
      title: "Chat",
      description: "Conversacional",
      badge: "Production"
    }
  ]}
/>
```

**Props:**
- `features`: array de `{ icon, title, description, badge }`
- `columns`: 2 | 3 | 4 (default: 3)
- `className`: string

**Uso:** Listar features, módulos

---

#### 3. **EnterpriseCard**
Card elegante com glow e animações.

```jsx
<EnterpriseCard
  icon={StarIcon}
  title="Enterprise"
  description="Solução dedicada"
  features={["SLA 99.9%", "Suporte 24/7"]}
  glowColor="emerald"
/>
```

**Props:**
- `icon`: React component
- `title`: string
- `description`: string
- `features`: string[]
- `glowColor`: "emerald" | "blue" | "slate"
- `variant`: "default" | "flat"
- `href`: optional link
- `className`: string

**Uso:** Cards em grids, módulos

---

#### 4. **BentoGrid**
Layout Apple-style com diferentes tamanhos.

```jsx
<BentoGrid
  items={[
    {
      icon: Icon1,
      title: "Item 1",
      description: "...",
      colSpan: 1,
      rowSpan: 1
    }
  ]}
/>
```

**Props:**
- `items`: array de `{ icon, title, description, footer, colSpan, rowSpan, className }`
- `className`: string

**Uso:** Layouts complexos, dashboards

---

#### 5. **GlassPanel**
Glassmorphism com bordas elegantes.

```jsx
<GlassPanel
  title="Título"
  subtitle="Subtítulo"
  icon={Icon}
  glowIntensity="medium"
>
  Conteúdo aqui
</GlassPanel>
```

**Props:**
- `title`: string
- `subtitle`: string
- `icon`: React component
- `glowIntensity`: "subtle" | "medium" | "prominent"
- `border`: boolean (default: true)
- `animated`: boolean (default: true)
- `className`: string

**Uso:** Destaques, call-to-actions, citações

---

### Tier 2 — Funcionalidades

#### 6. **AnimatedIntegrationCards**
Cards para integrações com floating animation.

```jsx
<AnimatedIntegrationCards
  integrations={[
    { title: "API", badge: "Ready" },
    { title: "Zapier", icon: ZapierIcon }
  ]}
/>
```

**Props:**
- `integrations`: array de `{ title, icon?, badge }`
- `className`: string

**Uso:** Listar integrações, partners

---

#### 7. **GradientBorderCard**
Card com bordas gradiente animadas.

```jsx
<GradientBorderCard
  title="Título"
  description="Descrição"
  icon={Icon}
  gradientFrom="emerald"
>
  Conteúdo
</GradientBorderCard>
```

**Props:**
- `title`: string
- `description`: string
- `icon`: React component
- `gradientFrom`: "emerald" | "blue" | "purple"
- `children`: ReactNode
- `className`: string

**Uso:** Destaques, CTAs

---

#### 8. **FloatingCTA**
CTA que aparece ao scroll, flutuante.

```jsx
<FloatingCTA
  title="Experimente?"
  subtitle="Acesso imediato"
  primaryText="Acessar"
  primaryHref="/chat"
  secondaryText="Saiba Mais"
  secondaryHref="#about"
/>
```

**Props:**
- `title`: string
- `subtitle`: string
- `primaryText`: string
- `primaryHref`: string | `onPrimaryClick`
- `secondaryText`: string
- `secondaryHref`: string | `onSecondaryClick`
- `className`: string

**Uso:** Engajamento global

---

#### 9. **AIWorkflowSection**
Workflow visual com passos numerados.

```jsx
<AIWorkflowSection
  title="Como Funciona"
  description="Processo em 4 passos"
  steps={[
    {
      title: "Passo 1",
      description: "...",
      details: ["Detalhe 1", "Detalhe 2"]
    }
  ]}
/>
```

**Props:**
- `title`: string
- `description`: string
- `steps`: array de `{ title, description, details }`
- `className`: string

**Uso:** Tutoriais, processos

---

#### 10. **SecurityHighlights**
Grid de highlights de segurança.

```jsx
<SecurityHighlights
  title="Segurança"
  highlights={[
    { icon: Icon, title: "LGPD", description: "...", badge: "Certified" }
  ]}
/>
```

**Props:**
- `title`: string
- `description`: string
- `highlights`: array de `{ icon, title, description, badge }`
- `className`: string

**Uso:** Segurança, compliance

---

### Tier 3 — Seções Completas

#### 11. **ModernFAQ**
FAQ com accordion premium.

```jsx
<ModernFAQ
  title="Perguntas Frequentes"
  description="Respostas rápidas"
  faqs={[
    { question: "P?", answer: "R?" }
  ]}
/>
```

**Props:**
- `title`: string
- `description`: string
- `faqs`: array de `{ question, answer }`
- `className`: string

**Uso:** FAQ, documentação

---

#### 12. **PremiumFooterExpansion**
Footer expandido com newsletter.

```jsx
<PremiumFooterExpansion
  newsletter={true}
  sections={[
    { title: "Produto", links: [...] }
  ]}
/>
```

**Props:**
- `newsletter`: boolean
- `sections`: array de `{ title, links: [{ label, href }] }`
- `className`: string

**Uso:** Footer

---

#### 13. **EnterpriseBanner**
Banner destaque premium.

```jsx
<EnterpriseBanner
  title="Enterprise?"
  subtitle="Infraestrutura dedicada"
  icon={Icon}
  ctaText="Fale Conosco"
  ctaHref="/contact"
/>
```

**Props:**
- `title`: string
- `subtitle`: string
- `icon`: React component
- `ctaText`: string
- `ctaHref`: string
- `secondaryCtaText`: string
- `secondaryCtaHref`: string
- `glowColor`: "emerald" | "blue"
- `className`: string

**Uso:** Destaques, cross-sell

---

#### 14. **InfrastructureSection**
Seção visual de arquitetura.

```jsx
<InfrastructureSection
  title="Arquitetura"
  description="Nossa stack"
  layers={[
    { icon: Icon, title: "Frontend", components: ["React", "Next.js"] }
  ]}
/>
```

**Props:**
- `title`: string
- `description`: string
- `layers`: array de `{ icon, title, description, components }`
- `className`: string

**Uso:** Tech specs, documentação

---

#### 15. **PremiumStatsSection**
Stats com números animados.

```jsx
<PremiumStatsSection
  title="Por Números"
  stats={[
    { value: "99.9%", label: "Uptime", description: "SLA" }
  ]}
/>
```

**Props:**
- `title`: string
- `description`: string
- `stats`: array de `{ value, label, description }`
- `className`: string

**Uso:** Estatísticas, KPIs

---

#### 16. **APIShowcase**
Showcase de API com exemplos interativos.

```jsx
<APIShowcase
  title="API Documentation"
  description="Endpoints disponíveis"
  endpoints={[
    {
      method: "GET",
      name: "/api/chat",
      description: "...",
      example: "fetch('/api/chat')"
    }
  ]}
/>
```

**Props:**
- `title`: string
- `description`: string
- `endpoints`: array de `{ method, name, description, example }`
- `className`: string

**Uso:** API docs, integração

---

## 🎨 Variáveis Globais

Todos os componentes usam:

```css
/* Cores */
--color-primary: #059669 (verde)
--color-text-dark: #0f172a (preto)
--color-text-light: #64748b (cinza)
--color-border: rgba(15,23,42,0.06)

/* Spacing */
--spacing-base: 16px
--padding-section: 24px (py-24)

/* Typography */
--font-size-base: 16px
--line-height-relaxed: 1.625

/* Animations */
--transition-duration: 300ms
--ease-out: cubic-bezier(0.4, 0, 0.2, 1)
```

---

## 📋 Padrões de Uso

### Pattern 1: Grid de Features
```jsx
<FeatureGridPremium
  columns={3}
  features={[
    { icon: Icon1, title: "A", description: "..." },
    { icon: Icon2, title: "B", description: "..." }
  ]}
/>
```

### Pattern 2: Seção Completa
```jsx
<section className="py-24">
  <NeonDivider />
  <h2>Título</h2>
  <EnterpriseCard ... />
</section>
```

### Pattern 3: Com Canvas
```jsx
<div className="relative">
  <PremiumCanvas variant="grid" className="opacity-40" />
  <div className="relative z-10">Conteúdo</div>
</div>
```

### Pattern 4: Animação Global
```jsx
<FloatingCTA title="..." />
{/* Aparece automaticamente ao scroll */}
```

---

## ✅ Checklist de Integração

- [ ] Import do componente
- [ ] Props preenchidas corretamente
- [ ] Testado em desktop
- [ ] Testado em mobile
- [ ] Testado em Safari
- [ ] Sem console errors
- [ ] Performance OK (Lighthouse)
- [ ] Responsividade preservada

---

## 🆘 Troubleshooting

| Problema | Solução |
|----------|---------|
| Canvas lagado | Reduza `opacity`, use `variant="grid"` |
| Animações rápidas | Aumente `transition.duration` |
| Mobile quebrado | Teste em Safari, use `whileInView` |
| Memory leak | Verifique DevTools, cleanup em useEffect |
| Componente não renderiza | Verifique imports, props |

---

## 📞 Recursos

- JSDoc em cada arquivo (veja o topo)
- Exemplo em `app/parcerias/page.js`
- Guias em `PREMIUM_INTEGRATION_*.md`
- DevTools para debug

---

**Pronto para usar! Divirta-se expandindo o visual.** ✨
