/**
 * Cloudflare Worker - Gateway WhatsApp
 * 
 * Rota segura para:
 * - Validação de webhooks Meta
 * - Rate limiting edge
 * - Caching inteligente
 * - Logging centralizador
 */

export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // ─────────────────────────────────────────────────────
    // HEALTH CHECK
    // ─────────────────────────────────────────────────────
    if (path === '/whatsapp/health' && request.method === 'GET') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // ─────────────────────────────────────────────────────
    // WEBHOOK VALIDATION (GET)
    // ─────────────────────────────────────────────────────
    if (path === '/whatsapp/webhook' && request.method === 'GET') {
      const token = url.searchParams.get('hub_verify_token');
      const challenge = url.searchParams.get('hub_challenge');

      if (token === env.WHATSAPP_VERIFY_TOKEN) {
        return new Response(challenge);
      }
      return new Response('Invalid token', { status: 403 });
    }

    // ─────────────────────────────────────────────────────
    // WEBHOOK EVENTS (POST)
    // ─────────────────────────────────────────────────────
    if (path === '/whatsapp/webhook' && request.method === 'POST') {
      const signature = request.headers.get('x-hub-signature-256') || '';
      const body = await request.text();

      // Validar assinatura
      const hmac = await crypto.subtle.sign(
        'HMAC',
        await crypto.subtle.importKey(
          'raw',
          new TextEncoder().encode(env.WHATSAPP_APP_SECRET),
          { name: 'HMAC', hash: 'SHA-256' },
          false,
          ['sign']
        ),
        new TextEncoder().encode(body)
      );

      const expected = 'sha256=' + Array.from(new Uint8Array(hmac))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');

      if (signature !== expected) {
        return new Response('Invalid signature', { status: 403 });
      }

      // Rate limiting simples
      const ip = request.headers.get('cf-connecting-ip') || 'unknown';
      const rateLimitKey = `ratelimit:${ip}`;
      const count = await env.RATE_LIMIT.get(rateLimitKey) || '0';

      if (parseInt(count) > 1000) {
        return new Response('Rate limit exceeded', { status: 429 });
      }

      await env.RATE_LIMIT.put(
        rateLimitKey,
        (parseInt(count) + 1).toString(),
        { expirationTtl: 60 }
      );

      // Proxy para backend
      const backendUrl = new URL(path, env.WHATSAPP_BACKEND_URL);
      const backendRequest = new Request(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Forwarded-For': ip,
        },
        body,
      });

      try {
        const response = await fetch(backendRequest);
        return new Response(JSON.stringify({ received: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      } catch (error) {
        console.error('Backend error:', error);
        return new Response(JSON.stringify({ error: 'Backend unavailable' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    // ─────────────────────────────────────────────────────
    // OUTRAS ROTAS → proxy para backend
    // ─────────────────────────────────────────────────────
    if (path.startsWith('/whatsapp/')) {
      const backendUrl = new URL(path, env.WHATSAPP_BACKEND_URL);
      backendUrl.search = url.search;

      const backendRequest = new Request(backendUrl, {
        method: request.method,
        headers: request.headers,
        body: request.method !== 'GET' ? await request.text() : undefined,
      });

      try {
        return await fetch(backendRequest);
      } catch (error) {
        return new Response(JSON.stringify({ error: 'Backend unavailable' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    return new Response('Not found', { status: 404 });
  },
};
