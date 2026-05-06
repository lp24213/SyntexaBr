/**
 * Geração de imagem no browser via Puter.js (sem API key no servidor).
 * Tenta resoluções altas (até ~4K) e reduz se o modelo/driver recusar.
 */
function blobToBase64Parts(blob) {
  return new Promise(function (resolve, reject) {
    var fr = new FileReader();
    fr.onload = function () {
      var dataUrl = fr.result;
      if (typeof dataUrl !== "string") {
        reject(new Error("Leitura inválida."));
        return;
      }
      var m = /^data:([^;]+);base64,(.*)$/s.exec(dataUrl);
      if (!m) {
        reject(new Error("Formato de imagem inválido."));
        return;
      }
      resolve({ mime: m[1], image_base64: m[2] });
    };
    fr.onerror = function () {
      reject(fr.error || new Error("Falha ao ler imagem."));
    };
    fr.readAsDataURL(blob);
  });
}

/** Ordem: maior primeiro (4K UHD → 2K → Full HD → sem forçar tamanho). */
var RES_STEPS = [
  { w: 3840, h: 2160 },
  { w: 2560, h: 1440 },
  { w: 1920, h: 1080 },
  { w: 1536, h: 1536 },
  null,
];

function getModel() {
  if (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_PUTER_IMAGE_MODEL) {
    return String(process.env.NEXT_PUBLIC_PUTER_IMAGE_MODEL).trim();
  }
  return "black-forest-labs/FLUX.1-schnell";
}

/**
 * @param {string} prompt
 * @returns {Promise<{ ok?: boolean, image_base64: string, mime: string, provider: string }>}
 */
export async function generateImageWithPuter(prompt) {
  if (typeof window === "undefined") {
    throw new Error("Puter só roda no navegador.");
  }
  var p = String(prompt || "")
    .trim()
    .slice(0, 4000);
  if (!p) {
    throw new Error("Prompt vazio.");
  }

  var puterMod = await import("@heyputer/puter.js");
  var puter = puterMod.default || puterMod.puter;
  if (!puter || !puter.ai || typeof puter.ai.txt2img !== "function") {
    throw new Error("Puter.js indisponível.");
  }

  var model = getModel();
  var lastErr = null;

  for (var i = 0; i < RES_STEPS.length; i++) {
    var dim = RES_STEPS[i];
    try {
      var opts = { model: model, prompt: p };
      if (dim) {
        opts.ratio = { w: dim.w, h: dim.h };
      }
      var img = await puter.ai.txt2img(opts);
      var src = img && (img.src || (typeof img.toString === "function" ? String(img.toString()) : ""));
      if (!src) {
        throw new Error("Resposta sem URL de imagem.");
      }
      var res = await fetch(src);
      if (!res.ok) {
        throw new Error("Falha ao obter bytes da imagem.");
      }
      var blob = await res.blob();
      var parts = await blobToBase64Parts(blob);
      return {
        ok: true,
        image_base64: parts.image_base64,
        mime: parts.mime.indexOf("png") !== -1 ? "image/png" : parts.mime.indexOf("jpeg") !== -1 ? "image/jpeg" : "image/png",
        provider: "puter",
      };
    } catch (e) {
      lastErr = e;
      continue;
    }
  }

  var msg =
    lastErr && typeof lastErr === "object" && lastErr.message
      ? String(lastErr.message)
      : lastErr instanceof Error
        ? lastErr.message
        : String(lastErr || "Puter falhou.");
  throw new Error(msg);
}

/**
 * Metadados da geração (prompt, mime, tamanho aproximado) para telemetria/histórico no cliente.
 * Não envia bytes — use upload dedicado se precisar persistir no servidor.
 */
export function describeGeneratedImageMeta(prompt, mime, base64Length) {
  return {
    prompt_preview: String(prompt || "").slice(0, 400),
    mime: mime || "image/png",
    base64_chars: typeof base64Length === "number" ? base64Length : 0,
    at: new Date().toISOString(),
    provider: "puter",
  };
}
