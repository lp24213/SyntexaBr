import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';

export async function companiesRouter(app: FastifyInstance) {
  // GET /companies - listar todas
  app.get('/', async (request: any, reply) => {
    const result = await pgPool.query(
      `SELECT id, name, email, plan, tokens_used, tokens_limit, created_at 
       FROM whatsapp.companies ORDER BY created_at DESC`
    );
    return { companies: result.rows };
  });

  // POST /companies - criar nova
  app.post('/', async (request: any, reply) => {
    const { name, email, plan } = request.body;
    
    const result = await pgPool.query(
      `INSERT INTO whatsapp.companies (name, email, plan)
       VALUES ($1, $2, $3)
       RETURNING *`,
      [name, email, plan || 'free']
    );
    
    reply.code(201);
    return result.rows[0];
  });

  // POST /companies/:id/phone-numbers - adicionar número
  app.post('/:id/phone-numbers', async (request: any, reply) => {
    const { id } = request.params;
    const { phone_number_id, display_number, waba_id, access_token } = request.body;
    
    const result = await pgPool.query(
      `INSERT INTO whatsapp.phone_numbers 
       (company_id, phone_number_id, display_number, waba_id, access_token)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [id, phone_number_id, display_number, waba_id, access_token]
    );
    
    reply.code(201);
    return result.rows[0];
  });
}
