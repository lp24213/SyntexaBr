const { contextBridge, ipcRenderer } = require("electron");

function invoke(channel, payload) {
  return ipcRenderer.invoke(channel, payload);
}

// ── EXPOSIÇÃO UNIFICADA DA API DESKTOP ────────────────────
contextBridge.exposeInMainWorld("__DESKTOP_MODE__", true);
contextBridge.exposeInMainWorld("__DESKTOP_PORT__", 34560);

contextBridge.exposeInMainWorld("desktopAPI", {
  // Flags de modo
  isDesktopMode: true,
  appVersion: require("./package.json").version,

  // FileSystem seguro
  openFile: function () {
    return invoke("desktop:open-file");
  },
  openFolder: function () {
    return invoke("desktop:open-folder");
  },
  listDirectory: function (targetPath) {
    return invoke("desktop:list-directory", { targetPath });
  },
  readFile: function (targetPath) {
    return invoke("desktop:read-file", { targetPath });
  },
  writeFile: function (targetPath, content) {
    return invoke("desktop:write-file", { targetPath, content });
  },
  createFile: function (targetPath, content) {
    return invoke("desktop:create-file", { targetPath, content });
  },
  getWorkspaceRoot: function () {
    return invoke("desktop:get-workspace-root");
  },
  revealInExplorer: function (targetPath) {
    return invoke("desktop:reveal-in-explorer", { targetPath });
  },

  // Backend status
  backendStatus: function () {
    return invoke("desktop:backend-status");
  },

  // Boot diagnostic (fail-fast)
  bootDiagnostic: function () {
    return invoke("desktop:boot-diagnostic");
  },

  // Multimodal upload (filePath → base64)
  multimodalUpload: function (filePath, kind) {
    return invoke("desktop:multimodal-upload", { filePath, kind });
  },

  // TTS
  ttsSynthesize: function (text, outputPath) {
    return invoke("desktop:tts-synthesize", { text, outputPath });
  },

  // Export conversation
  exportConversation: function (content, format, defaultName) {
    return invoke("desktop:export-conversation", { content, format, defaultName });
  },

  // Integrity / manifest
  getRuntimeManifest: function () {
    return invoke("desktop:runtime-manifest");
  },
  verifyIntegrity: function () {
    return invoke("desktop:verify-integrity");
  },

  // Eventos
  onSelection: function (listener) {
    if (typeof listener !== "function") return function () {};
    var wrapped = function (_event, payload) {
      listener(payload);
    };
    ipcRenderer.on("desktop:selected-path", wrapped);
    return function () {
      ipcRenderer.removeListener("desktop:selected-path", wrapped);
    };
  },

  onBackendReady: function (listener) {
    if (typeof listener !== "function") return function () {};
    var wrapped = function (_event, payload) {
      listener(payload);
    };
    ipcRenderer.on("desktop:backend-ready", wrapped);
    return function () {
      ipcRenderer.removeListener("desktop:backend-ready", wrapped);
    };
  },

  onBootFailure: function (listener) {
    if (typeof listener !== "function") return function () {};
    var wrapped = function (_event, payload) {
      listener(payload);
    };
    ipcRenderer.on("desktop:boot-failure", wrapped);
    return function () {
      ipcRenderer.removeListener("desktop:boot-failure", wrapped);
    };
  },
});

// Alias legado para compatibilidade
contextBridge.exposeInMainWorld("syntexaDesktop", {
  openFile: function () { return invoke("desktop:open-file"); },
  openFolder: function () { return invoke("desktop:open-folder"); },
  listDirectory: function (targetPath) { return invoke("desktop:list-directory", { targetPath }); },
  readFile: function (targetPath) { return invoke("desktop:read-file", { targetPath }); },
  writeFile: function (targetPath, content) { return invoke("desktop:write-file", { targetPath, content }); },
  createFile: function (targetPath, content) { return invoke("desktop:create-file", { targetPath, content }); },
  getWorkspaceRoot: function () { return invoke("desktop:get-workspace-root"); },
  revealInExplorer: function (targetPath) { return invoke("desktop:reveal-in-explorer", { targetPath }); },
  onSelection: function (listener) {
    if (typeof listener !== "function") return function () {};
    var wrapped = function (_event, payload) { listener(payload); };
    ipcRenderer.on("desktop:selected-path", wrapped);
    return function () { ipcRenderer.removeListener("desktop:selected-path", wrapped); };
  },
});
