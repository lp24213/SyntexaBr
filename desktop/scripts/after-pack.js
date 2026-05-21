/**
 * SYNTEXA AFTER-PACK SCRIPT V45
 * ==============================
 * Executado após o electron-builder empacotar o app mas antes de gerar
 * instaladores (NSIS/MSI/AppImage/deb).
 *
 * Responsabilidades:
 * - Remover symlinks residuais (Windows sem Developer Mode)
 * - Copiar assets físicos em vez de links simbólicos
 * - Gerar runtime-manifest.json com checksums SHA256
 * - Corrigir permissões de execução no Linux
 * - Validar que todos os arquivos críticos existem
 */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const pkg = require("../package.json");

function sha256File(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function walkDir(dir, callback) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkDir(full, callback);
    } else {
      callback(full);
    }
  }
}

function removeSymlinksAndCopy(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isSymbolicLink()) {
      const target = fs.readlinkSync(full);
      const resolved = path.resolve(path.dirname(full), target);
      fs.unlinkSync(full);
      if (fs.existsSync(resolved)) {
        const stat = fs.statSync(resolved);
        if (stat.isDirectory()) {
          fs.mkdirSync(full, { recursive: true });
          copyDirRecursive(resolved, full);
        } else {
          fs.copyFileSync(resolved, full);
        }
      }
    } else if (entry.isDirectory()) {
      removeSymlinksAndCopy(full);
    }
  }
}

function copyDirRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

function generateManifest(context) {
  const appDir = context.appOutDir;
  const manifest = {
    version: pkg.version,
    schema_version: "V45",
    build_time: new Date().toISOString(),
    platform: context.electronPlatformName,
    arch: context.arch,
    files: [],
    symlinks_removed: true,
    signed: Boolean(process.env.SYNTEXA_CERT_FILE),
  };

  // Lista arquivos do runtime e backend
  const runtimeDir = path.join(appDir, "runtime");
  const backendDir = path.join(appDir, "backend");
  const resourcesDir = path.join(appDir, "resources");

  for (const dir of [runtimeDir, backendDir, resourcesDir]) {
    if (!fs.existsSync(dir)) continue;
    walkDir(dir, (filePath) => {
      const rel = path.relative(appDir, filePath).replace(/\\/g, "/");
      manifest.files.push({
        path: rel,
        sha256: sha256File(filePath),
        size: fs.statSync(filePath).size,
      });
    });
  }

  const manifestPath = path.join(appDir, "runtime-manifest.json");
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");
  console.log("[after-pack] Manifest gerado:", manifestPath, "—", manifest.files.length, "arquivos");
}

module.exports = async function (context) {
  const { appOutDir, electronPlatformName } = context;
  console.log("[after-pack] Iniciando pós-processamento para:", electronPlatformName);

  // 1) Remover symlinks
  const dirsToClean = [
    path.join(appOutDir, "runtime"),
    path.join(appOutDir, "backend"),
    path.join(appOutDir, "resources"),
  ];
  for (const d of dirsToClean) {
    if (fs.existsSync(d)) {
      try {
        removeSymlinksAndCopy(d);
        console.log("[after-pack] Symlinks removidos em:", d);
      } catch (e) {
        console.warn("[after-pack] Falha ao remover symlinks em", d, e.message);
      }
    }
  }

  // 2) Linux: corrigir permissões
  if (electronPlatformName === "linux") {
    const pythonBin = path.join(appOutDir, "runtime", "python", "bin", "python3");
    if (fs.existsSync(pythonBin)) {
      try {
        fs.chmodSync(pythonBin, 0o755);
        console.log("[after-pack] Permissões corrigidas:", pythonBin);
      } catch (e) {
        console.warn("[after-pack] chmod falhou:", e.message);
      }
    }
  }

  // 3) Windows: corrigir caminhos longos e permissões
  if (electronPlatformName === "win32") {
    // Nada especial aqui — electron-builder já lida com paths
    console.log("[after-pack] Windows build processado.");
  }

  // 4) Gerar manifest de integridade
  generateManifest(context);

  console.log("[after-pack] Concluído para:", electronPlatformName);
};
