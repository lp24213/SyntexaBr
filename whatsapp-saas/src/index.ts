/**
 * Syntexa WhatsApp SaaS Backend
 * 
 * Servidor Fastify que:
 * - Recebe webhooks da Meta
 * - Processa mensagens assincronamente
 * - Orquestra chamadas à LLM Syntexa
 * - Gerencia memória e contexto
 * - Executa tools (PDF, Excel, etc)
 * - Envia respostas via WhatsApp Cloud API
 */

import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import jwt from '@fastify/jwt';
import { Pool } from 'pg';
import { createClient } from 'redis';
import dotenv from 'dotenv';
import { logger } from './lib/logger.js';
import { rateLimitMiddleware } from './middleware/rate-limit.js';
import { authenticateJWT } from './middleware/auth.js';
import { webhookRouter } from './routes/webhook.js';
import { messagesRouter } from './routes/messages.js';
import { companiesRouter } from './routes/companies.js';
import { configRouter } from './routes/config.js';
import { toolsRouter } from './routes/tools.js';
import { memoryRouter } from './routes/memory.js';
import { healthRouter } from './routes/health.js';
import { authRouter } from './routes/auth.js';

dotenv.config();

// ─────────────────────────────────────────────────────────
// INICIALIZAÇÃO
// ─────────────────────────────────────────────────────────

const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
      },
    },
  },
});

// ─────────────────────────────────────────────────────────
// PLUGINS DE SEGURANÇA
// ─────────────────────────────────────────────────────────

await app.register(helmet);

await app.register(cors, {
  origin: (process.env.ALLOWED_ORIGINS || 'https://syntexabr.com.br').split(','),
  credentials: true,
});

await app.register(jwt, {
  secret: process.env.JWT_SECRET || 'your-secret-key',
  sign: {
    expiresIn: '24h'
  }
});

// ─────────────────────────────────────────────────────────
// CONEXÕES DE BANCO DE DADOS
// ─────────────────────────────────────────────────────────

export const pgPool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export const redis = createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379',
});

redis.on('error', (err) => {
  logger.error('Redis error:', err);
});

await redis.connect();
logger.info('✅ Redis connected');

await pgPool.query('SELECT NOW()').then(() => {
  logger.info('✅ PostgreSQL connected');
});

// ─────────────────────────────────────────────────────────
// MIDDLEWARE GLOBAL
// ─────────────────────────────────────────────────────────

// Rate limiting distribuído (após autenticação)
app.addHook('onRequest', async (request, reply) => {
  // Webhook do Meta não precisa de auth
  if (request.url.includes('/webhook/whatsapp')) {
    return;
  }
  
  // Health check não precisa de auth
  if (request.url.includes('/health')) {
    return;
  }
  
  // Autenticar
  try {
    await authenticateJWT(request, reply);
  } catch (err) {
    // Middleware de auth retorna error
    return;
  }
  
  // Rate limit após autenticar
  await rateLimitMiddleware(request, reply);
});

// ─────────────────────────────────────────────────────────
// ROTAS
// ─────────────────────────────────────────────────────────

app.register(healthRouter, { prefix: '/health' });
app.register(webhookRouter, { prefix: '/webhook' });
app.register(authRouter, { prefix: '/auth' });
app.register(messagesRouter, { prefix: '/messages' });
app.register(companiesRouter, { prefix: '/companies' });
app.register(configRouter, { prefix: '/config' });
app.register(toolsRouter, { prefix: '/tools' });
app.register(memoryRouter, { prefix: '/memory' });

// ─────────────────────────────────────────────────────────
// TRATAMENTO DE ERROS
// ─────────────────────────────────────────────────────────

app.setErrorHandler(async (err: any, request, reply) => {
  logger.error({
    error: err.message,
    stack: err.stack,
    path: request.url,
    method: request.method,
    statusCode: err.statusCode,
  });

  if (err.statusCode) {
    return reply.code(err.statusCode).send({ 
      error: err.message,
      statusCode: err.statusCode
    });
  }

  reply.code(500).send({
    error: 'Internal server error',
    requestId: request.id,
  });
});

// ─────────────────────────────────────────────────────────
// SHUTDOWN GRACIOSO
// ─────────────────────────────────────────────────────────

process.on('SIGTERM', async () => {
  logger.info('🛑 SIGTERM received, shutting down gracefully...');
  
  app.server.close();
  await new Promise(resolve => setTimeout(resolve, 30000));
  
  await pgPool.end();
  await redis.quit();
  
  logger.info('✅ Shutdown complete');
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  logger.error('💥 Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('💥 Unhandled rejection:', { reason, promise });
  process.exit(1);
});

// ─────────────────────────────────────────────────────────
// START SERVER
// ─────────────────────────────────────────────────────────

const start = async () => {
  try {
    await app.listen({ port: 3001, host: '0.0.0.0' });
    logger.info('🚀 Server running on http://0.0.0.0:3001');
  } catch (err) {
    logger.error('Failed to start server:', err);
    process.exit(1);
  }
};

start();

const gracefulShutdown = async () => {
  logger.info('🛑 Shutting down gracefully...');
  await app.close();
  await pgPool.end();
  await redis.quit();
  process.exit(0);
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);
