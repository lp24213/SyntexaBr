import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';
import { authenticateJWT, validateCompanyOwnership } from '../middleware/auth.js';
import { updateConfigSchema } from '../lib/validation.js';
import { logger } from '../lib/logger.js';

export async function configRouter(app: FastifyInstance) {
  // GET /config/:companyId
  app.get(
    '/:companyId',
    { onRequest: [authenticateJWT, validateCompanyOwnership] },
    async (request: any, reply) => {
      const { companyId } = request.params;
      
      const result = await pgPool.query(
        `SELECT * FROM whatsapp.company_config WHERE company_id = $1`,
        [companyId]
      );
      
      if (!result.rows[0]) {
        return reply.code(404).send({ error: 'Config not found' });
      }
      
      return result.rows[0];
    }
  );

  // PUT /config/:companyId
  app.put(
    '/:companyId',
    { onRequest: [authenticateJWT, validateCompanyOwnership] },
    async (request: any, reply) => {
      const { companyId } = request.params;
      
      const parsed = updateConfigSchema.safeParse(request.body);
      if (!parsed.success) {
        return reply.code(400).send({
          error: 'Validation failed',
          details: parsed.error.issues
        });
      }
      
      const updates = parsed.data;
      const setClause = Object.keys(updates)
        .map((key, i) => `${key} = $${i + 2}`)
        .join(', ');
      
      const values = [companyId, ...Object.values(updates)];
      
      const result = await pgPool.query(
        `UPDATE whatsapp.company_config 
         SET ${setClause}, updated_at = NOW()
         WHERE company_id = $1
         RETURNING *`,
        values
      );
      
      if (!result.rows[0]) {
        return reply.code(404).send({ error: 'Config not found' });
      }
      
      logger.info(`Config updated for company ${companyId}`);
      return result.rows[0];
    }
  );
}
