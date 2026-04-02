const fs = require("fs");
const path = require("path");

const distDir = path.join(__dirname, "dist");
const outDir = path.join(__dirname, "..", "frontend", "public", "download");

if (!fs.existsSync(distDir)) {
  console.warn("desktop/dist não existe. Rode npm run build antes.");
  process.exit(0);
}

const exes = fs.readdirSync(distDir).filter((f) => f.endsWith(".exe"));
if (exes.length === 0) {
  console.warn("Nenhum .exe em desktop/dist. Rode npm run build antes.");
  process.exit(0);
}

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

for (const name of exes) {
  const src = path.join(distDir, name);
  const dest = path.join(outDir, name);
  fs.copyFileSync(src, dest);
  console.log("Copiado:", name, "-> frontend/public/download/");
}
