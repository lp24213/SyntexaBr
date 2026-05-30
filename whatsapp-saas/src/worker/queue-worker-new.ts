/**
 * Queue Worker - Processa mensagens da fila Redis
 * Com retry logic, dead-letter queue e tratamento de erros robusto
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
logger.info('✅ Queue worker started');

const MAX_RETRIES = 3;

interface QueueJob {
  phone_number_id: string;
  message: any;
  contacts: any[];
  retries?: number;
  enqueuedAt?: string;
}

async function processQueue() {
  logger.info('Processing queue...');
  
  while (true) {
    let job: any = null;
    try {
      // Blocking pop with 1 second timeout
      job = await redis.brPop('queue:messages', 1);
      if (!job) continue;

      const data: QueueJob = JSON.parse(job.element);
      const retries = data.retries || 0;
      
      logger.info(`📨 Processing job (attempt ${retries + 1}/${MAX_RETRIES + 1}):`, {
        phone_number_id: data.phone_number_id,
        message_id: data.message?.id,
        retries
      });

      try {
        // Processar mensagem
        await orchestrateMessage(
          data.phone_number_id, 
          data.message, 
          data.contacts
        );
        
        logger.info(`✅ Job processed successfully: ${data.message?.id}`);
        // Job é removido do Redis automaticamente (via brPop)
        
      } catch (processingError) {
        logger.error(`❌ Job processing failed (attempt ${retries + 1}):`, {
          error: (processingError as Error).message,
          message_id: data.message?.id,
          phone_number_id: data.phone_number_id
        });
        
        if (retries < MAX_RETRIES) {
          // Retentar com backoff exponencial: 1s, 2s, 4s
          const delay = Math.pow(2, retries) * 1000;
          logger.info(`⏳ Retrying in ${delay}ms...`, { 
            message_id: data.message?.id 
          });
          
          await new Promise(r => setTimeout(r, delay));
          
          // Re-enfileirar com retry counter incrementado
          await redis.lPush(
            'queue:messages',
            JSON.stringify({
              ...data,
              retries: retries + 1,
              enqueuedAt: new Date().toISOString()
            })
          );
        } else {
          // Enviar para DLQ após max retries
          logger.error(`🚨 Max retries exceeded, moving to DLQ:`, {
            message_id: data.message?.id,
            error: (processingError as Error).message
          });
          
          await redis.lPush(
            'queue:dlq',
            JSON.stringify({
              ...data,
              failedAt: new Date().toISOString(),
              error: (processingError as Error).message,
              stack: (processingError as Error).stack
            })
          );
        }
      }
      
    } catch (error) {
      logger.error('Queue worker error:', error);
      // Se falhar parseando, não retentar - apenas logar e continuar
      await new Promise(r => setTimeout(r, 1000));
    }
  }
}

// Monitorar DLQ periodicamente
async function monitorDLQ() {
  setInterval(async () => {
    try {
      const dlqSize = await redis.lLen('queue:dlq');
      if (dlqSize > 0) {
        logger.warn(`⚠️ DLQ has ${dlqSize} items - may need manual intervention`);
        
        // Logar primeiros 5 items
        const items = await redis.lRange('queue:dlq', 0, 4);
        for (const item of items) {
          const data = JSON.parse(item);
          logger.error('DLQ Item:', {
            message_id: data.message?.id,
            error: data.error,
            failedAt: data.failedAt
          });
        }
      }
    } catch (err) {
      logger.error('DLQ monitoring error:', err);
    }
  }, 60000); // Verificar a cada minuto
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('🛑 SIGTERM received, shutting down gracefully...');
  await redis.quit();
  await pgPool.end();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('🛑 SIGINT received, shutting down gracefully...');
  await redis.quit();
  await pgPool.end();
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  logger.error('💥 Uncaught exception:', error);
  process.exit(1);
});

// Start processing
monitorDLQ();
processQueue().catch(error => {
  logger.error('💥 Fatal worker error:', error);
  process.exit(1);
});
