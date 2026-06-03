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

// ✅ CORS whitelist — SOMENTE domínios confiáveis
const ALLOWED_ORIGINS = [
  "https://syntexabr.com.br",
  "https://www.syntexabr.com.br",
  "https://app.syntexabr.com.br",
  "https://production.syntexa-frontend.pages.dev",
  "http://localhost:3000", // Dev only
];

const corsOptions = {
  origin: (origin, callback) => {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      logger.warn({ origin }, "CORS origin rejected");
      callback(new Error("CORS not allowed"));
    }
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
  maxAge: 86400,
};

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  path: "/socket.io",
  cors: corsOptions
});

const port = Number(process.env.PORT || 3001);
const uploadDir = process.env.UPLOAD_DIR || "/data/uploads";
fs.mkdirSync(uploadDir, { recursive: true });

// ✅ WHITELIST de tipos MIME permitidos SOMENTE
const ALLOWED_MIME_TYPES = [
  "audio/webm",
  "audio/mp4",
  "audio/mpeg",
  "audio/wav",
  "audio/ogg",
  "audio/flac",
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
  "text/plain",
  "text/csv",
];

const ALLOWED_EXTENSIONS = [".webm", ".mp4", ".mp3", ".wav", ".ogg", ".flac", ".pdf", ".docx", ".xlsx", ".txt", ".csv"];

const upload = multer({
  storage: multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, uploadDir),
    filename: (_req, file, cb) => {
      // ✅ Sanitizar nome do arquivo (remover path traversal)
      const sanitized = path.basename(file.originalname || "").replace(/[^\w.-]/g, "_");
      const ext = path.extname(sanitized) || ".bin";
      cb(null, `${Date.now()}-${uuidv4()}${ext}`);
    }
  }),
  fileFilter: (req, file, cb) => {
    // ✅ Validar MIME type (whitelist)
    if (!ALLOWED_MIME_TYPES.includes(file.mimetype)) {
      logger.warn({ mimetype: file.mimetype }, "MIME type rejected");
      return cb(new Error(`MIME type not allowed: ${file.mimetype}`));
    }
    // ✅ Validar extensão (whitelist)
    const ext = path.extname(file.originalname || "").toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      logger.warn({ ext }, "Extension rejected");
      return cb(new Error(`Extension not allowed: ${ext}`));
    }
    cb(null, true);
  },
  limits: {
    fileSize: 40 * 1024 * 1024 // 40MB max
  }
});

app.use(express.json({ limit: "1mb" }));
app.use(cors(corsOptions));
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
  try {
    const files = Array.isArray(req.files) ? req.files : [];
    const picked =
      files.find((f) => f && (f.fieldname === "audio" || f.fieldname === "file")) || files[0];
    if (!picked) {
      return res.status(400).json({ ok: false, error: "audio_file_required" });
    }

    // ✅ Validar que o arquivo está em uploadDir seguro (sem path traversal)
    const resolvedPath = path.resolve(picked.path);
    const resolvedUploadDir = path.resolve(uploadDir);
    if (!resolvedPath.startsWith(resolvedUploadDir)) {
      logger.error({ filePath: picked.path, uploadDir }, "Path traversal attempt detected");
      return res.status(403).json({ ok: false, error: "invalid_file_path" });
    }

    const clientJobId = String(req.body?.clientJobId || uuidv4());
    const job = await sttQueue.add("transcribe", {
      jobId: clientJobId,
      filePath: resolvedPath, // ✅ Usar resolved path
      mimeType: picked.mimetype || "application/octet-stream",
      originalName: path.basename(picked.originalname || "audio.bin"), // ✅ Sanitizar
      languageHint: req.body?.language || "pt"
    });

    res.status(202).json({
      ok: true,
      jobId: job.id,
      status: "queued"
    });
  } catch (err) {
    logger.error({ err }, "Error enqueueing STT job");
    res.status(500).json({ ok: false, error: "internal_error" });
  }
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
