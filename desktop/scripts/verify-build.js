/**
 * SYNTEXA DESKTOP — Build Verification Script V45
 * Verifica se o build gerou todos os artefatos obrigatórios
 * com checksums válidos e sem arquivos corrompidos.
 */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const pkg = require("../package.json");
const ver = pkg.version;

const distDir = process.argv[2] ? path.resolve(process.argv[2]) : path.join(__dirname, "..", "dist");
const runtimeDir = path.join(__dirname, "..", "runtime");
const manifestPath = path.join(__dirname, "..", "runtime-manifest.json");

let exitCode = 0;

function fail(msg) {
  console.error("[VERIFY] FAIL:", msg);
  exitCode = 1;
}

function ok(msg) {
  console.log("[VERIFY]  OK:", msg);
}

function getSha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
console.log("  SYNTEXA DESKTOP BUILD VERIFICATION V45");
console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

// 1) Verifica dist/
if (!fs.existsSync(distDir)) {
  fail(`Pasta dist/ não encontrada: ${distDir}`);
} else {
  ok(`dist/ encontrado: ${distDir}`);
}

const files = fs.readdirSync(distDir).filter((f) => !fs.statSync(path.join(distDir, f)).isDirectory());
if (files.length === 0) {
  fail("dist/ está vazio. Nenhum artefato gerado.");
} else {
  ok(`${files.length} artefatos em dist/`);
}

// 2) Verifica artefatos obrigatórios por plataforma
const platform = process.platform;
const requiredPatterns = [];

if (platform === "win32") {
  requiredPatterns.push(/\.exe$/i);
} else if (platform === "linux") {
  requiredPatterns.push(/\.AppImage$/i, /\.deb$/i, /\.tar\.gz$/i);
}

for (const pat of requiredPatterns) {
  const found = files.some((f) => pat.test(f));
  if (!found) {
    fail(`Artefato obrigatório não encontrado (padrão: ${pat.source})`);
  } else {
    ok(`Artefato obrigatório encontrado: ${pat.source}`);
  }
}

// 3) Verifica SHA256SUMS
const checksumsPath = path.join(distDir, "SHA256SUMS.txt");
if (fs.existsSync(checksumsPath)) {
  ok("SHA256SUMS.txt presente");
  // Verifica integridade
  const lines = fs.readFileSync(checksumsPath, "utf8").trim().split("\n");
  for (const line of lines) {
    const parts = line.trim().split(/\s+/);
    if (parts.length !== 2) continue;
    const [expectedHash, fname] = parts;
    const fpath = path.join(distDir, fname);
    if (!fs.existsSync(fpath)) {
      fail(`Arquivo listado em SHA256SUMS ausente: ${fname}`);
      continue;
    }
    const actualHash = getSha256(fpath);
    if (actualHash !== expectedHash.toLowerCase()) {
      fail(`Checksum inválido: ${fname}`);
    }
  }
  ok("Todos os checksums verificados");
} else {
  fail("SHA256SUMS.txt ausente — builds não estão verificáveis");
}

// 4) Verifica manifesto
const signedManifest = path.join(distDir, "syntexa-manifest-v45.json");
if (fs.existsSync(signedManifest)) {
  ok("syntexa-manifest-v45.json presente");
} else {
  fail("syntexa-manifest-v45.json ausente");
}

// 5) Verifica runtime/ (para builds dev)
if (fs.existsSync(runtimeDir)) {
  ok("runtime/ presente");
  if (fs.existsSync(manifestPath)) {
    ok("runtime-manifest.json presente");
    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
      const files_ = manifest.files || [];
      let missing = 0;
      let mismatch = 0;
      for (const entry of files_) {
        const fpath = path.join(runtimeDir, entry.path.replace(/\//g, path.sep));
        if (!fs.existsSync(fpath)) {
          missing++;
        } else {
          const hash = getSha256(fpath);
          if (hash !== entry.sha256) mismatch++;
        }
      }
      if (missing > 0) fail(`${missing} arquivos do runtime ausentes`);
      if (mismatch > 0) fail(`${mismatch} arquivos do runtime com checksum inválido`);
      if (missing === 0 && mismatch === 0) ok("Runtime integrity: 100% verificado");
    } catch (e) {
      fail(`Erro ao verificar manifesto: ${e.message}`);
    }
  } else {
    fail("runtime-manifest.json ausente — runtime não verificável");
  }
} else {
  console.warn("[VERIFY] WARN: runtime/ não encontrado (pode ser build de CI sem runtime empacotado)");
}

// 6) Tamanho mínimo dos artefatos (anti-build-vazio)
const minSizeMB = 5; // NSIS/MSI deve ter pelo menos alguns MB
for (const f of files) {
  const fpath = path.join(distDir, f);
  const sizeMB = fs.statSync(fpath).size / (1024 * 1024);
  if (sizeMB < minSizeMB && f.endsWith(".exe")) {
    fail(`Artefato suspeitamente pequeno: ${f} (${sizeMB.toFixed(2)} MB). Build pode estar incompleto.`);
  }
}

console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
if (exitCode === 0) {
  console.log("  VERIFICAÇÃO PASSOU — BUILD V45 OK");
} else {
  console.log("  VERIFICAÇÃO FALHOU — CORRIJA OS ERROS ACIMA");
}
console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
process.exit(exitCode);
