import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';
import { authenticateJWT } from '../middleware/auth.js';
import { logger } from '../lib/logger.js';

export async function memoryRouter(app: FastifyInstance) {
  // GET /memory/:conversationId
  app.get(
    '/:conversationId',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId } = request.params;
      const userCompanyId = request.user.company_id;
      
      // Validar ownership
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(404).send({ error: 'Conversation not found' });
      }
      
      const result = await pgPool.query(
        `SELECT id, content, created_at FROM whatsapp.memory_vectors 
         WHERE conversation_id = $1 
         ORDER BY created_at DESC LIMIT 20`,
        [conversationId]
      );
      
      return { 
        memories: result.rows.map((r: any) => r.content),
        count: result.rows.length 
      };
    }
  );

  // GET /memory/summary/:conversationId
  app.get(
    '/summary/:conversationId',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId } = request.params;
      const userCompanyId = request.user.company_id;
      
      const conversation = await pgPool.query(
        `SELECT memory_summary FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(404).send({ error: 'Conversation not found' });
      }
      
      return { summary: conversation.rows[0]?.memory_summary || '' };
    }
  );

  // POST /memory/:conversationId
  app.post(
    '/:conversationId',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId } = request.params;
      const { content } = request.body;
      const userCompanyId = request.user.company_id;
      
      if (!content || content.trim().length === 0) {
        return reply.code(400).send({ error: 'Content required' });
      }
      
      // Validar ownership
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(403).send({ error: 'Access denied' });
      }
      
      const result = await pgPool.query(
        `INSERT INTO whatsapp.memory_vectors 
         (conversation_id, content)
         VALUES ($1, $2)
         RETURNING id, created_at`,
        [conversationId, content]
      );
      
      logger.info(`Memory added to conversation ${conversationId}`);
      reply.code(201);
      return result.rows[0];
    }
  );
}
