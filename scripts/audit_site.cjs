/**
 * Auditoria visual + bloqueios de prod. Tira screenshots e detecta overlays.
 */
const path = require("path");
const fs = require("fs");
const fePath = path.resolve(__dirname, "..", "frontend", "node_modules", "@playwright", "test");
const { chromium, devices } = require(fePath);

const ROUTES = [
  { name: "home", url: "https://syntexabr.com.br/" },
  { name: "chat", url: "https://syntexabr.com.br/chat/" },
  { name: "login", url: "https://syntexabr.com.br/login/" },
  { name: "privacidade", url: "https://syntexabr.com.br/privacidade/" },
  { name: "cookies", url: "https://syntexabr.com.br/cookies/" },
  { name: "educacao", url: "https://syntexabr.com.br/educacao/" },
];

const OUT = path.resolve(__dirname, "..", "audit-screens");
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

async function inspectPage(page) {
  return await page.evaluate(() => {
    // Coleta todos elements fixed/absolute com z-index alto que podem bloquear
    const overlays = [];
    const all = document.querySelectorAll("*");
    all.forEach((el) => {
      const cs = getComputedStyle(el);
      const pos = cs.position;
      const z = parseInt(cs.zIndex || "0", 10) || 0;
      const pe = cs.pointerEvents;
      if ((pos === "fixed" || pos === "absolute") && (z >= 30 || pe === "auto")) {
        const r = el.getBoundingClientRect();
        if (r.width > 100 && r.height > 30 && r.top < window.innerHeight && r.left < window.innerWidth) {
          overlays.push({
            tag: el.tagName,
            cls: (el.className || "").toString().slice(0, 100),
            id: el.id || "",
            role: el.getAttribute("role") || "",
            ariaLabel: el.getAttribute("aria-label") || "",
            pos, z, pe,
            rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          });
        }
      }
    });

    // Encontra textarea principal
    const ta = document.querySelector("textarea.chat-input, textarea");
    let textareaInfo = null;
    if (ta) {
      const r = ta.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      const el = document.elementFromPoint(cx, cy);
      textareaInfo = {
        rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        viewport: { w: window.innerWidth, h: window.innerHeight },
        elAtCenter: el ? (el.tagName + "." + (el.className || "").toString().slice(0, 60)) : null,
        topMostMatch: el === ta,
      };
    }

    // Header/sidebar layout
    const header = document.querySelector("header");
    const aside = document.querySelector("aside");
    const main = document.querySelector("main");
    const layout = {
      header: header ? { ...header.getBoundingClientRect().toJSON(), display: getComputedStyle(header).display } : null,
      aside: aside ? { rect: aside.getBoundingClientRect().toJSON(), display: getComputedStyle(aside).display } : null,
      main: main ? main.getBoundingClientRect().toJSON() : null,
    };

    return { overlays, textareaInfo, layout, hasFramerMotion: typeof window.motion !== "undefined" };
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = {};

  for (const profile of [{ k: "desktop", ctx: { viewport: { width: 1440, height: 900 } } }, { k: "mobile", ctx: { ...devices["iPhone 14 Pro"] } }]) {
    results[profile.k] = {};
    for (const r of ROUTES) {
      const ctx = await browser.newContext(profile.ctx);
      const page = await ctx.newPage();
      const errs = [];
      page.on("pageerror", (e) => errs.push("pageerror: " + e.message));
      page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
      try {
        await page.goto(r.url, { waitUntil: "domcontentloaded", timeout: 25000 });
        await page.waitForLoadState("load", { timeout: 15000 }).catch(() => {});
        // limpa localStorage pra forçar cookie banner aparecer (UX real do primeiro acesso)
        await page.evaluate(() => { try { localStorage.clear(); } catch (_) {} });
        await page.reload({ waitUntil: "domcontentloaded" }).catch(() => {});
        await page.waitForTimeout(2200);
        const info = await inspectPage(page);
        await page.screenshot({ path: path.join(OUT, `${profile.k}_${r.name}.png`), fullPage: r.name === "home" });
        results[profile.k][r.name] = { ...info, errors: errs };
      } catch (e) {
        results[profile.k][r.name] = { error: String(e), errors: errs };
      }
      await ctx.close();
    }
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, "audit.json"), JSON.stringify(results, null, 2));

  // Resumo enxuto
  console.log("=== RESUMO ===");
  for (const k of Object.keys(results)) {
    for (const rk of Object.keys(results[k])) {
      const r = results[k][rk];
      if (r.error) { console.log(`${k}/${rk} FAIL: ${r.error.slice(0,120)}`); continue; }
      const blockers = (r.overlays || []).filter(o => o.pe === "auto" && o.z >= 50);
      const taOk = r.textareaInfo ? (r.textareaInfo.topMostMatch ? "OK" : `BLOQ por ${r.textareaInfo.elAtCenter}`) : "n/a";
      console.log(`${k}/${rk}: overlays_auto_z>=50=${blockers.length}, textarea=${taOk}, errs=${r.errors.length}`);
      blockers.slice(0, 3).forEach(b => console.log(`   - [z${b.z} pe:${b.pe}] ${b.tag}.${b.cls.slice(0,50)} aria=${b.ariaLabel} rect=${JSON.stringify(b.rect)}`));
      r.errors.slice(0, 2).forEach(e => console.log(`   ERR: ${e.slice(0,160)}`));
    }
  }
})().catch(e => { console.error(e); process.exit(1); });
