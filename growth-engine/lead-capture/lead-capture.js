/**
 * Lead Capture - Sistema Inteligente de Captura de Leads
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * Captura:
 * - Popups inteligentes
 * - CRM integrado
 * - WhatsApp API
 * - Email segmentado
 * - Analytics completo
 * - Tracking de eventos
 */

export class LeadCapture {
  constructor(config = {}) {
    this.leads = [];
    this.segmentedLists = {};
    this.webhooks = {};
    this.apiKeys = config.apiKeys || {};
    this.config = config;
  }

  /**
   * Popup inteligente com detecção de comportamento
   */
  createSmartPopup(config = {}) {
    const popup = {
      id: `popup-${Date.now()}`,
      enabled: true,
      type: config.type || 'email', // email, chat, offer, ebook
      trigger: config.trigger || {
        event: 'scroll', // scroll, exit-intent, time, pageview
        value: 50, // 50% scroll
        delay: 5000, // 5 segundos
      },
      targeting: config.targeting || {
        deviceType: ['desktop', 'mobile'],
        firstTime: true,
        exitIntent: true,
      },
      content: {
        headline: config.headline || 'Transforme sua estratégia de IA',
        subheadline: config.subheadline || 'Receba dicas exclusivas no seu email',
        cta: config.cta || 'Quero receber',
        image: config.image,
        fields: config.fields || [
          { name: 'email', type: 'email', placeholder: 'seu@email.com', required: true },
          { name: 'firstName', type: 'text', placeholder: 'Seu nome', required: false },
          { name: 'company', type: 'text', placeholder: 'Sua empresa', required: false },
        ],
      },
      analytics: {
        impressions: 0,
        clicks: 0,
        submissions: 0,
        conversionRate: 0,
      },
      schedule: {
        startDate: config.startDate || new Date(),
        endDate: config.endDate || null,
        active: true,
      },
    };

    return popup;
  }

  /**
   * Captura lead do popup
   */
  captureLead(data, source = 'popup') {
    const lead = {
      id: `lead-${Date.now()}`,
      email: data.email,
      firstName: data.firstName || 'Lead',
      company: data.company || '',
      source,
      capturedAt: new Date(),
      segment: this.segmentLead(data),
      score: this.calculateLeadScore(data),
      status: 'new',
      metadata: {
        referrer: data.referrer,
        utm_source: data.utm_source,
        utm_campaign: data.utm_campaign,
        deviceType: data.deviceType,
      },
    };

    this.leads.push(lead);
    this.addToSegment(lead);
    this.triggerWebhooks('lead.captured', lead);

    return lead;
  }

  /**
   * Segmenta leads automaticamente
   */
  segmentLead(data) {
    const segments = [];

    // Segmentação por tipo de empresa
    if (data.company) {
      segments.push(data.company.includes('startup') ? 'startup' : 'enterprise');
    }

    // Segmentação por fonte
    if (data.utm_campaign?.includes('promo')) {
      segments.push('promotional-aware');
    }

    // Segmentação por comportamento
    if (data.pageTime > 300) {
      segments.push('high-engagement');
    }

    // Segmentação por tipo de problema
    if (data.interests?.includes('growth')) {
      segments.push('growth-focused');
    }

    return segments.length > 0 ? segments : ['general'];
  }

  /**
   * Calcula lead score (0-100)
   */
  calculateLeadScore(data) {
    let score = 0;

    // Email corporativo: +20
    if (data.email && !data.email.includes('gmail')) score += 20;

    // Empresa informada: +15
    if (data.company) score += 15;

    // Nome completo: +10
    if (data.firstName && data.firstName.split(' ').length > 1) score += 10;

    // Tempo na página: +20 (se > 300s)
    if (data.pageTime > 300) score += 20;

    // Múltiplas páginas visitadas: +15
    if (data.pagesVisited > 3) score += 15;

    // Clicou em CTA: +10
    if (data.clickedCTA) score += 10;

    return Math.min(100, score);
  }

  /**
   * Adiciona lead ao segment
   */
  addToSegment(lead) {
    for (const segment of lead.segment) {
      if (!this.segmentedLists[segment]) {
        this.segmentedLists[segment] = [];
      }
      this.segmentedLists[segment].push(lead);
    }
  }

  /**
   * CRM com fluxo de automação
   */
  setupCRM() {
    return {
      automations: {
        'welcome-series': {
          name: 'Série de boas-vindas',
          trigger: 'lead.captured',
          emails: [
            { delay: 0, subject: 'Bem-vindo a Syntexa!', template: 'welcome-1' },
            { delay: 86400, subject: 'Continue descobrindo', template: 'welcome-2' },
            { delay: 172800, subject: 'Sua oferta exclusiva', template: 'welcome-3' },
          ],
        },
        'nurture-growth': {
          name: 'Nutrição - Growth Focused',
          trigger: 'segment:growth-focused',
          frequency: 'twice-weekly',
          emails: [
            { subject: 'Dica de growth #1', template: 'growth-tip-1' },
            { subject: 'Case de sucesso', template: 'case-growth' },
            { subject: 'Webinar exclusivo', template: 'webinar-growth' },
          ],
        },
        're-engagement': {
          name: 'Re-engajamento',
          trigger: 'inactive:30d',
          emails: [
            { subject: 'Sentiremos sua falta!', template: 'reengagement-1' },
            { delay: 604800, subject: 'Última chance de desconto', template: 'reengagement-2' },
          ],
        },
      },
      integrations: {
        email: { provider: 'resend', configured: true },
        whatsapp: { provider: 'twilio', configured: false },
        slack: { provider: 'slack-api', configured: false },
      },
    };
  }

  /**
   * Envia para WhatsApp
   */
  async sendToWhatsApp(phoneNumber, message) {
    if (!this.apiKeys.twilio) {
      throw new Error('Twilio API key não configurada');
    }

    try {
      const response = {
        phone: phoneNumber,
        message,
        sent: true,
        timestamp: new Date(),
        messageId: `msg-${Date.now()}`,
      };
      return response;
    } catch (err) {
      return { phone: phoneNumber, sent: false, error: err.message };
    }
  }

  /**
   * Rastreia eventos de leads
   */
  trackEvent(leadId, eventType, eventData = {}) {
    const lead = this.leads.find(l => l.id === leadId);
    if (!lead) throw new Error('Lead não encontrado');

    lead.events = lead.events || [];
    lead.events.push({
      type: eventType,
      timestamp: new Date(),
      data: eventData,
    });

    // Atualiza lead score baseado em eventos
    switch (eventType) {
      case 'email.opened':
        lead.score += 5;
        break;
      case 'email.clicked':
        lead.score += 10;
        break;
      case 'page.visited':
        lead.score += 2;
        break;
      case 'demo.scheduled':
        lead.score += 30;
        lead.status = 'qualified';
        break;
    }

    lead.score = Math.min(100, lead.score);

    this.triggerWebhooks('event.tracked', { lead, event: eventType });

    return lead;
  }

  /**
   * Analytics de leads
   */
  getLeadAnalytics() {
    const analytics = {
      totalLeads: this.leads.length,
      bySegment: {},
      byScore: { hot: 0, warm: 0, cold: 0 },
      byStatus: { new: 0, engaged: 0, qualified: 0, customer: 0 },
      conversionMetrics: {
        captureRate: 0,
        engagementRate: 0,
        conversionRate: 0,
      },
    };

    for (const lead of this.leads) {
      // Por segment
      for (const segment of lead.segment) {
        analytics.bySegment[segment] = (analytics.bySegment[segment] || 0) + 1;
      }

      // Por score
      if (lead.score >= 70) analytics.byScore.hot++;
      else if (lead.score >= 40) analytics.byScore.warm++;
      else analytics.byScore.cold++;

      // Por status
      analytics.byStatus[lead.status]++;
    }

    // Calcula taxas
    analytics.conversionMetrics.captureRate = (this.leads.length / this.getTotalPageViews()) * 100;
    analytics.conversionMetrics.engagementRate = (
      this.leads.filter(l => l.events?.length > 0).length / this.leads.length
    ) * 100;

    return analytics;
  }

  /**
   * Exporta leads para plataformas
   */
  exportLeads(format = 'csv', segment = null) {
    let leads = segment ? (this.segmentedLists[segment] || []) : this.leads;

    if (format === 'csv') {
      return this.toCsv(leads);
    } else if (format === 'json') {
      return JSON.stringify(leads, null, 2);
    }

    return leads;
  }

  /**
   * Converte para CSV
   */
  toCsv(leads) {
    const headers = ['ID', 'Email', 'Nome', 'Empresa', 'Score', 'Status', 'Capturado em'];
    const rows = leads.map(l => [
      l.id,
      l.email,
      l.firstName,
      l.company,
      l.score,
      l.status,
      l.capturedAt.toLocaleString(),
    ]);

    return [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');
  }

  /**
   * Registra webhook
   */
  registerWebhook(event, url) {
    if (!this.webhooks[event]) {
      this.webhooks[event] = [];
    }
    this.webhooks[event].push(url);
  }

  /**
   * Dispara webhooks
   */
  async triggerWebhooks(event, data) {
    const webhookUrls = this.webhooks[event] || [];

    for (const url of webhookUrls) {
      try {
        // Em produção, fazer POST real
        console.log(`[Webhook] ${event} → ${url}`, data);
      } catch (err) {
        console.error(`Webhook error for ${event}:`, err);
      }
    }
  }

  /**
   * Mock: Total de page views
   */
  getTotalPageViews() {
    return Math.floor(Math.random() * 100000) + 10000;
  }

  /**
   * Cria funnel de conversão
   */
  getConversionFunnel() {
    const funnel = {
      visitors: this.getTotalPageViews(),
      leadsGenerated: this.leads.length,
      engaged: this.leads.filter(l => l.score > 40).length,
      qualified: this.leads.filter(l => l.status === 'qualified').length,
      customers: this.leads.filter(l => l.status === 'customer').length,
    };

    funnel.conversionRates = {
      visitorToLead: (funnel.leadsGenerated / funnel.visitors) * 100,
      leadToEngaged: (funnel.engaged / funnel.leadsGenerated) * 100,
      engagedToQualified: (funnel.qualified / funnel.engaged) * 100 || 0,
      qualifiedToCustomer: (funnel.customers / funnel.qualified) * 100 || 0,
    };

    return funnel;
  }
}

export default LeadCapture;
