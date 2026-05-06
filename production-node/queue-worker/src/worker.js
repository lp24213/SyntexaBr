import fs from "node:fs/promises";
import { Worker } from "bullmq";
import Redis from "ioredis";
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  base: { service: "syntexa-queue-worker" },
  timestamp: pino.stdTimeFunctions.isoTime
});

const redisUrl = process.env.REDIS_URL || "redis://redis:6379";
const queueName = process.env.QUEUE_NAME || "stt_jobs";
const eventsChannel = process.env.QUEUE_EVENTS_CHANNEL || "stt_events";
const sttServiceUrl = process.env.STT_SERVICE_URL || "http://stt-service:8001";
const sttTimeoutMs = Number(process.env.STT_TIMEOUT_MS || 240000);
const concurrency = Number(process.env.WORKER_CONCURRENCY || 2);

const redis = new Redis(redisUrl, { maxRetriesPerRequest: null });

function publish(payload) {
  return redis.publish(eventsChannel, JSON.stringify(payload));
}

async function saveResult(jobId, payload) {
  await redis.set(`stt:result:${jobId}`, JSON.stringify(payload), "EX", 60 * 60 * 6);
}

const worker = new Worker(
  queueName,
  async (job) => {
    const { filePath, languageHint } = job.data;
    const jobId = String(job.id);
    await publish({ jobId, status: "processing" });

    const form = new FormData();
    const bytes = await fs.readFile(filePath);
    const blob = new Blob([bytes], { type: "audio/wav" });
    form.set("audio", blob, "audio.wav");
    form.set("language", String(languageHint || "pt"));

    const ctrl = new AbortController();
    const to = setTimeout(() => ctrl.abort(), sttTimeoutMs);

    try {
      const resp = await fetch(`${sttServiceUrl}/transcribe`, {
        method: "POST",
        body: form,
        signal: ctrl.signal
      });
      if (!resp.ok) throw new Error(`stt_http_${resp.status}`);
      const body = await resp.json();
      const result = {
        ok: true,
        jobId,
        status: "done",
        transcript: body.text || "",
        segments: body.segments || [],
        duration_sec: body.duration_sec || null
      };
      await saveResult(jobId, result);
      await publish(result);
      await fs.rm(filePath, { force: true });
      return result;
    } catch (err) {
      logger.error({ err, jobId }, "stt job failed");
      const fail = {
        ok: false,
        jobId,
        status: "failed",
        detail: String(err?.message || err)
      };
      await saveResult(jobId, fail);
      await publish(fail);
      throw err;
    } finally {
      clearTimeout(to);
    }
  },
  {
    connection: new Redis(redisUrl, { maxRetriesPerRequest: null }),
    concurrency
  }
);

worker.on("completed", (job) => logger.info({ jobId: job.id }, "job completed"));
worker.on("failed", (job, err) => logger.warn({ jobId: job?.id, err }, "job failed"));

logger.info({ queueName, concurrency }, "queue worker started");
