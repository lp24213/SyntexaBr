import { Queue } from "bullmq";
import Redis from "ioredis";

const redisUrl = process.env.REDIS_URL || "redis://redis:6379";

export const connection = new Redis(redisUrl, {
  maxRetriesPerRequest: null,
  enableReadyCheck: true,
  lazyConnect: false
});

export const queueName = process.env.QUEUE_NAME || "stt_jobs";
export const queueEventsChannel = process.env.QUEUE_EVENTS_CHANNEL || "stt_events";

export const sttQueue = new Queue(queueName, {
  connection,
  defaultJobOptions: {
    attempts: Number(process.env.MAX_JOB_ATTEMPTS || 3),
    removeOnComplete: 2000,
    removeOnFail: 2000,
    backoff: {
      type: "exponential",
      delay: Number(process.env.JOB_BACKOFF_MS || 5000)
    }
  }
});
