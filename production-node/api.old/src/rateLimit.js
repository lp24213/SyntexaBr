import rateLimit from "express-rate-limit";
import RedisStore from "rate-limit-redis";
import Redis from "ioredis";

// ✅ Redis client para rate limiting (escalável em múltiplas instâncias)
let redisClient;

try {
  redisClient = new Redis(process.env.REDIS_URL || "redis://redis:6379");
  redisClient.on("error", (err) => console.error("Redis connection error:", err));
} catch (err) {
  console.warn("Redis not available, rate limiting will use memory (NOT PRODUCTION SAFE)");
}

export function apiRateLimiter() {
  const windowMs = Number(process.env.API_RATE_LIMIT_WINDOW_MS || 60_000);
  const limit = Number(process.env.API_RATE_LIMIT_MAX || 120);

  // ✅ Se Redis disponível, usa persistência distribuída; senão fallback (com warning)
  const store = redisClient
    ? new RedisStore({
        client: redisClient,
        prefix: "rl:",
        sendCommand: async (cmd, args) => {
          try {
            return await redisClient.call(cmd, ...args);
          } catch (err) {
            console.error("Redis command error:", err);
            throw err;
          }
        },
      })
    : undefined; // Fallback para memory store

  return rateLimit({
    store,
    windowMs,
    max: limit,
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req, res) => {
      // ✅ Usar IP real, não X-Forwarded-For sem validação
      return req.ip || req.connection.remoteAddress || "unknown";
    },
    message: {
      ok: false,
      error: "too_many_requests",
      detail: "Muitas requisições; aguarde alguns segundos e tente novamente."
    },
    skip: (req) => {
      // ✅ Não limitar health checks
      return req.path === "/health";
    }
  });
}
