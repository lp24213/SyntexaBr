const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const fs = require("fs");

const APP_URL = "https://syntexabr.com.br";
const iconPath = path.join(__dirname, "build", "icon.ico");

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
    },
    show: false,
  };
  if (fs.existsSync(iconPath)) opts.icon = iconPath;

  const win = new BrowserWindow(opts);

  win.once("ready-to-show", () => win.show());

  // Abrir links externos no navegador
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http") && !url.startsWith(APP_URL)) {
      shell.openExternal(url);
      return { action: "deny" };
    }
    return { action: "allow" };
  });

  win.loadURL(APP_URL);
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
