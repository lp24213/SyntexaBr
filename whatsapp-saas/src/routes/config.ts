import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';

export async function configRouter(app: FastifyInstance) {
  // GET /config/:companyId
  app.get('/:companyId', async (request: any, reply) => {
    const { companyId } = request.params;
    
    const result = await pgPool.query(
      `SELECT * FROM whatsapp.company_config WHERE company_id = $1`,
      [companyId]
    );
    
    return result.rows[0] || { error: 'Config not found' };
  });

  // PUT /config/:companyId
  app.put('/:companyId', async (request: any, reply) => {
    const { companyId } = request.params;
    const updates = request.body;
    
    const setClause = Object.keys(updates)
      .map((key, i) => `${key} = $${i + 2}`)
      .join(', ');
    
    const values = [companyId, ...Object.values(updates)];
    
    const result = await pgPool.query(
      `UPDATE whatsapp.company_config 
       SET ${setClause}
       WHERE company_id = $1
       RETURNING *`,
      values
    );
    
    return result.rows[0];
  });
}
