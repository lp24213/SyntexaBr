// @ts-check
/**
 * Testes de download real (produção por omissão).
 * SYNTEXA_E2E_BASE — site (default https://syntexabr.com.br)
 * SYNTEXA_API_BASE — API (default https://api.syntexabr.com.br)
 */
const { test, expect } = require("@playwright/test");

const SITE = process.env.SYNTEXA_E2E_BASE || "https://syntexabr.com.br";
const API = process.env.SYNTEXA_API_BASE || "https://api.syntexabr.com.br";

test.describe("Downloads de pacotes desktop", () => {
  test("site: GET /download/*.exe → 302 para API /v1/desktop/binary", async ({ request }) => {
    const res = await request.get(`${SITE}/download/SyntexaAI-Setup-1.0.0.exe`, {
      maxRedirects: 0,
    });
    expect([301, 302, 307, 308]).toContain(res.status());
    const loc = res.headers().location || "";
    expect(loc, "Location deve apontar para api…/v1/desktop/binary/…exe").toMatch(
      /api\.syntexabr\.com\.br.*\/v1\/desktop\/binary\/SyntexaAI-Setup-1\.0\.0\.exe/
    );
  });

  test("API: /v1/desktop/binary/SyntexaAI-Setup-1.0.0.exe → 200 e corpo grande", async ({
    request,
  }) => {
    const res = await request.get(`${API}/v1/desktop/binary/SyntexaAI-Setup-1.0.0.exe`);
    expect(
      res.status(),
      "404 = pacote não está na VM. Rode: desktop npm run build + copy-artifacts, depois deploy-back."
    ).toBe(200);
    const buf = await res.body();
    expect(buf.byteLength).toBeGreaterThan(1_000_000);
  });

  test("API: /v1/desktop/binary/SyntexaAI-linux-x64.AppImage → 200 e corpo grande", async ({
    request,
  }) => {
    const res = await request.get(`${API}/v1/desktop/binary/SyntexaAI-linux-x64.AppImage`);
    expect(
      res.status(),
      "404 = AppImage não está na VM. Rode deploy completo com build Electron (Linux)."
    ).toBe(200);
    const buf = await res.body();
    expect(buf.byteLength).toBeGreaterThan(10_000_000);
  });
});
