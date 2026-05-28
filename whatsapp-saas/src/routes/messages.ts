import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';

export async function messagesRouter(app: FastifyInstance) {
  // GET /messages/:conversationId
  app.get('/:conversationId', async (request: any, reply) => {
    const { conversationId } = request.params;
    
    const result = await pgPool.query(
      `SELECT * FROM whatsapp.messages 
       WHERE conversation_id = $1 
       ORDER BY created_at DESC LIMIT 100`,
      [conversationId]
    );
    
    return { messages: result.rows };
  });

  // POST /messages (send manual message)
  app.post('/', async (request: any, reply) => {
    const { conversationId, content } = request.body;
    
    const result = await pgPool.query(
      `INSERT INTO whatsapp.messages 
       (conversation_id, direction, message_type, content)
       VALUES ($1, 'outbound', 'text', $2)
       RETURNING *`,
      [conversationId, content]
    );
    
    return result.rows[0];
  });
}
