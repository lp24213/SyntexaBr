/**
 * Queue Worker - Processa mensagens da fila Redis
 */

import { Pool } from 'pg';
import { createClient } from 'redis';
import dotenv from 'dotenv';
import { orchestrateMessage } from '../orchestrator/index.js';
import { logger } from '../lib/logger.js';

dotenv.config();

const pgPool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

const redis = createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379',
});

redis.on('error', (err) => {
  logger.error('Redis error:', err);
});

await redis.connect();
logger.info('Queue worker started');

async function processQueue() {
  while (true) {
    try {
      const job = await redis.brPop('queue:messages', 0);
      if (!job) continue;

      const data = JSON.parse(job.element);
      const { phone_number_id, message, contacts } = data;

      logger.info(`Processing message ${message.id}`);
      await orchestrateMessage(phone_number_id, message, contacts);
      logger.info(`Message ${message.id} processed`);
    } catch (error) {
      logger.error('Queue processing error:', error);
      await new Promise(r => setTimeout(r, 1000));
    }
  }
}

process.on('SIGTERM', async () => {
  logger.info('Worker shutting down...');
  await redis.quit();
  await pgPool.end();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('Worker shutting down...');
  await redis.quit();
  await pgPool.end();
  process.exit(0);
});

processQueue();
