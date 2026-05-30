import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';
import { authenticateJWT, validateCompanyOwnership } from '../middleware/auth.js';
import { createPhoneNumberSchema, createCompanySchema } from '../lib/validation.js';
import { logger } from '../lib/logger.js';

export async function companiesRouter(app: FastifyInstance) {
  // GET /companies - retorna apenas a empresa do usuário
  app.get(
    '/',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const userCompanyId = request.user.company_id;
      
      const result = await pgPool.query(
        `SELECT id, name, email, plan, tokens_used, tokens_limit, created_at 
         FROM whatsapp.companies 
         WHERE id = $1
         ORDER BY created_at DESC`,
        [userCompanyId]
      );
      
      return { companies: result.rows };
    }
  );

  // POST /companies - criar nova (admin only)
  app.post(
    '/',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const parsed = createCompanySchema.safeParse(request.body);
      if (!parsed.success) {
        return reply.code(400).send({
          error: 'Validation failed',
          details: parsed.error.issues
        });
      }
      
      const { name, email, plan } = parsed.data;
      
      const result = await pgPool.query(
        `INSERT INTO whatsapp.companies (name, email, plan)
         VALUES ($1, $2, $3)
         RETURNING id, name, email, plan, created_at`,
        [name, email, plan]
      );
      
      logger.info(`Company created: ${result.rows[0].id}`);
      reply.code(201);
      return result.rows[0];
    }
  );

  // POST /companies/:id/phone-numbers - adicionar número
  app.post(
    '/:id/phone-numbers',
    { onRequest: [authenticateJWT, validateCompanyOwnership] },
    async (request: any, reply) => {
      const { id } = request.params;
      const userCompanyId = request.user.company_id;
      
      // Double-check company ownership
      if (id !== userCompanyId) {
        return reply.code(403).send({ error: 'Access denied' });
      }
      
      const parsed = createPhoneNumberSchema.safeParse(request.body);
      if (!parsed.success) {
        return reply.code(400).send({
          error: 'Validation failed',
          details: parsed.error.issues
        });
      }
      
      const { phone_number_id, display_number, waba_id, access_token } = parsed.data;
      
      // Verify phone number doesn't already exist
      const existing = await pgPool.query(
        `SELECT id FROM whatsapp.phone_numbers WHERE phone_number_id = $1`,
        [phone_number_id]
      );
      
      if (existing.rows.length > 0) {
        return reply.code(409).send({ error: 'Phone number already registered' });
      }
      
      const result = await pgPool.query(
        `INSERT INTO whatsapp.phone_numbers 
         (company_id, phone_number_id, display_number, waba_id, access_token)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING id, phone_number_id, display_number, created_at`,
        [id, phone_number_id, display_number, waba_id, access_token]
      );
      
      logger.info(`Phone number added: ${phone_number_id} for company ${id}`);
      reply.code(201);
      return result.rows[0];
    }
  );
}
