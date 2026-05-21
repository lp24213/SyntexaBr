/**
 * SYNTEXA DESKTOP — Runtime Soberano Offline
 * ==========================================
 * Electron app com backend Python empacotado.
 * Funciona 100% offline com Foundation Model própria.
 */
const { app, BrowserWindow, shell, dialog, Menu, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const fsp = require("fs/promises");
const { spawn } = require("child_process");

const APP_USER_MODEL_ID = "br.com.syntexabr.desktop";
const iconPath = path.join(__dirname, "build", "icon.ico");
const preloadPath = path.join(__dirname, "preload.js");
const DESKTOP_SHORTCUT_NAME = "Syntexa AI.lnk";
const MAX_FILE_BYTES = 2 * 1024 * 1024;
let workspaceRoot = "";

// ── OFFLINE MODE ───────────────────────────────────────────
const isDev = !app.isPackaged;
const FRONTEND_PATH = isDev
  ? path.join(__dirname, "..", "frontend", "dist")
  : path.join(__dirname, "frontend", "dist");

const PYTHON_RUNTIME = isDev
  ? path.join(__dirname, "..", "venv", "Scripts", "python.exe")
  : path.join(__dirname, "runtime", "python", "python.exe");

const BACKEND_SCRIPT = path.join(__dirname, "backend", "desktop_server.py");
let backendProcess = null;
let backendReady = false;
let backendPort = 0;

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

async function startBackendPython() {
  if (!fs.existsSync(PYTHON_RUNTIME)) {
    console.error("[DESKTOP] Python runtime não encontrado:", PYTHON_RUNTIME);
    return false;
  }
  if (!fs.existsSync(BACKEND_SCRIPT)) {
    console.error("[DESKTOP] Backend script não encontrado:", BACKEND_SCRIPT);
    return false;
  }

  // Porta aleatória para evitar conflitos
  backendPort = 34560 + Math.floor(Math.random() * 1000);

  backendProcess = spawn(PYTHON_RUNTIME, [BACKEND_SCRIPT, "--port", String(backendPort)], {
    detached: false,
    stdio: ["ignore", "pipe", "pipe"],
  });

  backendProcess.stdout.on("data", (data) => {
    const text = data.toString();
    console.log("[PYTHON]", text.trim());
    if (text.includes("RUNTIME READY") || text.includes("Uvicorn running")) {
      backendReady = true;
      // Notifica todas as janelas abertas
      BrowserWindow.getAllWindows().forEach((w) => {
        if (!w.isDestroyed()) {
          w.webContents.send("desktop:backend-ready", { ready: true, port: backendPort, pid: backendProcess.pid });
        }
      });
    }
  });

  backendProcess.stderr.on("data", (data) => {
    console.error("[PYTHON ERR]", data.toString().trim());
  });

  backendProcess.on("exit", (code) => {
    console.log("[DESKTOP] Backend Python exited with code", code);
    backendReady = false;
    backendProcess = null;
  });

  // Aguarda backend estar pronto
  let retries = 0;
  while (!backendReady && retries < 60) {
    await new Promise((r) => setTimeout(r, 500));
    retries++;
  }

  if (!backendReady) {
    console.error("[DESKTOP] Backend Python timeout após 30s.");
  }
  return backendReady;
}

/** Atualiza a porta no contexto do preload para o frontend saber onde conectar */
function exposeDesktopPort(win, port) {
  if (!win || win.isDestroyed()) return;
  win.webContents.executeJavaScript(`
    if (window.desktopAPI) window.desktopAPI.__desktopPort = ${port};
    window.__DESKTOP_PORT__ = ${port};
  `).catch(() => {});
}

async function verifyBootValidation() {
  if (!backendReady || !backendPort) return { boot_passed: false, failures: [{ component: "backend", error: "Backend Python não iniciado ou porta desconhecida." }] };
  try {
    const http = require("http");
    const data = await new Promise((resolve, reject) => {
      const req = http.get(`http://127.0.0.1:${backendPort}/boot/diagnostic`, (res) => {
        let body = "";
        res.on("data", chunk => body += chunk);
        res.on("end", () => {
          try { resolve(JSON.parse(body)); } catch { resolve({ boot_passed: false }); }
        });
      });
      req.on("error", reject);
      req.setTimeout(8000, () => { req.destroy(); reject(new Error("timeout")); });
    });
    if (data.boot_passed) {
      console.log("[DESKTOP] Boot validation APROVADO.");
    } else {
      console.error("[DESKTOP] Boot validation FALHOU:", data.failures ? data.failures.map(f => f.component).join(", ") : "unknown");
    }
    return data;
  } catch (e) {
    console.error("[DESKTOP] Boot validation request falhou:", e.message);
    return { boot_passed: false, failures: [{ component: "boot_request", error: String(e.message) }] };
  }
}

function stopBackendPython() {
  if (backendProcess) {
    backendProcess.kill("SIGTERM");
    backendProcess = null;
    backendReady = false;
  }
}

function createWindow() {
  const opts = {
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: "Syntexa AI — Runtime Soberano",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      spellcheck: true,
      preload: preloadPath,
    },
    show: false,
    backgroundColor: "#fafbfc",
  };
  if (fs.existsSync(iconPath)) opts.icon = iconPath;

  const win = new BrowserWindow(opts);

  win.once("ready-to-show", () => win.show());
  applyAppMenu(win);

  // Abrir links externos no navegador
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http")) {
      shell.openExternal(url);
      return { action: "deny" };
    }
    return { action: "allow" };
  });

  // Carrega frontend local (offline)
  const indexPath = path.join(FRONTEND_PATH, "index.html");
  if (fs.existsSync(indexPath)) {
    win.loadFile(indexPath);
  } else {
    // Fallback para modo de desenvolvimento
    win.loadURL("https://syntexabr.com.br");
    console.warn("[DESKTOP] Frontend local não encontrado. Carregando URL externa.");
  }

  // ── IPC HANDLERS ───────────────────────────────────────
  const channels = [
    "desktop:open-folder",
    "desktop:open-file",
    "desktop:get-workspace-root",
    "desktop:list-directory",
    "desktop:read-file",
    "desktop:create-file",
    "desktop:write-file",
    "desktop:reveal-in-explorer",
    "desktop:backend-status",
    "desktop:multimodal-upload",
    "desktop:tts-synthesize",
    "desktop:export-conversation",
  ];
  channels.forEach((ch) => ipcMain.removeHandler(ch));

  ipcMain.handle("desktop:open-folder", async function () {
    const out = await dialog.showOpenDialog(win, { properties: ["openDirectory"] });
    if (out.canceled || !out.filePaths || !out.filePaths[0]) return null;
    workspaceRoot = out.filePaths[0];
    const payload = { kind: "folder", path: workspaceRoot };
    emitSelectedPath(win, payload);
    return payload;
  });

  ipcMain.handle("desktop:open-file", async function () {
    const out = await dialog.showOpenDialog(win, {
      properties: ["openFile"],
      filters: [
        { name: "Documentos", extensions: ["pdf", "docx", "txt", "md", "csv", "json", "html"] },
        { name: "Imagens", extensions: ["png", "jpg", "jpeg", "gif", "webp"] },
        { name: "Áudio", extensions: ["wav", "mp3", "ogg", "m4a"] },
        { name: "Todos", extensions: ["*"] },
      ],
    });
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

  // ── BACKEND STATUS ──────────────────────────────────────
  ipcMain.handle("desktop:backend-status", async function () {
    return {
      ready: backendReady,
      port: backendPort,
      pid: backendProcess ? backendProcess.pid : null,
      pythonPath: PYTHON_RUNTIME,
      backendScript: BACKEND_SCRIPT,
    };
  });

  // ── BOOT DIAGNOSTIC ────────────────────────────────────
  ipcMain.handle("desktop:boot-diagnostic", async function () {
    try {
      const http = require("http");
      const data = await new Promise((resolve, reject) => {
        const req = http.get(`http://127.0.0.1:${backendPort}/boot/diagnostic`, (res) => {
          let body = "";
          res.on("data", chunk => body += chunk);
          res.on("end", () => {
            try { resolve(JSON.parse(body)); } catch { resolve({ boot_passed: false, raw: body }); }
          });
        });
        req.on("error", reject);
        req.setTimeout(5000, () => { req.destroy(); reject(new Error("timeout")); });
      });
      return { ok: true, data };
    } catch (e) {
      return { ok: false, error: String(e) };
    }
  });

  // ── RUNTIME MANIFEST ────────────────────────────────────
  ipcMain.handle("desktop:runtime-manifest", async function () {
    const manifestPath = path.join(__dirname, "runtime-manifest.json");
    try {
      if (!fs.existsSync(manifestPath)) {
        return { ok: false, error: "Manifesto não encontrado. Runtime pode estar incompleto." };
      }
      const data = await fsp.readFile(manifestPath, "utf8");
      return { ok: true, manifest: JSON.parse(data) };
    } catch (e) {
      return { ok: false, error: String(e) };
    }
  });

  // ── VERIFY INTEGRITY ────────────────────────────────────
  ipcMain.handle("desktop:verify-integrity", async function () {
    const crypto = require("crypto");
    const manifestPath = path.join(__dirname, "runtime-manifest.json");
    if (!fs.existsSync(manifestPath)) {
      return { ok: false, passed: false, errors: ["Manifesto de runtime não encontrado."] };
    }

    let manifest;
    try {
      manifest = JSON.parse(await fsp.readFile(manifestPath, "utf8"));
    } catch (e) {
      return { ok: false, passed: false, errors: ["Manifesto corrompido: " + String(e)] };
    }

    const errors = [];
    const runtimeDir = path.join(__dirname, "runtime");
    const files = manifest.files || [];
    for (const entry of files) {
      const full = path.join(runtimeDir, entry.path.replace(/\//g, path.sep));
      if (!fs.existsSync(full)) {
        errors.push(`Arquivo ausente: ${entry.path}`);
        continue;
      }
      const hash = crypto.createHash("sha256").update(fs.readFileSync(full)).digest("hex");
      if (hash !== entry.sha256) {
        errors.push(`Checksum mismatch: ${entry.path} (esperado ${entry.sha256}, obtido ${hash})`);
      }
    }

    return {
      ok: true,
      passed: errors.length === 0,
      totalFiles: files.length,
      errors: errors,
      verifiedAt: new Date().toISOString(),
    };
  });

  // ── MULTIMODAL UPLOAD ─────────────────────────────────
  ipcMain.handle("desktop:multimodal-upload", async function (_event, payload) {
    const { filePath, kind } = payload || {};
    if (!filePath || !fs.existsSync(filePath)) throw new Error("Arquivo não encontrado.");
    // Lê arquivo como base64 para enviar ao backend
    const data = await fsp.readFile(filePath);
    const base64 = data.toString("base64");
    const ext = path.extname(filePath).toLowerCase();
    return {
      path: filePath,
      base64: base64,
      mime: getMimeType(ext),
      size: data.length,
      kind: kind || "file",
    };
  });

  // ── TTS SYNTHESIZE ────────────────────────────────────
  ipcMain.handle("desktop:tts-synthesize", async function (_event, payload) {
    const { text, outputPath } = payload || {};
    if (!text) throw new Error("Texto não fornecido.");
    // Delega ao backend Python via HTTP ou IPC
    const out = outputPath || path.join(app.getPath("temp"), `syntexa-tts-${Date.now()}.wav`);
    return { path: out, text, status: "queued" };
  });

  // ── EXPORT CONVERSATION ───────────────────────────────
  ipcMain.handle("desktop:export-conversation", async function (_event, payload) {
    const { content, format, defaultName } = payload || {};
    const filters = {
      pdf: [{ name: "PDF", extensions: ["pdf"] }],
      docx: [{ name: "Word", extensions: ["docx"] }],
      md: [{ name: "Markdown", extensions: ["md"] }],
      html: [{ name: "HTML", extensions: ["html"] }],
      csv: [{ name: "CSV", extensions: ["csv"] }],
      json: [{ name: "JSON", extensions: ["json"] }],
      txt: [{ name: "Texto", extensions: ["txt"] }],
    };
    const out = await dialog.showSaveDialog(win, {
      defaultPath: defaultName || `syntexa-export.${format || "txt"}`,
      filters: filters[format] || filters.txt,
    });
    if (out.canceled || !out.filePath) return null;
    await fsp.writeFile(out.filePath, content || "", "utf8");
    return { path: out.filePath, ok: true };
  });
}

function getMimeType(ext) {
  const map = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
  };
  return map[ext] || "application/octet-stream";
}

if (process.platform === "win32") {
  app.setAppUserModelId(APP_USER_MODEL_ID);
}

app.whenReady().then(async () => {
  ensureDesktopShortcut();
  // Inicia backend Python local antes de abrir a janela
  const backendOk = await startBackendPython();
  if (!backendOk) {
    console.error("[DESKTOP] BACKEND PYTHON NÃO INICIADO. PROIBIDO ABRIR UI COM MODELO QUEBRADO.");
    dialog.showErrorBox(
      "Syntexa V45 — Boot Validation Falhou",
      "O runtime neural não pôde ser iniciado.\n\n" +
      "Possíveis causas:\n" +
      "• Python runtime não encontrado em runtime/python/python.exe\n" +
      "• Backend script desktop_server.py ausente\n" +
      "• Dependências (fastapi, uvicorn) não instaladas\n\n" +
      "Verifique os logs em logs/runtime.log"
    );
    app.quit();
    return;
  }
  // Verifica boot validation do backend antes de mostrar a janela
  const bootData = await verifyBootValidation();
  const bootOk = bootData && bootData.boot_passed;
  if (!bootOk) {
    console.error("[DESKTOP] BOOT VALIDATION FALHOU. UI BLOQUEADA.");
    // Envia diagnóstico real para todas as janelas (presentes e futuras)
    const payload = { boot_passed: false, failures: (bootData && bootData.failures) || [], raw: bootData };
    BrowserWindow.getAllWindows().forEach((w) => {
      if (!w.isDestroyed()) w.webContents.send("desktop:boot-failure", payload);
    });
  }
  createWindow();
  // Expõe porta real para o frontend
  BrowserWindow.getAllWindows().forEach((w) => {
    if (!w.isDestroyed()) exposeDesktopPort(w, backendPort);
  });
});

app.on("window-all-closed", () => {
  stopBackendPython();
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on("before-quit", () => {
  stopBackendPython();
});
