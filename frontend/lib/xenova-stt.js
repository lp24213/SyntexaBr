/**
 * STT no navegador — Whisper via @xenova/transformers (ONNX).
 * Sem Azure, sem API externa de transcrição: modelo Xenova/whisper-small (Hugging Face CDN na 1ª carga).
 */

const XENOVA_MODEL = "Xenova/whisper-small";

let pipelinePromise = null;
let loadProgressCb = null;

export function setXenovaSttProgressCallback(fn) {
  loadProgressCb = typeof fn === "function" ? fn : null;
}

function emitProgress(msg) {
  if (loadProgressCb) loadProgressCb(String(msg || ""));
}

function extractText(result) {
  if (!result) return "";
  if (typeof result === "string") return result.trim();
  if (typeof result.text === "string") return result.text.trim();
  if (Array.isArray(result) && result[0] && result[0].text) {
    return String(result[0].text).trim();
  }
  if (Array.isArray(result.chunks)) {
    return result.chunks
      .map(function (c) {
        return (c && c.text) || "";
      })
      .join(" ")
      .trim();
  }
  return "";
}

async function getTranscriber() {
  if (typeof window === "undefined") {
    throw new Error("Xenova STT só roda no navegador.");
  }
  if (!pipelinePromise) {
    pipelinePromise = (async function () {
      emitProgress("Carregando Whisper (Xenova) no navegador…");
      const { pipeline, env } = await import("@xenova/transformers");
      env.allowLocalModels = false;
      env.allowRemoteModels = true;
      if (env.backends && env.backends.onnx && env.backends.onnx.wasm) {
        env.backends.onnx.wasm.numThreads = Math.min(
          4,
          typeof navigator !== "undefined" && navigator.hardwareConcurrency
            ? navigator.hardwareConcurrency
            : 2
        );
      }
      const transcriber = await pipeline("automatic-speech-recognition", XENOVA_MODEL, {
        quantized: true,
        progress_callback: function (data) {
          if (!data || typeof data !== "object") return;
          if (data.status === "progress" && data.file) {
            var pct =
              data.progress != null && data.total
                ? Math.round((100 * data.progress) / data.total)
                : null;
            emitProgress(
              pct != null
                ? "Baixando modelo: " + data.file + " (" + pct + "%)"
                : "Baixando modelo: " + data.file
            );
          } else if (data.status === "done" && data.file) {
            emitProgress("Modelo pronto: " + data.file);
          }
        },
      });
      emitProgress("");
      return transcriber;
    })().catch(function (err) {
      pipelinePromise = null;
      throw err;
    });
  }
  return pipelinePromise;
}

/**
 * Transcreve Blob/File de áudio gravado pelo MediaRecorder.
 * @param {Blob} blob
 * @param {{ language?: string }} [opts]
 * @returns {Promise<string>}
 */
export async function transcribeWithXenova(blob, opts) {
  if (!blob || blob.size < 256) {
    throw new Error("Gravação muito curta. Fale por mais tempo e tente de novo.");
  }
  const transcriber = await getTranscriber();
  const url = URL.createObjectURL(blob);
  try {
    emitProgress("Transcrevendo áudio…");
    const language = (opts && opts.language) || "portuguese";
    const out = await transcriber(url, {
      language: language,
      task: "transcribe",
      chunk_length_s: 30,
      stride_length_s: 5,
    });
    const text = extractText(out);
    emitProgress("");
    if (!text) {
      throw new Error("Transcrição vazia. Fale mais perto do microfone e tente de novo.");
    }
    return text;
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function getXenovaModelId() {
  return XENOVA_MODEL;
}

export default {
  transcribeWithXenova,
  setXenovaSttProgressCallback,
  getXenovaModelId,
};
