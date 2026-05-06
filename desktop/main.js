const { app, BrowserWindow, shell, dialog, Menu, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const fsp = require("fs/promises");

const APP_URL = "https://syntexabr.com.br";
const APP_USER_MODEL_ID = "br.com.syntexabr.desktop";
const iconPath = path.join(__dirname, "build", "icon.ico");
const preloadPath = path.join(__dirname, "preload.js");
const DESKTOP_SHORTCUT_NAME = "Syntexa AI.lnk";
const MAX_FILE_BYTES = 2 * 1024 * 1024;
let workspaceRoot = "";

function normalizeAbs(targetPath) {
  if (!targetPath || typeof targetPath !== "string") return "";
  const full = path.resolve(targetPath);
  return full;
}

function isInsideWorkspace(targetPath) {
  if (!workspaceRoot) return true;
  const normalized = normalizeAbs(targetPath);
  const root = normalizeAbs(workspaceRoot);
  if (!normalized || !root) return false;
  return normalized === root || normalized.startsWith(root + path.sep);
}

function ensureWorkspaceWritePermission(targetPath) {
  if (!isInsideWorkspace(targetPath)) {
    throw new Error("Operação permitida somente dentro da pasta aberta.");
  }
}

async function listDirectorySafe(targetPath) {
  const normalized = normalizeAbs(targetPath || workspaceRoot || app.getPath("documents"));
  if (!normalized) throw new Error("Caminho inválido.");
  const st = await fsp.stat(normalized);
  if (!st.isDirectory()) throw new Error("O caminho não é uma pasta.");
  const entries = await fsp.readdir(normalized, { withFileTypes: true });
  return entries
    .map((entry) => {
      const fullPath = path.join(normalized, entry.name);
      return {
        name: entry.name,
        path: fullPath,
        type: entry.isDirectory() ? "directory" : "file",
      };
    })
    .sort((a, b) => {
      if (a.type === b.type) return a.name.localeCompare(b.name);
      return a.type === "directory" ? -1 : 1;
    });
}

function emitSelectedPath(win, payload) {
  if (!win || win.isDestroyed()) return;
  win.webContents.send("desktop:selected-path", payload);
}

function applyAppMenu(win) {
  const template = [
    {
      label: "Arquivo",
      submenu: [
        {
          label: "Open Folder",
          accelerator: "CmdOrCtrl+Shift+O",
          click: async function () {
            if (!win || win.isDestroyed()) return;
            const out = await dialog.showOpenDialog(win, {
              properties: ["openDirectory"],
            });
            if (out.canceled || !out.filePaths || !out.filePaths[0]) return;
            workspaceRoot = out.filePaths[0];
            emitSelectedPath(win, { kind: "folder", path: workspaceRoot });
          },
        },
        {
          label: "Open File",
          accelerator: "CmdOrCtrl+O",
          click: async function () {
            if (!win || win.isDestroyed()) return;
            const out = await dialog.showOpenDialog(win, {
              properties: ["openFile"],
            });
            if (out.canceled || !out.filePaths || !out.filePaths[0]) return;
            emitSelectedPath(win, { kind: "file", path: out.filePaths[0] });
          },
        },
        { type: "separator" },
        {
          label: "Reveal Workspace in Explorer",
          click: function () {
            if (!workspaceRoot) return;
            shell.openPath(workspaceRoot);
          },
        },
        { type: "separator" },
        { role: "quit", label: "Sair" },
      ],
    },
    { role: "editMenu" },
    { role: "viewMenu" },
    { role: "windowMenu" },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

/** Primeira execução empacotada (Windows): atalho na área de trabalho apontando para este .exe. */
function ensureDesktopShortcut() {
  if (process.platform !== "win32" || !app.isPackaged) return;
  const flag = path.join(app.getPath("userData"), ".desktop-shortcut-created");
  if (fs.existsSync(flag)) return;
  try {
    const desktop = app.getPath("desktop");
    if (!desktop || !fs.existsSync(desktop)) return;
    const lnk = path.join(desktop, DESKTOP_SHORTCUT_NAME);
    const target = process.execPath;
    const cwd = path.dirname(target);
    const op = fs.existsSync(lnk) ? "update" : "create";
    const ok = shell.writeShortcutLink(lnk, op, {
      target,
      cwd,
      description: "Syntexa AI — cliente desktop",
      icon: target,
      iconIndex: 0,
      appUserModelId: APP_USER_MODEL_ID,
    });
    if (ok) fs.writeFileSync(flag, new Date().toISOString(), "utf8");
  } catch (_) {
    /* sem permissão / OneDrive: ignora */
  }
}

function createWindow() {
  const opts = {
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "Syntexa AI",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      spellcheck: true,
      preload: preloadPath,
    },
    show: false,
  };
  if (fs.existsSync(iconPath)) opts.icon = iconPath;

  const win = new BrowserWindow(opts);

  win.once("ready-to-show", () => win.show());
  applyAppMenu(win);

  // Abrir links externos no navegador
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http") && !url.startsWith(APP_URL)) {
      shell.openExternal(url);
      return { action: "deny" };
    }
    return { action: "allow" };
  });

  win.loadURL(APP_URL);

  [
    "desktop:open-folder",
    "desktop:open-file",
    "desktop:get-workspace-root",
    "desktop:list-directory",
    "desktop:read-file",
    "desktop:create-file",
    "desktop:write-file",
    "desktop:reveal-in-explorer",
  ].forEach(function (channel) {
    ipcMain.removeHandler(channel);
  });

  ipcMain.handle("desktop:open-folder", async function () {
    const out = await dialog.showOpenDialog(win, { properties: ["openDirectory"] });
    if (out.canceled || !out.filePaths || !out.filePaths[0]) return null;
    workspaceRoot = out.filePaths[0];
    const payload = { kind: "folder", path: workspaceRoot };
    emitSelectedPath(win, payload);
    return payload;
  });

  ipcMain.handle("desktop:open-file", async function () {
    const out = await dialog.showOpenDialog(win, { properties: ["openFile"] });
    if (out.canceled || !out.filePaths || !out.filePaths[0]) return null;
    const payload = { kind: "file", path: out.filePaths[0] };
    emitSelectedPath(win, payload);
    return payload;
  });

  ipcMain.handle("desktop:get-workspace-root", async function () {
    return workspaceRoot || "";
  });

  ipcMain.handle("desktop:list-directory", async function (_event, payload) {
    const p = payload && payload.targetPath ? payload.targetPath : workspaceRoot;
    return listDirectorySafe(p);
  });

  ipcMain.handle("desktop:read-file", async function (_event, payload) {
    const targetPath = payload && payload.targetPath ? normalizeAbs(payload.targetPath) : "";
    if (!targetPath) throw new Error("Caminho inválido.");
    const st = await fsp.stat(targetPath);
    if (!st.isFile()) throw new Error("Caminho não aponta para arquivo.");
    if (st.size > MAX_FILE_BYTES) throw new Error("Arquivo muito grande para edição no app.");
    const content = await fsp.readFile(targetPath, "utf8");
    return { path: targetPath, content };
  });

  ipcMain.handle("desktop:create-file", async function (_event, payload) {
    const targetPath = payload && payload.targetPath ? normalizeAbs(payload.targetPath) : "";
    const content = payload && typeof payload.content === "string" ? payload.content : "";
    if (!targetPath) throw new Error("Caminho inválido.");
    ensureWorkspaceWritePermission(targetPath);
    await fsp.mkdir(path.dirname(targetPath), { recursive: true });
    const exists = fs.existsSync(targetPath);
    if (exists) throw new Error("Arquivo já existe.");
    await fsp.writeFile(targetPath, content, "utf8");
    return { ok: true, path: targetPath };
  });

  ipcMain.handle("desktop:write-file", async function (_event, payload) {
    const targetPath = payload && payload.targetPath ? normalizeAbs(payload.targetPath) : "";
    const content = payload && typeof payload.content === "string" ? payload.content : "";
    if (!targetPath) throw new Error("Caminho inválido.");
    ensureWorkspaceWritePermission(targetPath);
    await fsp.mkdir(path.dirname(targetPath), { recursive: true });
    await fsp.writeFile(targetPath, content, "utf8");
    return { ok: true, path: targetPath };
  });

  ipcMain.handle("desktop:reveal-in-explorer", async function (_event, payload) {
    const targetPath = payload && payload.targetPath ? normalizeAbs(payload.targetPath) : "";
    if (!targetPath) throw new Error("Caminho inválido.");
    shell.showItemInFolder(targetPath);
    return { ok: true };
  });
}

if (process.platform === "win32") {
  app.setAppUserModelId(APP_USER_MODEL_ID);
}

app.whenReady().then(() => {
  ensureDesktopShortcut();
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
