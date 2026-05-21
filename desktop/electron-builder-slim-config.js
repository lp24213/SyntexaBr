/**
 * SYNTEXA DESKTOP — Slim Build Config V46
 *
 * Build leve para o download público em syntexabr.com.br/download:
 * apenas o shell Electron + launcher do webapp (~150 MB) — sem
 * checkpoints (695 MB), sem runtime Python, sem vereda_ai/llm-quantum.
 *
 * Para o build completo institucional/desktop offline, continue
 * usando `electron-builder-config.js`.
 */
const path = require("path");
const fs = require("fs");
const pkg = require("./package.json");

const buildResources = path.join(__dirname, "build");
if (!fs.existsSync(buildResources)) {
  fs.mkdirSync(buildResources, { recursive: true });
}
const licenseFile = path.join(buildResources, "LICENSE.txt");
if (!fs.existsSync(licenseFile)) {
  fs.writeFileSync(
    licenseFile,
    "Syntexa AI Desktop\n" +
      "Copyright (c) 2026 SyntexaBR. Todos os direitos reservados.\n" +
      "Uso conforme termos em https://syntexabr.com.br/termos.\n",
    "utf-8"
  );
}

module.exports = {
  appId: "br.com.syntexabr.desktop",
  productName: "Syntexa AI",
  copyright: "Copyright 2026 SyntexaBR",
  buildVersion: pkg.version,
  directories: {
    output: "dist",
    buildResources: "build",
  },
  // Empacota só o que importa para o shell rodar.
  files: [
    "main.js",
    "preload.js",
    "package.json",
    "!**/*.map",
    "!node_modules/**/*.map",
    "!**/__pycache__/**",
    "!**/*.pyc",
  ],
  // Nada de extraResources pesados nessa build.
  extraResources: [],
  asar: true,
  compression: "normal",

  // Linux: tar.gz é o que precisamos para o download direto.
  linux: {
    target: [{ target: "tar.gz", arch: ["x64"] }],
    category: "Office;Utility;",
    synopsis: "Syntexa AI Desktop",
    description: "Cliente desktop oficial do Syntexa AI (shell Electron).",
    maintainer: "SyntexaBR <contato@syntexabr.com.br>",
    vendor: "SyntexaBR",
    artifactName: "SyntexaAI-${version}-linux-${arch}.${ext}",
  },

  // Windows: NSIS Setup + Portable EXE.
  win: {
    target: [
      { target: "nsis", arch: ["x64"] },
      { target: "portable", arch: ["x64"] },
    ],
    artifactName: "SyntexaAI-${version}-win-${arch}.${ext}",
    publisherName: "SyntexaBR",
    requestedExecutionLevel: "asInvoker",
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    shortcutName: "Syntexa AI",
    artifactName: "SyntexaAI-${version}-Setup.${ext}",
    uninstallDisplayName: "Syntexa AI",
    deleteAppDataOnUninstall: false,
  },
  portable: {
    artifactName: "SyntexaAI-${version}-Portable.${ext}",
    requestExecutionLevel: "user",
  },

  publish: null,
};
