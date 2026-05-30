import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';
import { authenticateJWT } from '../middleware/auth.js';
import { createMessageSchema } from '../lib/validation.js';
import { logger } from '../lib/logger.js';

export async function messagesRouter(app: FastifyInstance) {
  // GET /messages/:conversationId
  app.get(
    '/:conversationId',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId } = request.params;
      const userCompanyId = request.user.company_id;
      
      // CRÍTICO: Validar que conversa pertence à empresa do usuário
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        logger.warn(`Unauthorized access attempt to conversation ${conversationId}`);
        return reply.code(404).send({ error: 'Conversation not found' });
      }
      
      const result = await pgPool.query(
        `SELECT id, direction, message_type, content, media_url, created_at 
         FROM whatsapp.messages 
         WHERE conversation_id = $1 
         ORDER BY created_at DESC LIMIT 100`,
        [conversationId]
      );
      
      return { messages: result.rows };
    }
  );

  // POST /messages (send manual message)
  app.post(
    '/',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const userCompanyId = request.user.company_id;
      
      const parsed = createMessageSchema.safeParse(request.body);
      if (!parsed.success) {
        return reply.code(400).send({
          error: 'Validation failed',
          details: parsed.error.issues
        });
      }
      
      const { conversationId, content } = parsed.data;
      
      // Validar que conversa pertence à empresa do usuário
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        logger.warn(`Unauthorized message attempt to conversation ${conversationId}`);
        return reply.code(403).send({ error: 'Access denied' });
      }
      
      const result = await pgPool.query(
        `INSERT INTO whatsapp.messages 
         (conversation_id, direction, message_type, content)
         VALUES ($1, 'outbound', 'text', $2)
         RETURNING id, created_at`,
        [conversationId, content]
      );
      
      logger.info(`Message sent to conversation ${conversationId}`);
      reply.code(201);
      return result.rows[0];
    }
  );
}
