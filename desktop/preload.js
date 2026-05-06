const { contextBridge, ipcRenderer } = require("electron");

function invoke(channel, payload) {
  return ipcRenderer.invoke(channel, payload);
}

contextBridge.exposeInMainWorld("syntexaDesktop", {
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
});
