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
  // Windows
  {
    test: (f) => /^SyntexaAI-.*-Setup\.exe$/i.test(f),
    dest: `SyntexaAI-Setup-${ver}.exe`,
  },
  {
    test: (f) => /^SyntexaAI-.*-Installer\.msi$/i.test(f),
    dest: `SyntexaAI-Installer-${ver}.msi`,
  },
  {
    test: (f) => /^SyntexaAI-.*-Portable\.exe$/i.test(f),
    dest: `SyntexaAI-Portable-${ver}.exe`,
  },
  // macOS
  { test: (f) => f.endsWith(".dmg"), dest: `SyntexaAI-macos-universal-${ver}.dmg` },
  // Linux
  { test: (f) => /^SyntexaAI-.*\.AppImage$/i.test(f), dest: `SyntexaAI-linux-x64-${ver}.AppImage` },
  { test: (f) => /^SyntexaAI-.*\.deb$/i.test(f), dest: `SyntexaAI-linux-x64-${ver}.deb` },
  { test: (f) => f.endsWith(".tar.gz"), dest: `SyntexaAI-linux-x64-${ver}.tar.gz` },
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

// Copia também checksums e manifestos
for (const extra of ["SHA256SUMS.txt", `syntexa-manifest-${ver}.json`]) {
  const src = path.join(distDir, extra);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, path.join(outDir, extra));
    console.log("[copy-artifacts]", extra, "->", outDir);
  }
}

// Verifica artefatos mínimos por plataforma — PROIBIDO builds vazios
const platform = process.platform;
const windowsArtifacts = [`SyntexaAI-Setup-${ver}.exe`, `SyntexaAI-Installer-${ver}.msi`, `SyntexaAI-Portable-${ver}.exe`];
const linuxArtifacts = [`SyntexaAI-linux-x64-${ver}.AppImage`, `SyntexaAI-linux-x64-${ver}.deb`, `SyntexaAI-linux-x64-${ver}.tar.gz`];
const macosArtifacts = [`SyntexaAI-macos-universal-${ver}.dmg`];

let foundAny = 0;
let missing = [];
for (const name of [...windowsArtifacts, ...linuxArtifacts, ...macosArtifacts]) {
  const p = path.join(outDir, name);
  if (fs.existsSync(p)) {
    foundAny++;
  } else {
    missing.push(name);
  }
}
if (foundAny === 0) {
  console.error("[copy-artifacts] CRÍTICO: Nenhum artefato encontrado em", outDir);
  process.exit(1);
}
// Build parcial só é erro se a plataforma atual não gerou NADA
const currentPlatformArtifacts = platform === "win32" ? windowsArtifacts : platform === "linux" ? linuxArtifacts : platform === "darwin" ? macosArtifacts : [];
const currentPlatformFound = currentPlatformArtifacts.filter((n) => fs.existsSync(path.join(outDir, n)));
if (currentPlatformArtifacts.length > 0 && currentPlatformFound.length === 0) {
  console.error("[copy-artifacts] CRÍTICO: Build parcial detectado. Nenhum artefato da plataforma atual encontrado.");
  console.error("[copy-artifacts] PROIBIDO mascarar build incompleto como sucesso.");
  process.exit(1);
}
console.log(`[copy-artifacts] ${foundAny} artefato(s) presente(s) em ${outDir}`);
