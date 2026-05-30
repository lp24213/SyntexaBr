import { FastifyRequest, FastifyReply } from 'fastify';
import { redis } from '../index.js';
import { logger } from '../lib/logger.js';

export async function rateLimitMiddleware(
  request: FastifyRequest,
  reply: FastifyReply
) {
  const user = (request as any).user;
  if (!user || !user.id) return; // Skip if not authenticated

  const now = new Date();
  const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const rateLimitKey = `ratelimit:${user.id}:${monthKey}`;

  const limit = 10000; // 10k requests per month
  const count = await redis.incr(rateLimitKey);

  if (count === 1) {
    await redis.expire(rateLimitKey, 2592000); // 30 days
  }

  reply.header('X-RateLimit-Limit', String(limit));
  reply.header('X-RateLimit-Remaining', String(Math.max(0, limit - count)));

  if (count > limit) {
    logger.warn(`Rate limit exceeded for user ${user.id}`);
    reply.code(429);
    return reply.send({
      error: 'Too many requests',
      detail: 'Monthly limit exceeded',
      resetAt: new Date(now.getFullYear(), now.getMonth() + 1, 1).toISOString()
    });
  }
}
