import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';

export async function memoryRouter(app: FastifyInstance) {
  // GET /memory/:conversationId - recuperar memória
  app.get('/:conversationId', async (request: any, reply) => {
    const { conversationId } = request.params;
    
    const result = await pgPool.query(
      `SELECT content FROM whatsapp.memory_vectors 
       WHERE conversation_id = $1 
       ORDER BY created_at DESC LIMIT 20`,
      [conversationId]
    );
    
    return { 
      memories: result.rows.map((r: any) => r.content),
      count: result.rows.length 
    };
  });

  // GET /memory/summary/:conversationId - sumário da conversa
  app.get('/summary/:conversationId', async (request: any, reply) => {
    const { conversationId } = request.params;
    
    const result = await pgPool.query(
      `SELECT memory_summary FROM whatsapp.conversations 
       WHERE id = $1`,
      [conversationId]
    );
    
    return { summary: result.rows[0]?.memory_summary || '' };
  });

  // POST /memory/:conversationId - adicionar à memória
  app.post('/:conversationId', async (request: any, reply) => {
    const { conversationId } = request.params;
    const { content } = request.body;
    
    const result = await pgPool.query(
      `INSERT INTO whatsapp.memory_vectors 
       (conversation_id, content)
       VALUES ($1, $2)
       RETURNING *`,
      [conversationId, content]
    );
    
    reply.code(201);
    return result.rows[0];
  });
}
