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
import { webhookRouter } from './routes/webhook.js';
import { messagesRouter } from './routes/messages.js';
import { companiesRouter } from './routes/companies.js';
import { configRouter } from './routes/config.js';
import { toolsRouter } from './routes/tools.js';
import { memoryRouter } from './routes/memory.js';
import { healthRouter } from './routes/health.js';

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
// PLUGINS
// ─────────────────────────────────────────────────────────

await app.register(helmet);

await app.register(cors, {
  origin: (process.env.ALLOWED_ORIGINS || 'https://syntexabr.com.br').split(','),
  credentials: true,
});

await app.register(jwt, {
  secret: process.env.JWT_SECRET || 'your-secret-key',
});

// ─────────────────────────────────────────────────────────
// DATABASE CONNECTIONS
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
// DECORATORS & HOOKS
// ─────────────────────────────────────────────────────────

// Rate limiting simples em memória
const rateLimitStore = new Map<string, { count: number; resetAt: number }>();

app.addHook('onRequest', async (request, reply) => {
  const ip = request.headers['cf-connecting-ip'] || request.socket.remoteAddress;
  const now = Date.now();
  const key = `${ip}`;

  let bucket = rateLimitStore.get(key);
  if (!bucket || bucket.resetAt < now) {
    bucket = { count: 0, resetAt: now + 60000 };
    rateLimitStore.set(key, bucket);
  }

  bucket.count++;
  if (bucket.count > 1000) {
    reply.statusCode = 429;
    return reply.send({ error: 'Too many requests' });
  }
});

// ─────────────────────────────────────────────────────────
// ROTAS
// ─────────────────────────────────────────────────────────

app.register(healthRouter, { prefix: '/health' });
app.register(webhookRouter, { prefix: '/webhook' });
app.register(messagesRouter, { prefix: '/messages' });
app.register(companiesRouter, { prefix: '/companies' });
app.register(configRouter, { prefix: '/config' });
app.register(toolsRouter, { prefix: '/tools' });
app.register(memoryRouter, { prefix: '/memory' });

// ─────────────────────────────────────────────────────────
// ERROR HANDLING
// ─────────────────────────────────────────────────────────

app.setErrorHandler(async (error, request, reply) => {
  logger.error({
    error: error.message,
    stack: error.stack,
    path: request.url,
    method: request.method,
  });

  if (error.statusCode) {
    return reply.code(error.statusCode).send({ error: error.message });
  }

  reply.code(500).send({
    error: 'Internal server error',
    requestId: request.id,
  });
});

// ─────────────────────────────────────────────────────────
// SHUTDOWN GRACEFULLY
// ─────────────────────────────────────────────────────────

const gracefulShutdown = async () => {
  logger.info('🛑 Shutting down gracefully...');
  await app.close();
  await pgPool.end();
  await redis.quit();
  process.exit(0);
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// ─────────────────────────────────────────────────────────
// START SERVER
// ─────────────────────────────────────────────────────────

const start = async () => {
  try {
    await app.listen({ port: 3001, host: '0.0.0.0' });
    logger.info('🚀 Server running on http://localhost:3001');
  } catch (err) {
    logger.error(err);
    process.exit(1);
  }
};

start();
