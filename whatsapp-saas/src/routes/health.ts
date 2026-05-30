import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';
import { logger } from '../lib/logger.js';

export async function healthRouter(app: FastifyInstance) {
  app.get('/', async (request, reply) => {
    try {
      await pgPool.query('SELECT NOW()');
      return {
        status: 'ok',
        timestamp: new Date().toISOString(),
        database: 'connected',
        version: '1.0.0',
      };
    } catch (error) {
      logger.error('Health check failed:', error);
      reply.code(503);
      return {
        status: 'error',
        error: 'Database connection failed',
      };
    }
  });
}
