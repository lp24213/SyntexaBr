/**
 * Copia instaladores gerados em desktop/dist para vereda_backend/static/desktop/
 * (servidos pela API em /v1/desktop/binary/*).
 */
const fs = require("fs");
const path = require("path");

const pkg = require("./package.json");
const ver = pkg.version;
const distDir = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(__dirname, "dist");
const outDir = path.join(__dirname, "..", "vereda_backend", "static", "desktop");

if (!fs.existsSync(distDir)) {
  console.error("[copy-artifacts] Pasta de build ausente:", distDir);
  process.exit(1);
}

const files = fs.readdirSync(distDir).filter((f) => !fs.statSync(path.join(distDir, f)).isDirectory());
if (files.length === 0) {
  console.error("[copy-artifacts] Pasta de build vazia:", distDir);
  process.exit(1);
}

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const rules = [
  {
    test: (f) => /^SyntexaAI-Setup-.*\.exe$/i.test(f) || (/\.exe$/i.test(f) && /setup/i.test(f)),
    dest: `SyntexaAI-Setup-${ver}.exe`,
  },
  { test: (f) => f.endsWith(".dmg"), dest: "SyntexaAI-macos-universal.dmg" },
  { test: (f) => f.endsWith(".tar.gz"), dest: "SyntexaAI-linux-x64.tar.gz" },
];

const used = new Set();
let copied = 0;
for (const rule of rules) {
  const hit = files.find((f) => rule.test(f) && !used.has(f));
  if (!hit) {
    console.warn("[copy-artifacts] (aviso) Não encontrado para:", rule.dest);
    continue;
  }
  used.add(hit);
  const src = path.join(distDir, hit);
  const dest = path.join(outDir, rule.dest);
  fs.copyFileSync(src, dest);
  copied += 1;
  console.log("[copy-artifacts]", hit, "->", path.relative(path.join(__dirname, ".."), dest));
}

if (copied === 0) {
  console.error("[copy-artifacts] Nenhum artefato reconhecido em dist/. Verifique electron-builder.");
  process.exit(1);
}

const mustExist = [`SyntexaAI-Setup-${ver}.exe`, "SyntexaAI-linux-x64.tar.gz"];
for (const name of mustExist) {
  const p = path.join(outDir, name);
  if (!fs.existsSync(p)) {
    console.error("[copy-artifacts] Obrigatório após build:", name);
    process.exit(1);
  }
}
