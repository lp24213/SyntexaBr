# 📝 EXEMPLO DE INTEGRAÇÃO PRÁTICA — page.js

## LOCALIZAÇÃO
`frontend/app/page.js`

## ESTRATÉGIA
Este arquivo mostra como expandir GRADUALMENTE a página home com componentes premium,
mantendo 100% do que existe atualmente.

## INTEGRAÇÃO PASSO-A-PASSO

### PASSO 1: Adicionar Imports (NO TOPO do arquivo)

```jsx
// Existing imports...
import Link from "next/link";
import { motion } from "framer-motion";
import React from "react";
import { AppShell } from "../components/shell";
import { InfrastructureVisual } from "../components/infrastructure-visual";
import { DownloadSection } from "../components/download-section";
import { t } from "../lib/i18n";
import { useLanguage } from "../components/language-provider";
import { encryptedPath } from "../lib/routes";

// ✨ NOVO: Imports Premium (adicione isto)
import {
  PremiumCanvas,
  NeonDivider,
  FeatureGridPremium,
  GlassPanel,
  FloatingCTA,
  AnimatedIntegrationCards,
} from "../components/premium";
```

### PASSO 2: Integração no Hero (SEM quebrar o existente)

**ANTES:**
```jsx
{/* Background infrastructure grid */}
<div className="fixed inset-0 z-0 pointer-events-none">
  <div className="absolute inset-0 infrastructure-grid opacity-60" />
  <div className="hero-fog-a pointer-events-none absolute inset-0" />
</div>

{/* Hero Section — Clean Premium */}
<section className="relative z-10 flex min-h-[100dvh] flex-col items-center justify-center px-5 pt-20 pb-16">
```

**DEPOIS:**
```jsx
{/* Background infrastructure grid */}
<div className="fixed inset-0 z-0 pointer-events-none">
  <div className="absolute inset-0 infrastructure-grid opacity-60" />
  <div className="hero-fog-a pointer-events-none absolute inset-0" />
  {/* ✨ NOVO: Canvas premium overlay (muito leve) */}
  <PremiumCanvas variant="grid" className="opacity-40" />
</div>

{/* Hero Section — Clean Premium */}
<section className="relative z-10 flex min-h-[100dvh] flex-col items-center justify-center px-5 pt-20 pb-16">
```

**RESULTADO:**
- ✅ Visual mais premium com grid animado
- ✅ Hero mantém 100% do layout existente
- ✅ Canvas é apenas decorativo, atrás do texto

### PASSO 3: Expandir Modules com NeonDivider (Opcional)

Adicione ANTES da seção Platform Modules:

```jsx
{/* Platform Modules */}
<section id="infraestrutura" className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-24">
  {/* ✨ NOVO: Divisor elegante */}
  <NeonDivider variant="medium" />

  <motion.div
    initial={{ opacity: 0, y: 40 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.7 }}
  >
    {/* Resto do conteúdo... */}
  </motion.div>
```

### PASSO 4: Adicionar FloatingCTA (Automático)

Adicione NO FINAL da seção `<main>`, antes de fechar:

```jsx
      {/* ✨ NOVO: FloatingCTA aparece ao scroll */}
      <FloatingCTA
        title="Experimente Agora"
        subtitle="Acesse a plataforma SyntexaBR"
        primaryText="Acessar Console"
        primaryHref={encryptedPath("/chat")}
        secondaryText="Ver Documentação"
        secondaryHref="#infraestrutura"
      />
    </main>
  </AppShell>
);
```

**RESULTADO:**
- ✅ CTA flutuante aparece ao scroll
- ✅ Não interfere com conteúdo existente
- ✅ Completamente agnóstico

### PASSO 5: Expandir Future Sections (Opcional)

Você pode adicionar novas seções após `<DownloadSection />`:

```jsx
{/* WhatsApp Business Section */}
{/* ... existing code ... */}

{/* ✨ NOVO: Seção Enterprise (opcional) */}
<section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-24">
  <NeonDivider />
  
  <GlassPanel
    title="Plataforma Enterprise"
    subtitle="Infraestrutura dedicada para seu negócio"
  >
    <div className="grid grid-cols-2 gap-4 text-sm">
      <div>✓ SLA 99.9% uptime</div>
      <div>✓ Suporte 24/7</div>
      <div>✓ Modelo customizado</div>
      <div>✓ Integração API</div>
    </div>
  </GlassPanel>
</section>

{/* ✨ NOVO: Integrações (opcional) */}
<section className="relative z-10 mx-auto w-full max-w-[1200px] px-5 py-24">
  <h2 className="text-2xl font-medium mb-8">Integrações Suportadas</h2>
  
  <AnimatedIntegrationCards
    integrations={[
      { title: "Zapier", icon: ZapierIcon, badge: "Conectado" },
      { title: "n8n", icon: n8nIcon, badge: "Beta" },
      { title: "Make", icon: MakeIcon, badge: "Coming Soon" },
      // ...
    ]}
  />
</section>
```

## TESTE CHECKLIST

Após cada mudança, teste:

- [ ] Hero ainda carrega normalmente
- [ ] Canvas não causa lag (DevTools > Performance)
- [ ] FloatingCTA aparece ao scroll
- [ ] Responsividade em mobile/tablet
- [ ] Chat ainda funciona (clique no botão)
- [ ] Sem mensagens de erro console
- [ ] Lighthouse ainda > 90

## COMMIT EXEMPLO

```
git add frontend/app/page.js
git commit -m "feat: Adiciona PremiumCanvas e FloatingCTA ao home

- Integra canvas leve para visual premium
- Adiciona FloatingCTA para engagement
- Mantém 100% do layout existente
- Testado em mobile/desktop/Safari
"
```

## ROLLBACK SIMPLES

Se algo quebrar, remova os imports premium:

```jsx
// Remova isto:
import {
  PremiumCanvas,
  // ...
} from "../components/premium";

// Remova as linhas:
<PremiumCanvas variant="grid" className="opacity-40" />
<FloatingCTA ... />
<NeonDivider />
```

A página volta ao normal instant.

## PRÓXIMAS FASES (SEM PRESSA)

Depois de testar integração básica:

1. Expandir modules com `FeatureGridPremium` (opcional)
2. Criar nova seção "Enterprise" com `EnterpriseBanner`
3. Criar seção "Como Funciona" com `AIWorkflowSection`
4. Expandir footer com `PremiumFooterExpansion`
5. Criar novas páginas `/parcerias`, `/fale-conosco`, etc

## DOCUMENTAÇÃO

Cada componente tem JSDoc com:
- Props
- Valores padrão
- Exemplos
- Padrões de design

Veja no topo de cada arquivo em `components/premium/`
