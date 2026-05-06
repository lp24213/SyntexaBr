import cors from "cors";
import express from "express";
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import multer from "multer";
import pinoHttp from "pino-http";
import Redis from "ioredis";
import { Server } from "socket.io";
import { v4 as uuidv4 } from "uuid";
import { logger } from "./logger.js";
import { apiRateLimiter } from "./rateLimit.js";
import { sttQueue, connection, queueEventsChannel } from "./queue.js";

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  path: "/socket.io",
  cors: {
    origin: process.env.WS_CORS_ORIGIN || "*"
  }
});

const port = Number(process.env.PORT || 3001);
const uploadDir = process.env.UPLOAD_DIR || "/data/uploads";
fs.mkdirSync(uploadDir, { recursive: true });

const upload = multer({
  storage: multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, uploadDir),
    filename: (_req, file, cb) => {
      const ext = path.extname(file.originalname || "") || ".bin";
      cb(null, `${Date.now()}-${uuidv4()}${ext}`);
    }
  }),
  limits: {
    fileSize: 40 * 1024 * 1024
  }
});

app.use(express.json({ limit: "1mb" }));
app.use(cors());
app.use(apiRateLimiter());
app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return { method: req.method, url: req.url, id: req.id };
      }
    }
  })
);

const pubsub = new Redis(process.env.REDIS_URL || "redis://redis:6379");
pubsub.subscribe(queueEventsChannel);
pubsub.on("message", (_channel, message) => {
  try {
    const payload = JSON.parse(message);
    if (payload?.jobId) {
      io.to(`job:${payload.jobId}`).emit("stt:status", payload);
    }
  } catch (err) {
    logger.warn({ err }, "invalid pubsub payload");
  }
});

io.on("connection", (socket) => {
  socket.on("stt:watch", ({ jobId }) => {
    if (!jobId) return;
    socket.join(`job:${jobId}`);
  });
});

app.get("/health", async (_req, res) => {
  try {
    const pong = await connection.ping();
    res.json({
      ok: true,
      service: "syntexa-api",
      redis: pong === "PONG" ? "up" : "down"
    });
  } catch {
    res.status(503).json({ ok: false, service: "syntexa-api", redis: "down" });
  }
});

app.post("/api/stt/enqueue", upload.any(), async (req, res) => {
  const files = Array.isArray(req.files) ? req.files : [];
  const picked =
    files.find((f) => f && (f.fieldname === "audio" || f.fieldname === "file")) || files[0];
  if (!picked) {
    return res.status(400).json({ ok: false, error: "audio_file_required" });
  }

  const clientJobId = String(req.body?.clientJobId || uuidv4());
  const job = await sttQueue.add("transcribe", {
    jobId: clientJobId,
    filePath: picked.path,
    mimeType: picked.mimetype || "application/octet-stream",
    originalName: picked.originalname || "audio.bin",
    languageHint: req.body?.language || "pt"
  });

  res.status(202).json({
    ok: true,
    jobId: job.id,
    status: "queued"
  });
});

app.get("/api/stt/status/:jobId", async (req, res) => {
  const key = `stt:result:${req.params.jobId}`;
  const raw = await connection.get(key);
  if (!raw) return res.status(404).json({ ok: false, status: "not_found" });
  return res.json(JSON.parse(raw));
});

server.listen(port, () => {
  logger.info({ port }, "syntexa api started");
});
