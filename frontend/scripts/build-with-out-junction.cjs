/**
 * Build estático (output: export) tolerante a OneDrive / EBUSY em `out/`.
 *
 * 1) Tenta junction `out` → %TEMP% (rápido).
 * 2) Se falhar, copia o projeto para %TEMP%, corre `next build` lá (out em disco local)
 *    e faz mirror de `out/` de volta com robocopy (Windows) ou cp (Unix).
 */
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync, execFileSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const outPath = path.join(root, "out");
const tempOutTarget = path.join(os.tmpdir(), "syntexa-frontend-static-out-" + process.pid);

function sleepSync(ms) {
  try {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
  } catch {
    /* ignore */
  }
}

function wipeDir(dir) {
  for (let i = 0; i < 12; i++) {
    try {
      if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 120 });
      }
      fs.mkdirSync(dir, { recursive: true });
      return;
    } catch {
      sleepSync(250);
    }
  }
  throw new Error("Não foi possível preparar: " + dir);
}

function removeProjectOut() {
  if (!fs.existsSync(outPath)) return;
  try {
    fs.rmSync(outPath, { recursive: true, force: true, maxRetries: 6, retryDelay: 150 });
    return;
  } catch {
    /* continua */
  }
  const bak = path.join(root, "out__bak_" + Date.now());
  fs.renameSync(outPath, bak);
}

function prepareOutWindows() {
  wipeDir(tempOutTarget);
  let lastErr;
  for (let attempt = 0; attempt < 18; attempt++) {
    try {
      if (fs.existsSync(outPath)) {
        removeProjectOut();
      }
      execFileSync("cmd", ["/c", "mklink", "/J", "out", tempOutTarget], {
        cwd: root,
        stdio: "inherit",
      });
      return;
    } catch (e) {
      lastErr = e;
      sleepSync(350);
    }
  }
  throw lastErr || new Error("mklink junction falhou");
}

function prepareOutUnix() {
  wipeDir(tempOutTarget);
  if (fs.existsSync(outPath)) {
    fs.rmSync(outPath, { recursive: true, force: true });
  }
  fs.symlinkSync(tempOutTarget, outPath, "dir");
}

function robocopyExitOk(code) {
  return code !== null && code < 8;
}

function buildInTempWorkaround(reason) {
  console.warn("[build] " + reason);
  console.warn("[build] Compilando em cópia em %TEMP% (sem OneDrive em out/)…");

  const work = path.join(os.tmpdir(), "syntexa-fe-build-" + Date.now());
  fs.mkdirSync(work, { recursive: true });

  if (process.platform === "win32") {
    const rc = spawnSync(
      "robocopy",
      [
        root,
        work,
        "/E",
        "/XD",
        "node_modules",
        ".next",
        "out",
        "test-results",
        ".wrangler",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
      ],
      { stdio: "inherit" }
    );
    if (!robocopyExitOk(rc.status)) {
      console.error("[build] robocopy para pasta temporária falhou (código " + rc.status + ")");
      process.exit(1);
    }
  } else {
    fs.mkdirSync(work, { recursive: true });
    fs.cpSync(root, work, {
      recursive: true,
      filter: (p) => {
        const rel = path.relative(root, p);
        if (!rel || rel === ".") return true;
        const parts = rel.split(path.sep);
        return !parts.some((x) =>
          ["node_modules", ".next", "out", "test-results", ".wrangler"].includes(x)
        );
      },
    });
  }

  const npmInstall = spawnSync("npm", ["install", "--no-fund"], {
    cwd: work,
    stdio: "inherit",
    shell: process.platform === "win32",
    env: process.env,
  });
  if (npmInstall.status !== 0) {
    process.exit(npmInstall.status ?? 1);
  }

  const nb = spawnSync("npx", ["next", "build"], {
    cwd: work,
    stdio: "inherit",
    shell: process.platform === "win32",
    env: process.env,
  });
  if (nb.status !== 0) {
    process.exit(nb.status ?? 1);
  }

  const builtOut = path.join(work, "out");
  if (!fs.existsSync(builtOut)) {
    console.error("[build] next não gerou", builtOut);
    process.exit(1);
  }

  if (process.platform === "win32") {
    fs.mkdirSync(outPath, { recursive: true });
    const rc2 = spawnSync(
      "robocopy",
      [builtOut, outPath, "/MIR", "/R:10", "/W:300", "/NFL", "/NDL", "/NJH", "/NJS"],
      { stdio: "inherit" }
    );
    if (!robocopyExitOk(rc2.status)) {
      console.error(
        "[build] Não foi possível copiar out/ para o projeto (ficheiros em uso?). Saída em:\n  " +
          builtOut
      );
      process.exit(1);
    }
  } else {
    fs.rmSync(outPath, { recursive: true, force: true });
    fs.cpSync(builtOut, outPath, { recursive: true });
  }

  console.log("[OK] next build concluído; out/ atualizado em", outPath);
}

function main() {
  if (process.platform === "win32") {
    try {
      prepareOutWindows();
    } catch (e) {
      const msg = e && e.message ? e.message : String(e);
      const code = e && e.code ? e.code : "";
      if (code === "EBUSY" || msg.includes("EBUSY")) {
        return buildInTempWorkaround("Pasta out/ bloqueada (EBUSY).");
      }
      return buildInTempWorkaround("Junction não disponível: " + msg);
    }
  } else {
    try {
      prepareOutUnix();
    } catch (e) {
      return buildInTempWorkaround(String(e && e.message ? e.message : e));
    }
  }

  const r = spawnSync("npx", ["next", "build"], {
    cwd: root,
    stdio: "inherit",
    shell: process.platform === "win32",
    env: process.env,
  });

  if (r.status !== 0) {
    process.exit(r.status ?? 1);
  }

  console.log("[OK] next build concluído.");
}

main();
