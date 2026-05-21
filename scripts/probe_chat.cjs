/**
 * Playwright probe: confirma se o textarea do /chat aceita foco/digita em produção.
 * Uso: node probe_chat.cjs
 */
const path = require("path");
const fePath = path.resolve(__dirname, "..", "frontend", "node_modules", "@playwright", "test");
const { chromium, devices } = require(fePath);

(async () => {
  const out = { desktop: {}, mobile: {} };
  const browser = await chromium.launch({ headless: true });

  for (const profile of ["desktop", "mobile"]) {
    const ctx = profile === "mobile"
      ? await browser.newContext({ ...devices["iPhone 14 Pro"] })
      : await browser.newContext({ viewport: { width: 1366, height: 800 } });
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
    page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });

    await page.goto("https://syntexabr.com.br/chat/", { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(1500);

    const textareaInfo = await page.evaluate(() => {
      const ta = document.querySelector("textarea.chat-input, textarea");
      if (!ta) return { found: false };
      const r = ta.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      const elAtCenter = document.elementFromPoint(cx, cy);
      const cs = getComputedStyle(ta);
      return {
        found: true,
        rect: { x: r.x, y: r.y, w: r.width, h: r.height },
        pointerEvents: cs.pointerEvents,
        opacity: cs.opacity,
        zIndex: cs.zIndex,
        disabled: ta.disabled,
        readonly: ta.readOnly,
        elAtCenter: elAtCenter ? (elAtCenter.tagName + "#" + (elAtCenter.id || "") + "." + elAtCenter.className.toString().slice(0, 80)) : null,
        topMostMatch: elAtCenter === ta,
      };
    });

    let typed = null;
    let focused = null;
    try {
      const ta = await page.locator("textarea").first();
      await ta.scrollIntoViewIfNeeded();
      await ta.click({ timeout: 5000 });
      await ta.type("Hello world", { delay: 30 });
      typed = await ta.inputValue();
      focused = await page.evaluate(() => document.activeElement && document.activeElement.tagName);
    } catch (e) {
      typed = "ERR: " + e.message;
    }

    out[profile] = { textareaInfo, typed, focused, errors };
    await ctx.close();
  }

  await browser.close();
  console.log(JSON.stringify(out, null, 2));
})().catch((e) => { console.error("FATAL:", e); process.exit(1); });
