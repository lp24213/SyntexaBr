import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import crypto from 'crypto';
import { redis } from '../index.js';
import { logger } from '../lib/logger.js';

export async function webhookRouter(app: FastifyInstance) {
  /**
   * GET /webhook/whatsapp
   * Validação inicial de webhook com Meta
   */
  app.get('/whatsapp', async (request: FastifyRequest, reply: FastifyReply) => {
    const query = request.query as any;
    const token = query.hub_verify_token;
    const challenge = query.hub_challenge;

    if (!token || !challenge) {
      logger.warn('❌ Webhook verification: missing parameters');
      return reply.code(400).send({ error: 'Missing parameters' });
    }

    if (token !== process.env.WHATSAPP_VERIFY_TOKEN) {
      logger.warn('❌ Webhook verification: invalid token');
      return reply.code(403).send({ error: 'Invalid verify token' });
    }

    logger.info('✅ Webhook verified');
    return reply.send(challenge);
  });

  /**
   * POST /webhook/whatsapp
   * Recebe eventos da Meta com validação HMAC
   */
  app.post('/whatsapp', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const signature = request.headers['x-hub-signature-256'] || '';
      const body = JSON.stringify(request.body);

      // Validar assinatura HMAC
      const hmac = crypto
        .createHmac('sha256', process.env.WHATSAPP_APP_SECRET || '')
        .update(body)
        .digest('hex');

      const expected = 'sha256=' + hmac;

      if (signature !== expected) {
        logger.warn('❌ Invalid webhook signature');
        return reply.code(403).send({ error: 'Invalid signature' });
      }

      // Responder rapidamente para Meta (não pode levar mais que 20s)
      reply.code(200).send({ received: true });

      // Processar eventos assincronamente
      const data = request.body as any;

      for (const entry of data.entry || []) {
        for (const change of entry.changes || []) {
          if (change.field !== 'messages') continue;

          const messages = change.value.messages || [];
          const contacts = change.value.contacts || [];
          const phone_number_id = change.value.metadata?.phone_number_id;

          if (!phone_number_id) {
            logger.error('❌ No phone_number_id in webhook');
            continue;
          }

          // SEGURANÇA: Validar que phone_number_id existe no BD
          // Será feito no orchestrator, mas logamos aqui
          logger.info(`📨 Webhook received for phone_number_id: ${phone_number_id}, messages: ${messages.length}`);

          for (const message of messages) {
            try {
              // Enfileirar com validação
              await redis.lPush(
                'queue:messages',
                JSON.stringify({
                  phone_number_id,
                  message,
                  contacts,
                  receivedAt: new Date().toISOString()
                })
              );
              
              logger.info(`✅ Message enqueued: ${message.id}`);
            } catch (error) {
              logger.error('Failed to enqueue message:', error);
            }
          }
        }
      }

    } catch (error) {
      logger.error('Webhook processing error:', error);
      // Não devemos retornar erro para Meta - é tarde demais de qualquer forma
    }
  });
}
