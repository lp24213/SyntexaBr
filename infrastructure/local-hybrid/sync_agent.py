"""
VEREDA / SYNTEXA — Sync Agent (Local ↔ AWS)
===========================================
Sincroniza filas, memórias e estados entre infra local e AWS GPU.
"""

import os
import time
import json
import logging
import asyncio

import httpx
import redis.asyncio as redis

log = logging.getLogger(__name__)

AWS_BASE_URL = os.getenv("AWS_BASE_URL", "")
LOCAL_AI_API_KEY = os.getenv("LOCAL_AI_API_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_SECONDS", "300"))


class SyncAgent:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.running = True

    async def check_aws_health(self) -> bool:
        if not AWS_BASE_URL:
            return False
        try:
            r = await self.client.get(f"{AWS_BASE_URL}/health", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    async def sync_queue(self):
        """Envia jobs pendentes da fila local para AWS quando disponível."""
        if not await self.check_aws_health():
            log.debug("AWS indisponível — mantendo jobs na fila local")
            return

        # Processa até 10 jobs por ciclo
        for _ in range(10):
            job_json = await self.redis.lpop("vereda:pending:aws")
            if not job_json:
                break
            try:
                job = json.loads(job_json)
                # Envia para AWS
                endpoint = job.get("endpoint", "/v1/chat/completions")
                r = await self.client.post(
                    f"{AWS_BASE_URL}{endpoint}",
                    json=job.get("payload", {}),
                    headers={"Authorization": f"Bearer {LOCAL_AI_API_KEY}"},
                )
                if r.status_code >= 500:
                    # Reenqueue para retry
                    await self.redis.rpush("vereda:pending:aws", job_json)
                    log.warning("Job falhou no AWS — reenfileirado: %s", job.get("id"))
                else:
                    log.info("Job sincronizado com AWS: %s", job.get("id"))
            except Exception as e:
                log.error("Erro sincronizando job: %s", e)
                await self.redis.rpush("vereda:pending:aws", job_json)

    async def sync_memory(self):
        """Sincroniza memórias de curto prazo se AWS disponível."""
        # Implementação futura: sync de embeddings e contextos
        pass

    async def run(self):
        log.info("Sync Agent iniciado — intervalo: %ds", SYNC_INTERVAL)
        while self.running:
            try:
                await self.sync_queue()
                await self.sync_memory()
            except Exception as e:
                log.error("Erro no ciclo de sync: %s", e)
            await asyncio.sleep(SYNC_INTERVAL)

    async def stop(self):
        self.running = False
        await self.client.aclose()
        await self.redis.close()


async def main():
    logging.basicConfig(level=logging.INFO)
    agent = SyncAgent()
    try:
        await agent.run()
    except KeyboardInterrupt:
        log.info("Sync Agent interrompido")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
