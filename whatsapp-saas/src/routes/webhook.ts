import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import crypto from 'crypto';
import { pgPool, redis } from '../index.js';
import { logger } from '../lib/logger.js';
import { orchestrateMessage } from '../orchestrator/index.js';

export async function webhookRouter(app: FastifyInstance) {
  /**
   * GET /webhook/whatsapp
   * Validação de webhook com Meta
   */
  app.get('/whatsapp', async (request: FastifyRequest, reply: FastifyReply) => {
    const token = request.query.hub_verify_token;
    const challenge = request.query.hub_challenge;

    if (token !== process.env.WHATSAPP_VERIFY_TOKEN) {
      logger.warn('❌ Invalid verify token');
      return reply.code(403).send({ error: 'Invalid verify token' });
    }

    logger.info('✅ Webhook verified');
    return reply.send(challenge);
  });

  /**
   * POST /webhook/whatsapp
   * Recebe eventos da Meta
   */
  app.post('/whatsapp', async (request: FastifyRequest, reply: FastifyReply) => {
    const signature = request.headers['x-hub-signature-256'] || '';
    const body = JSON.stringify(request.body);

    // Validar assinatura
    const expected = 'sha256=' + crypto
      .createHmac('sha256', process.env.WHATSAPP_APP_SECRET || '')
      .update(body)
      .digest('hex');

    if (signature !== expected) {
      logger.warn('❌ Invalid webhook signature');
      return reply.code(403).send({ error: 'Invalid signature' });
    }

    // Responder rapidamente para Meta
    reply.code(200).send({ received: true });

    try {
      const data = request.body as any;

      // Processar cada entrada
      for (const entry of data.entry || []) {
        for (const change of entry.changes || []) {
          if (change.field !== 'messages') continue;

          const messages = change.value.messages || [];
          const contacts = change.value.contacts || [];
          const phone_number_id = change.value.metadata?.phone_number_id;

          for (const message of messages) {
            try {
              // Enqueue para processamento assíncrono
              await redis.lPush('queue:messages', JSON.stringify({
                phone_number_id,
                message,
                contacts,
                timestamp: Date.now(),
              }));

              logger.info(`📨 Message queued: ${message.id}`);
            } catch (error) {
              logger.error('Failed to queue message:', error);
            }
          }
        }
      }
    } catch (error) {
      logger.error('Webhook processing error:', error);
    }
  });
}
