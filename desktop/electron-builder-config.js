/**
 * SYNTEXA DESKTOP — Electron Builder Enterprise Configuration V45
 * Builds reais para Windows (NSIS/MSI/Portable) e Linux (AppImage/deb/tar.gz)
 */
const path = require("path");
const fs = require("fs");

const pkg = require("./package.json");

// Detecta se runtime Python existe para incluir no pacote
const runtimeDir = path.join(__dirname, "runtime");
const hasRuntime = fs.existsSync(runtimeDir);
const frontendDist = path.join(__dirname, "..", "frontend", "dist");
const hasFrontend = fs.existsSync(frontendDist);

// ── SYMLINK-SAFE BUILD HELPERS ───────────────────────────
/**
 * Remove symlinks de um diretório e os substitui por cópias físicas.
 * Compatível com Windows sem Developer Mode.
 */
function unlinkSymlinksRecursively(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isSymbolicLink()) {
      const target = fs.readlinkSync(full);
      const resolved = path.resolve(path.dirname(full), target);
      fs.unlinkSync(full);
      if (fs.existsSync(resolved)) {
        if (fs.statSync(resolved).isDirectory()) {
          fs.mkdirSync(full, { recursive: true });
          copyDirRecursive(resolved, full);
        } else {
          fs.copyFileSync(resolved, full);
        }
      }
    } else if (entry.isDirectory()) {
      unlinkSymlinksRecursively(full);
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

function ensureSymlinkSafe() {
  const dirsToClean = [runtimeDir, path.join(__dirname, "backend")];
  for (const d of dirsToClean) {
    if (fs.existsSync(d)) {
      try { unlinkSymlinksRecursively(d); } catch (_) {}
    }
  }
}

// Executa antes do build
ensureSymlinkSafe();

/** Gera lista de arquivos a empacotar com validação de existência */
function buildFiles() {
  const files = [
    "main.js",
    "preload.js",
    "build/**/*",
    "!**/*.map",
    "!**/node_modules/**/*.map",
  ];

  if (hasFrontend) {
    files.push("frontend/dist/**/*");
  }

  if (hasRuntime) {
    files.push("runtime/**/*");
  } else {
    console.warn("[electron-builder] WARNING: runtime/ não encontrado. Build será incompleto.");
  }

  // Backend embutido
  const backendDir = path.join(__dirname, "backend");
  if (fs.existsSync(backendDir)) {
    files.push("backend/**/*");
  }

  return files;
}

/** Recursos extras: vereda_ai e llm-quantum */
function buildExtraResources() {
  const extras = [];
  const veredaAi = path.join(__dirname, "..", "vereda_ai");
  const llmQuantum = path.join(__dirname, "..", "llm-quantum");

  if (fs.existsSync(veredaAi)) {
    extras.push({
      from: "../vereda_ai",
      to: "vereda_ai",
      filter: ["**/*", "!**/__pycache__", "!**/*.pyc", "!**/.git"],
    });
  }

  if (fs.existsSync(llmQuantum)) {
    extras.push({
      from: "../llm-quantum",
      to: "llm-quantum",
      filter: ["**/*", "!**/__pycache__", "!**/*.pyc", "!**/.git"],
    });
  }

  // Model checkpoints (se existirem)
  const checkpoints = path.join(__dirname, "..", "checkpoints");
  if (fs.existsSync(checkpoints)) {
    extras.push({
      from: "../checkpoints",
      to: "checkpoints",
      filter: ["**/*", "!**/__pycache__", "!**/*.pyc"],
    });
  }

  return extras;
}

/** Configuração principal */
module.exports = {
  appId: "br.com.syntexabr.desktop",
  productName: "Syntexa AI",
  copyright: "Copyright 2026 SyntexaBR",
  buildVersion: pkg.version,
  directories: {
    output: "dist",
    buildResources: "build",
  },
  files: buildFiles(),
  extraResources: buildExtraResources(),
  asar: true,
  asarUnpack: [
    "backend/**/*",
    "runtime/**/*",
    "vereda_ai/**/*",
    "llm-quantum/**/*",
    "checkpoints/**/*",
  ],
  compression: "maximum",

  // macOS (mantido para compatibilidade)
  mac: {
    target: ["dmg", "zip"],
    category: "public.app-category.productivity",
    artifactName: "SyntexaAI-${version}-macos-universal.${ext}",
  },

  // Linux Enterprise
  linux: {
    target: [
      { target: "AppImage", arch: ["x64"] },
      { target: "deb", arch: ["x64"] },
      { target: "tar.gz", arch: ["x64"] },
    ],
    category: "Office;Utility;ArtificialIntelligence",
    synopsis: "Syntexa AI — Foundation Model Soberana Desktop (Offline)",
    description:
      "Runtime neural soberano com Foundation Model 70B, multimodal (TTS/STT/OCR/Vision), " +
      "QPanda3 quantum layer, e chat cinematográfico. Funciona 100% offline.",
    maintainer: "SyntexaBR <contato@syntexabr.com.br>",
    vendor: "SyntexaBR",
    artifactName: "SyntexaAI-${version}-linux-${arch}.${ext}",
    desktop: {
      Name: "Syntexa AI",
      Comment: "Foundation Model Soberana Desktop",
      Categories: "Office;Utility;ArtificialIntelligence;",
      Keywords: "ai;llm;chat;multimodal;offline;soberano;",
      StartupNotify: "true",
      Terminal: "false",
    },
  },

  // Post-pack para todas as plataformas (symlink-safe, assinatura, permissões)
  afterPack: path.join(__dirname, "scripts", "after-pack.js"),

  // Windows Enterprise
  win: (function () {
    const cfg = {
      target: [
        { target: "nsis", arch: ["x64"] },
        { target: "portable", arch: ["x64"] },
        { target: "msi", arch: ["x64"] },
      ],
      artifactName: "SyntexaAI-${version}-win-${arch}.${ext}",
      publisherName: "SyntexaBR",
      verifyUpdateCodeSignature: false,
      requestedExecutionLevel: "asInvoker",
      // Hardened signing
      rfc3161TimeStampServer: "http://timestamp.digicert.com",
      timeStampServer: "http://timestamp.digicert.com",
      signAndEditExecutable: true,
      signDlls: true,
    };
    const certFile = process.env.SYNTEXA_CERT_FILE;
    if (certFile && fs.existsSync(certFile)) {
      cfg.certificateFile = certFile;
      cfg.certificatePassword = process.env.SYNTEXA_CERT_PASS || "";
    } else {
      // Sem certificado: gera unsigned mas com manifesto de integridade
      console.warn("[electron-builder] SYNTEXA_CERT_FILE não definido. Build será unsigned (SmartScreen pode alertar).");
    }
    return cfg;
  })(),

  // NSIS Installer
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    shortcutName: "Syntexa AI",
    installerLanguages: ["pt-BR", "en"],
    language: "1046",
    artifactName: "SyntexaAI-${version}-Setup.${ext}",
    // Uninstall display name
    uninstallDisplayName: "Syntexa AI Foundation Model",
    // Remove previous version antes de instalar
    deleteAppDataOnUninstall: false,
    // Include custom installer script
    include: path.join(__dirname, "scripts", "nsis-custom.nsh"),
    // Mensagens do instalador
    displayLanguageSelector: true,
    multiLanguageInstaller: true,
    license: path.join(__dirname, "build", "LICENSE.txt"),
  },

  // Portable
  portable: {
    artifactName: "SyntexaAI-${version}-Portable.${ext}",
    // Request execution level
    requestExecutionLevel: "user",
  },

  // MSI
  msi: {
    artifactName: "SyntexaAI-${version}-Installer.${ext}",
    // Upgrade code para updates via MSI
    upgradeCode: "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}",
    // Run after install
    runAfterFinish: true,
    // Create desktop shortcut via MSI
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
  },

  publish: null,
};
