/**
 * Gera build/icon.ico a partir de LOGOTIPO.png
 * Usa jimp (v1 ESM wrapped) + png-to-ico
 */
const fs = require("fs");
const path = require("path");

async function main() {
  const { Jimp } = require("jimp");
  const { default: pngToIco } = require("png-to-ico");

  const src = path.join(__dirname, "..", "..", "LOGOTIPO.png");
  const outDir = path.join(__dirname, "..", "build");
  const outPng = path.join(outDir, "icon-256.png");
  const outIco = path.join(outDir, "icon.ico");

  fs.mkdirSync(outDir, { recursive: true });

  const img = await Jimp.read(src);
  const w = img.bitmap.width;
  const h = img.bitmap.height;
  const size = Math.max(w, h);

  // Cria fundo quadrado cor Syntexa #0f172a
  const bg = new Jimp({ width: size, height: size, color: 0x0f172aff });
  bg.composite(img, Math.floor((size - w) / 2), Math.floor((size - h) / 2));
  bg.resize({ w: 256, h: 256 });

  const pngBuf = await bg.getBuffer("image/png");
  fs.writeFileSync(outPng, pngBuf);
  console.log("PNG 256x256 gerado:", outPng);

  const icoBuf = await pngToIco(outPng);
  fs.writeFileSync(outIco, icoBuf);
  console.log("icon.ico gerado:", outIco, "(" + icoBuf.length + " bytes)");
}

main().catch(e => { console.error("ERRO:", e.message); process.exit(1); });
