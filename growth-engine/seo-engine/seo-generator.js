/**
 * SEO Engine - Gerador Programático de Páginas Otimizadas
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * Gera páginas automaticamente com:
 * - Meta tags otimizadas
 * - Schema.org (JSON-LD)
 * - OpenGraph
 * - Sitemap dinâmico
 * - Canonical tags
 * - Interlinkagem automática
 * - FAQ estruturado
 */

export class SEOEngine {
  constructor(config = {}) {
    this.domain = config.domain || 'https://syntexabr.com.br';
    this.defaultLocale = config.locale || 'pt-BR';
    this.socialHandles = config.social || {};
    this.author = config.author || 'Syntexa AI';
  }

  /**
   * Gera meta tags completas para uma página
   */
  generateMetaTags(metadata) {
    const {
      title,
      description,
      keywords = [],
      image,
      url,
      type = 'website',
      author = this.author,
      publishedDate,
      modifiedDate,
      locale = this.defaultLocale,
    } = metadata;

    return {
      // Meta básicas
      title: this.optimizeTitle(title),
      description: this.optimizeDescription(description),
      keywords: keywords.join(', '),
      author,
      locale,
      charset: 'UTF-8',
      viewport: 'width=device-width, initial-scale=1.0',
      
      // Preload/prefetch
      'preload': [
        { rel: 'preload', as: 'font', href: '/fonts/system-ui.woff2', crossOrigin: 'anonymous' },
      ],

      // OpenGraph
      og: {
        'og:title': title,
        'og:description': description,
        'og:image': image || `${this.domain}/og-image.png`,
        'og:url': url || this.domain,
        'og:type': type,
        'og:site_name': 'Syntexa AI',
        'og:locale': locale,
      },

      // Twitter Card
      twitter: {
        'twitter:card': 'summary_large_image',
        'twitter:title': title,
        'twitter:description': description,
        'twitter:image': image || `${this.domain}/og-image.png`,
        'twitter:site': this.socialHandles.twitter || '@syntexabr',
      },

      // Timestamps
      ...(publishedDate && { 'article:published_time': publishedDate }),
      ...(modifiedDate && { 'article:modified_time': modifiedDate }),

      // Links relacionados
      canonical: url || this.domain,
      alternate: [
        { hreflang: 'pt-BR', href: url },
        { hreflang: 'en', href: url?.replace('pt-BR', 'en') },
      ],
    };
  }

  /**
   * Gera Schema.org JSON-LD
   */
  generateSchemaJson(type, data) {
    const baseSchema = {
      '@context': 'https://schema.org',
      '@type': type,
      'name': data.title,
      'description': data.description,
      'url': data.url || this.domain,
      'image': data.image,
      'author': {
        '@type': 'Organization',
        'name': this.author,
        'url': this.domain,
        'logo': `${this.domain}/logo.png`,
      },
      'publisher': {
        '@type': 'Organization',
        'name': 'Syntexa',
        'url': this.domain,
      },
    };

    // Schemas específicas por tipo
    switch (type) {
      case 'Article':
        return {
          ...baseSchema,
          'datePublished': data.publishedDate,
          'dateModified': data.modifiedDate || data.publishedDate,
          'articleBody': data.content,
          'keywords': data.keywords?.join(', '),
          'articleSection': data.category,
        };

      case 'Product':
        return {
          ...baseSchema,
          'sku': data.sku,
          'brand': {
            '@type': 'Brand',
            'name': 'Syntexa',
          },
          'offers': {
            '@type': 'Offer',
            'url': data.url,
            'priceCurrency': 'BRL',
            'price': data.price,
            'availability': 'https://schema.org/InStock',
          },
          'aggregateRating': {
            '@type': 'AggregateRating',
            'ratingValue': data.rating || 4.8,
            'reviewCount': data.reviewCount || 100,
          },
        };

      case 'FAQPage':
        return {
          ...baseSchema,
          'mainEntity': {
            '@type': 'FAQPage',
            'mainEntity': data.faqs?.map(faq => ({
              '@type': 'Question',
              'name': faq.question,
              'acceptedAnswer': {
                '@type': 'Answer',
                'text': faq.answer,
              },
            })) || [],
          },
        };

      case 'BreadcrumbList':
        return {
          '@context': 'https://schema.org',
          '@type': 'BreadcrumbList',
          'itemListElement': data.items?.map((item, idx) => ({
            '@type': 'ListItem',
            'position': idx + 1,
            'name': item.name,
            'item': item.url,
          })) || [],
        };

      case 'LocalBusiness':
        return {
          ...baseSchema,
          '@type': 'LocalBusiness',
          'address': {
            '@type': 'PostalAddress',
            'streetAddress': data.address,
            'addressLocality': data.city,
            'addressRegion': data.state,
            'postalCode': data.postalCode,
            'addressCountry': 'BR',
          },
          'telephone': data.phone,
          'email': data.email,
          'priceRange': data.priceRange,
        };

      default:
        return baseSchema;
    }
  }

  /**
   * Gera sitemap XML
   */
  generateSitemap(pages) {
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
        xmlns:mobile="http://www.google.com/schemas/sitemap-mobile/1.0">
${pages.map(page => `  <url>
    <loc>${page.url}</loc>
    <lastmod>${page.lastMod || new Date().toISOString()}</lastmod>
    <changefreq>${page.changefreq || 'weekly'}</changefreq>
    <priority>${page.priority || 0.8}</priority>
    ${page.images?.map(img => `<image:image><image:loc>${img}</image:loc></image:image>`).join('\n    ') || ''}
  </url>`).join('\n')}
</urlset>`;
    return xml;
  }

  /**
   * Gera RSS Feed
   */
  generateRSSFeed(posts) {
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>Syntexa AI - Blog</title>
  <link>${this.domain}</link>
  <description>Conteúdo de IA, automação e growth hacking</description>
  <language>pt-br</language>
${posts.map(post => `  <item>
    <title>${this.escapeXml(post.title)}</title>
    <link>${post.url}</link>
    <guid>${post.url}</guid>
    <pubDate>${new Date(post.publishedDate).toUTCString()}</pubDate>
    <description>${this.escapeXml(post.description)}</description>
    <content:encoded><![CDATA[${post.content}]]></content:encoded>
    <category>${post.category}</category>
    <author>${post.author}</author>
  </item>`).join('\n')}
</channel>
</rss>`;
    return xml;
  }

  /**
   * Gera FAQ estruturado
   */
  generateFAQ(questions) {
    return questions.map(q => ({
      '@type': 'Question',
      'name': q.question,
      'acceptedAnswer': {
        '@type': 'Answer',
        'text': q.answer,
      },
    }));
  }

  /**
   * Gera interlinkagem automática
   */
  generateInterlinks(currentPage, allPages) {
    const keywords = currentPage.keywords || [];
    const relatedPages = [];

    for (const page of allPages) {
      if (page.url === currentPage.url) continue;

      const matchedKeywords = page.keywords?.filter(k => 
        keywords.includes(k)
      ).length || 0;

      if (matchedKeywords > 0) {
        relatedPages.push({
          url: page.url,
          title: page.title,
          relevance: matchedKeywords,
        });
      }
    }

    return relatedPages.sort((a, b) => b.relevance - a.relevance).slice(0, 5);
  }

  /**
   * Otimiza título para SEO (55-60 caracteres)
   */
  optimizeTitle(title) {
    if (title.length > 60) {
      return title.substring(0, 57) + '...';
    }
    return title;
  }

  /**
   * Otimiza descrição (150-160 caracteres)
   */
  optimizeDescription(desc) {
    if (desc.length > 160) {
      return desc.substring(0, 157) + '...';
    }
    return desc;
  }

  /**
   * Escapa caracteres XML
   */
  escapeXml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  /**
   * Gera canonical tag
   */
  generateCanonical(url) {
    return `<link rel="canonical" href="${url}" />`;
  }

  /**
   * Verifica SEO score da página
   */
  checkSEOScore(page) {
    let score = 0;
    const issues = [];

    // Meta tags
    if (page.title && page.title.length > 30 && page.title.length < 60) score += 20;
    else issues.push('Título inótimo (deve ter 30-60 caracteres)');

    if (page.description && page.description.length > 100 && page.description.length < 160) score += 20;
    else issues.push('Descrição inótima (deve ter 100-160 caracteres)');

    if (page.keywords && page.keywords.length >= 3) score += 15;
    else issues.push('Palavras-chave insuficientes');

    if (page.image) score += 10;
    else issues.push('Imagem OG faltando');

    if (page.schema) score += 15;
    else issues.push('Schema.org faltando');

    if (page.canonical) score += 10;
    else issues.push('URL canônica faltando');

    if (page.interlinks && page.interlinks.length > 0) score += 10;
    else issues.push('Interlinkagem insuficiente');

    return { score: Math.min(100, score), issues };
  }
}

export default SEOEngine;
