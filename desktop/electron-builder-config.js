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

/** Configuração principal — APENAS NSIS, sem ZIP, sem portable, sem MSI */
module.exports = {
  appId: "com.syntexa.desktop",
  productName: "Syntexa AI",
  copyright: "Copyright 2026 SyntexaBR",
  buildVersion: pkg.version,

  directories: {
    output: "release",
    buildResources: "build",
  },

  files: buildFiles(),
  extraResources: buildExtraResources(),

  asar: true,
  asarUnpack: [
    "backend/**/*",
    "runtime/**/*",
  ],
  compression: "normal",

  afterPack: path.join(__dirname, "scripts", "after-pack.js"),

  // ── WINDOWS — MSI (instalador nativo REAL que nunca abre com WinRAR) ─────
  win: (function () {
    const cfg = {
      target: [
        { target: "msi", arch: ["x64"] },
      ],
      icon: path.join(__dirname, "build", "icon.ico"),
      artifactName: "SyntexaAI-Setup-${version}.${ext}",
      publisherName: "SyntexaBR",
      verifyUpdateCodeSignature: false,
      requestedExecutionLevel: "requireAdministrator",
      rfc3161TimeStampServer: "http://timestamp.digicert.com",
      timeStampServer: "http://timestamp.digicert.com",
    };
    const certPass = process.env.SYNTEXA_CERT_PASS || "";
    let certFile = process.env.SYNTEXA_CERT_FILE || "";
    if (!certFile || !fs.existsSync(certFile)) {
      const candidates = [
        path.join(__dirname, "..", "Syntexa-codesign-new.pfx"),
        path.join(__dirname, "..", "Syntexa-codesign.pfx"),
        path.join(__dirname, "..", "syntexa.pfx"),
      ];
      certFile = candidates.find(function(c) { return fs.existsSync(c); }) || "";
    }
    if (certFile && certPass) {
      cfg.certificateFile = certFile;
      cfg.certificatePassword = certPass;
      console.info("[electron-builder] Certificado: " + certFile);
    } else {
      console.warn("[electron-builder] Sem certificado — build unsigned.");
    }
    return cfg;
  })(),

  // ── NSIS installer gráfico profissional (como Cursor/Claude) ────────
  nsis: {
    oneClick: false,
    allowElevation: true,
    allowToChangeInstallationDirectory: true,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    shortcutName: "Syntexa AI",
    installerIcon: path.join(__dirname, "build", "icon.ico"),
    uninstallerIcon: path.join(__dirname, "build", "icon.ico"),
    installerHeaderIcon: path.join(__dirname, "build", "icon.ico"),
    artifactName: "SyntexaAI-Setup-${version}.${ext}",
    uninstallDisplayName: "Syntexa AI",
    deleteAppDataOnUninstall: false,
    multiLanguageInstaller: true,
    displayLanguageSelector: false,
    language: "1046",
    license: path.join(__dirname, "build", "LICENSE.txt"),
    include: path.join(__dirname, "scripts", "nsis-installer.nsh"),
  },

  // ── Linux — AppImage nativo como VSCode/Cursor ─────────────────────
  linux: {
    target: [
      { target: "AppImage", arch: ["x64"] },
      { target: "deb", arch: ["x64"] },
    ],
    category: "Utility",
    artifactName: "SyntexaAI-${version}-linux-x64.${ext}",
    icon: path.join(__dirname, "build", "icon.png"),
    desktop: {
      Name: "Syntexa AI",
      Comment: "Inteligência Artificial Soberana",
      Keywords: "ai;chat;assistant;",
    },
  },

  // ── macOS ─────────────────────────────────────────────────
  mac: {
    target: [{ target: "dmg", arch: ["x64"] }],
    category: "public.app-category.productivity",
    artifactName: "SyntexaAI-${version}-macos.${ext}",
  },

  publish: null,
};
