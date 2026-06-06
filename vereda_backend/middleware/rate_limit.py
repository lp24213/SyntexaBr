# ⏱️ Rate Limiting Middleware
# Migrado de production-node/api/src/rateLimit.js para vereda_backend

import logging
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
import redis
import os

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    """Redis-backed rate limiter for distributed rate limiting across multiple instances"""
    
    def __init__(
        self,
        redis_url: str | None = None,
        window_ms: int = 60_000,  # 1 minuto
        max_requests: int = 120,  # 120 requests per window
    ):
        self.window_ms = window_ms
        self.max_requests = max_requests
        self.prefix = "rl:"
        
        try:
            self.redis_client = redis.from_url(
                redis_url or os.getenv("REDIS_URL", "redis://redis:6379"),
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis rate limiter connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}. Using in-memory rate limiting (NOT PRODUCTION SAFE)")
            self.redis_client = None
            self._memory_store = {}  # Fallback para in-memory
    
    def get_client_id(self, request: Request) -> str:
        """Extract real client IP (respects X-Forwarded-For from proxies)"""
        # Cloudflare headers
        if cf_connecting_ip := request.headers.get("cf-connecting-ip"):
            return cf_connecting_ip
        # Standard proxy header
        if x_forwarded_for := request.headers.get("x-forwarded-for"):
            return x_forwarded_for.split(",")[0].strip()
        # Direct connection
        return request.client.host if request.client else "unknown"
    
    async def check_limit(self, request: Request) -> tuple[bool, dict]:
        """Check if request exceeds rate limit. Returns (allowed, metadata)"""
        client_id = self.get_client_id(request)
        key = f"{self.prefix}{client_id}"
        
        try:
            if self.redis_client:
                # Use Redis for distributed rate limiting
                current = self.redis_client.incr(key)
                ttl = self.redis_client.ttl(key)
                
                if current == 1:
                    # First request in window
                    self.redis_client.expire(key, int(self.window_ms / 1000))
                
                remaining = max(0, self.max_requests - current)
                reset_at = datetime.utcnow() + timedelta(milliseconds=self.window_ms)
                
                allowed = current <= self.max_requests
                
                return allowed, {
                    "limit": self.max_requests,
                    "current": current,
                    "remaining": remaining,
                    "reset_at": reset_at.isoformat(),
                    "client_id": client_id,
                }
            else:
                # Fallback: in-memory (not thread-safe, NOT for production)
                now = datetime.utcnow()
                if key not in self._memory_store:
                    self._memory_store[key] = {"count": 0, "reset_at": now + timedelta(milliseconds=self.window_ms)}
                
                entry = self._memory_store[key]
                
                if now >= entry["reset_at"]:
                    entry["count"] = 0
                    entry["reset_at"] = now + timedelta(milliseconds=self.window_ms)
                
                entry["count"] += 1
                remaining = max(0, self.max_requests - entry["count"])
                allowed = entry["count"] <= self.max_requests
                
                return allowed, {
                    "limit": self.max_requests,
                    "current": entry["count"],
                    "remaining": remaining,
                    "reset_at": entry["reset_at"].isoformat(),
                    "client_id": client_id,
                }
        
        except Exception as e:
            logger.error(f"❌ Rate limiter error: {e}")
            # On error, allow the request but log it
            return True, {"error": str(e), "client_id": client_id}
    
    async def middleware(self, request: Request):
        """FastAPI middleware decorator"""
        allowed, metadata = await self.check_limit(request)
        
        if not allowed:
            logger.warning(f"❌ Rate limit exceeded for {metadata['client_id']}")
            raise HTTPException(
                status_code=429,
                detail={
                    "ok": False,
                    "error": "too_many_requests",
                    "message": "Muitas requisições; aguarde alguns segundos e tente novamente.",
                    "reset_at": metadata["reset_at"],
                }
            )
        
        return None


# ✅ Initialize global rate limiter
rate_limiter = RedisRateLimiter(
    redis_url=os.getenv("REDIS_URL"),
    window_ms=int(os.getenv("API_RATE_LIMIT_WINDOW_MS", 60_000)),
    max_requests=int(os.getenv("API_RATE_LIMIT_MAX", 120)),
)
