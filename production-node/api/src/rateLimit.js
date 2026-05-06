import rateLimit from "express-rate-limit";

export function apiRateLimiter() {
  const windowMs = Number(process.env.API_RATE_LIMIT_WINDOW_MS || 60_000);
  const limit = Number(process.env.API_RATE_LIMIT_MAX || 120);
  return rateLimit({
    windowMs,
    limit,
    standardHeaders: true,
    legacyHeaders: false,
    message: {
      ok: false,
      error: "too_many_requests",
      detail: "Muitas requisições; aguarde alguns segundos e tente novamente."
    }
  });
}
