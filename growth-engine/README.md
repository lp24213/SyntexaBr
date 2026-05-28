# Syntexa Growth Engine - Documentação Completa

## 🚀 Visão Geral

O **Syntexa Growth Engine** é um sistema integrado de growth hacking e automação de marketing que transforma a plataforma em uma **máquina de aquisição orgânica massiva**.

## 📊 Módulos

### 1. **SEO Engine** (`seo-engine/`)
Geração programática de páginas otimizadas para SEO.

#### Funcionalidades:
- ✅ Meta tags automáticas (55-60 caracteres)
- ✅ Schema.org JSON-LD (Article, Product, LocalBusiness, FAQ)
- ✅ OpenGraph e Twitter Card
- ✅ Sitemap XML dinâmico
- ✅ RSS Feed automático
- ✅ Canonical tags
- ✅ Interlinkagem inteligente
- ✅ Breadcrumb estruturado

#### Uso:
```javascript
import SEOEngine from './seo-engine/seo-generator.js';

const seo = new SEOEngine({ domain: 'https://syntexabr.com.br' });

// Gerar metadata
const metadata = seo.generateMetaTags({
  title: 'Transforme sua empresa com IA',
  description: 'Solução completa de IA para automação',
  keywords: ['IA', 'automação', 'empresa'],
  url: 'https://syntexabr.com.br/solucoes/ia',
});

// Gerar schema
const schema = seo.generateSchemaJson('Product', {
  title: 'Syntexa AI Pro',
  description: 'Plataforma de IA avançada',
  price: 99.99,
});
```

### 2. **Content Generator** (`content-generator/`)
Gerador massivo de conteúdo automático.

#### Funcionalidades:
- ✅ 50+ artigos por mês
- ✅ Landing pages customizadas
- ✅ Páginas comparativas (vs competitors)
- ✅ Páginas por keywords
- ✅ FAQ estruturado
- ✅ Multilíngue (PT-BR, EN, ES)
- ✅ Export em Markdown/HTML/JSON

#### Uso:
```javascript
import ContentGenerator from './content-generator/content-generator.js';

const generator = new ContentGenerator();

// Gerar artigo
const article = await generator.generateNicheArticle(
  'Growth Hacking',
  'como crescer startup',
  'pt-BR'
);

// Gerar lote (50 artigos)
const batch = await generator.generateArticleBatch(
  ['IA', 'Automação', 'Growth'],
  ['eficiência', 'conversão', 'escala'],
  50
);

// Exportar para Markdown
const markdown = generator.exportContent(article, 'markdown');
```

### 3. **Marketing Automation** (`marketing-automation/`)
Sistema de marketing automático multi-plataforma.

#### Funcionalidades:
- ✅ Auto-post em LinkedIn, Twitter, Reddit, Instagram, Medium
- ✅ Email automático segmentado
- ✅ WhatsApp API
- ✅ Calendário de conteúdo trimestral
- ✅ Templates virais por plataforma
- ✅ Análise de performance
- ✅ Hashtags automáticas

#### Plataformas Suportadas:
- 🔵 LinkedIn (Thought leadership, Case studies, Controversies)
- 🐦 Twitter (Tips, Threads, Virais)
- 📱 Reddit (Community posts, AMAs)
- 📸 Instagram (Visual content)
- 📧 Email (Newsletter, Promo)
- 💬 WhatsApp (Promo, Educational)
- 📰 Medium (Long-form content)

#### Uso:
```javascript
import MarketingAutomation from './marketing-automation/marketing-automation.js';

const marketing = new MarketingAutomation({
  socialAccounts: {
    linkedin: 'YOUR_LINKEDIN_TOKEN',
    twitter: 'YOUR_TWITTER_TOKEN',
  }
});

// Gerar post viral
const post = marketing.generateViralPost('IA e educação', 'linkedin');

// Auto-post em múltiplas plataformas
const result = await marketing.autoPostContent({
  content: post.variants[0],
  platforms: ['linkedin', 'twitter', 'reddit'],
});

// Calendário trimestral
const calendar = marketing.generateMarketingCalendar(
  new Date(),
  new Date(Date.now() + 90*86400000),
  { platforms: ['linkedin', 'twitter', 'email'] }
);
```

### 4. **Lead Capture** (`lead-capture/`)
Sistema inteligente de captura de leads.

#### Funcionalidades:
- ✅ 3 tipos de popups inteligentes
- ✅ Detecção de intent (scroll, exit-intent, time)
- ✅ Lead scoring automático (0-100)
- ✅ Segmentação automática
- ✅ CRM com automações de email
- ✅ WhatsApp integration
- ✅ Event tracking completo
- ✅ Funnel de conversão
- ✅ Export CSV/JSON

#### Popup Types:
1. **Email Capture** - Scroll trigger (50%)
2. **Ebook Offer** - Exit intent
3. **Discount Popup** - Time-based (30s)

#### Automações de Email:
- Welcome series (3 emails)
- Nurture automático por segment
- Re-engajamento após 30 dias

#### Uso:
```javascript
import LeadCapture from './lead-capture/lead-capture.js';

const capture = new LeadCapture();

// Criar popup
const popup = capture.createSmartPopup({
  type: 'email',
  headline: 'Transforme sua IA',
  trigger: { event: 'scroll', value: 50 },
});

// Capturar lead
const lead = capture.captureLead({
  email: 'user@company.com',
  firstName: 'João',
  company: 'Tech Startup',
  referrer: document.referrer,
}, 'popup');

// Analytics
const analytics = capture.getLeadAnalytics();
const funnel = capture.getConversionFunnel();

// Exportar leads
const csv = capture.exportLeads('csv', 'growth-focused');
```

## 🎯 Growth Engine Principal

### Inicialização:
```javascript
import GrowthEngine from './growth-engine/index.js';

const engine = new GrowthEngine({
  seo: { domain: 'https://syntexabr.com.br' },
  marketing: { platforms: ['linkedin', 'twitter', 'email'] },
  leads: { apiKeys: { twilio: 'YOUR_KEY' } }
});

await engine.initialize();

// Dashboard
const dashboard = engine.getDashboard();
console.log(dashboard);
```

### Status Esperado após inicialização:
```json
{
  "status": "active",
  "initialized": true,
  "modules": {
    "seo": { "status": "active", "tasks": 6 },
    "content": { "status": "active", "tasks": 1 },
    "marketing": { "status": "active", "tasks": 5 },
    "leads": { "status": "active", "tasks": 1 }
  },
  "nextActions": [
    "Conectar IA para gerar conteúdo real",
    "Configurar API keys das plataformas",
    "Implementar webhooks de eventos",
    "Monitorar métricas em tempo real"
  ]
}
```

## 📈 Métricas de Crescimento

### Primeiras 30 dias:
- 📊 50+ artigos indexados no Google
- 📢 300+ posts em redes sociais
- 🎯 500-1000 leads capturados
- 💰 5-10% taxa de conversão esperada

### 90 dias:
- 📊 200+ páginas indexadas
- 📢 1000+ posts publicados
- 🎯 3000-5000 leads
- 💰 500-1000 clientes

### 1 ano:
- 📊 1000+ páginas em ranking
- 📢 10000+ posts/publications
- 🎯 50000+ leads acumulados
- 💰 10000+ clientes ativos

## 🔌 Integrações Necessárias

### Plataformas de Social Media:
```env
LINKEDIN_API_KEY=xxx
TWITTER_API_KEY=xxx
TWITTER_API_SECRET=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
INSTAGRAM_TOKEN=xxx
```

### Email & SMS:
```env
RESEND_API_KEY=xxx
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE=xxx
```

### Analytics:
```env
GOOGLE_ANALYTICS_KEY=xxx
SEGMENT_WRITE_KEY=xxx
```

## 📝 Checklist de Setup

- [ ] Instalar dependências do Growth Engine
- [ ] Configurar variáveis de ambiente (.env)
- [ ] Conectar IA para geração de conteúdo real
- [ ] Validar API keys de todas as plataformas
- [ ] Criar primeiros 10 artigos manualmente como seed
- [ ] Testar popups de captura em staging
- [ ] Configurar webhooks para eventos
- [ ] Setup analytics e tracking
- [ ] Treinar equipe no uso do sistema
- [ ] Monitorar primeiros resultados
- [ ] Ajustar templates baseado em performance

## 🎓 Próximos Passos

1. **Conectar IA Real**: Integrar com a IA Syntexa para gerar conteúdo real
2. **Viral Tools**: Criar ferramentas gratuitas que capturam leads
3. **Affiliate System**: Implementar sistema de afiliados com tracking
4. **CRM Avançado**: Integrar com HubSpot/Pipedrive
5. **Analytics Dashboard**: Dashboard em tempo real
6. **A/B Testing**: Sistema automático de testes
7. **Internacionalization**: Suporte completo multilíngue

## 📊 Estrutura de Dados

### Lead Object:
```javascript
{
  id: 'lead-1234567890',
  email: 'user@company.com',
  firstName: 'João',
  company: 'Tech Startup',
  source: 'popup',
  capturedAt: Date,
  segment: ['startup', 'growth-focused'],
  score: 75,
  status: 'qualified',
  events: [
    { type: 'email.opened', timestamp: Date },
    { type: 'page.visited', timestamp: Date }
  ]
}
```

### Article Object:
```javascript
{
  title: 'Como crescer startup em 2024',
  slug: 'como-crescer-startup-2024',
  language: 'pt-BR',
  niche: 'Growth Hacking',
  keyword: 'crescimento startup',
  sections: [
    { title: 'Introdução', content: '...', wordCount: 350 }
  ],
  metadata: {
    seoKeywords: ['crescimento', 'startup', '2024'],
    readingTime: 8,
    difficulty: 'beginner'
  }
}
```

## 🚀 Comandos Úteis

```bash
# Gerar 50 artigos de SEO
node scripts/generate-content.js --count 50

# Publicar em todas as redes
node scripts/auto-post.js --platforms all

# Análise de métricas
node scripts/analytics.js --report weekly

# Export de leads
node scripts/export-leads.js --format csv --segment growth-focused
```

## ⚠️ Notas Importantes

1. **Segurança**: Todos os API keys devem estar em variáveis de ambiente
2. **Rate Limiting**: Respeitar limites das plataformas (LinkedIn, Twitter, etc)
3. **Qualidade**: Conteúdo gerado deve ser revisado antes de publicação
4. **LGPD**: Conformidade com lei de proteção de dados
5. **Experiência**: Não quebrar nada do sistema existente

---

**Última atualização**: 2026-05-27
**Status**: 🟢 Ativo e em crescimento
**Responsável**: Growth Team Syntexa
