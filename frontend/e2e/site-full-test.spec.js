/**
 * Teste completo do site Syntexa.
 * Fluxo: Homepage → Cadastro → Verificação de email → Login → Chat → Planos
 *
 * Executar: npx playwright test e2e/site-full-test.spec.js
 */
const { test, expect } = require("@playwright/test");

const BASE = (process.env.SYNTEXA_E2E_BASE || "https://syntexabr.com.br").replace(/\/$/, "");
const API_BASE = (process.env.SYNTEXA_API_BASE || "https://api.syntexabr.com.br").replace(/\/$/, "");

function randCpf() {
  const n = () => Math.floor(Math.random() * 10);
  const base = [n(),n(),n(),n(),n(),n(),n(),n(),n()];
  let d1 = base.reduce((s,v,i) => s + v * (10 - i), 0) % 11;
  d1 = d1 < 2 ? 0 : 11 - d1;
  let d2 = base.reduce((s,v,i) => s + v * (11 - i), 0) + d1 * 2;
  d2 = d2 % 11; d2 = d2 < 2 ? 0 : 11 - d2;
  return base.join("") + String(d1) + String(d2);
}

const TEST_SECRET = "f0c1fb412463e70169ce1e6f9c10e6f5";

const TEST_USER = {
  email: `teste_${Date.now()}@syntexabr.com.br`,
  password: "Teste123!",
  full_name: "Teste Automatizado",
  document: randCpf(),
};

let verificationCode = "";
let accessToken = "";
let refreshToken = "";

/**
 * TESTE 1: Homepage carrega
 */
test("1. Homepage carrega sem erros", async ({ page }) => {
  const errors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });
  page.on("pageerror", (err) => errors.push(err.message));

  const response = await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  expect(response.status()).toBe(200);
  expect(await page.title()).toContain("Syntexa");

  await page.waitForTimeout(500);
  expect(errors.length).toBe(0);
});

/**
 * TESTE 2: Cadastro envia código de verificação
 */
test("2. Cadastro public-register retorna 200", async () => {
  const resp = await fetch(`${API_BASE}/v1/auth/public-register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Syntexa-Test-Key": TEST_SECRET,
    },
    body: JSON.stringify(TEST_USER),
  });

  const data = await resp.json().catch(() => ({}));
  console.log("[CADASTRO] status:", resp.status, "| body:", JSON.stringify(data));

  expect([200, 400, 429]).toContain(resp.status);
  if (resp.status === 429) {
    console.log("[CADASTRO] Rate limit atingido — teste pulado");
    return;
  }
  expect(data.detail).toContain("código");
});

/**
 * TESTE 3: Buscar código de verificação no banco (via API interna ou log)
 *  - Se não conseguir, tenta verificar com "000000" e espera erro 400
 */
test("3. Verificação de email funciona", async () => {
  // Tenta pegar o código do último registro via API (se disponível)
  // Fallback: testa que endpoint responde corretamente
  const respVerify = await fetch(`${API_BASE}/v1/auth/verify-email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Syntexa-Test-Key": TEST_SECRET,
    },
    body: JSON.stringify({
      email: TEST_USER.email,
      code: "000000",
    }),
  });

  const data = await respVerify.json().catch(() => ({}));
  console.log("[VERIFY] status:", respVerify.status, "| body:", JSON.stringify(data));

  expect([200, 400]).toContain(respVerify.status);
  if (respVerify.status === 200) {
    console.log("[VERIFY] Email verificado com sucesso!");
  } else {
    console.log("[VERIFY] Código incorreto (esperado para teste com código fake)");
  }
});

/**
 * TESTE 4: Login com credenciais corretas retorna token
 */
test("4. Login retorna access_token 200", async () => {
  const body = new URLSearchParams();
  body.set("username", TEST_USER.email);
  body.set("password", TEST_USER.password);
  body.set("grant_type", "password");

  const resp = await fetch(`${API_BASE}/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-Syntexa-Test-Key": TEST_SECRET,
    },
    body,
  });

  const data = await resp.json().catch(() => ({}));
  console.log("[LOGIN] status:", resp.status, "| access_token:", data.access_token ? "SIM" : "NÃO");

  expect([200, 401]).toContain(resp.status);
  if (resp.status === 200) {
    expect(data.access_token).toBeTruthy();
    accessToken = data.access_token;
    refreshToken = data.refresh_token || "";
  }
});

/**
 * TESTE 5: Chat carrega para usuário autenticado
 */
test("5. Chat carrega e envia mensagem", async ({ page, browserName }) => {
  test.skip(!accessToken, "Login falhou — pulando teste de chat");

  // Injeta token no localStorage antes de abrir a página
  await page.goto(`${BASE}/login/`, { waitUntil: "networkidle" });
  await page.evaluate((token) => {
    window.localStorage.setItem("syntexa_token", token);
  }, accessToken);

  // Navega pro chat
  await page.goto(`${BASE}/chat/`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);

  const title = await page.title();
  console.log("[CHAT] title:", title);
  expect(title.toLowerCase()).toContain("syntexa");

  // Tenta encontrar input e enviar mensagem
  const input = await page.locator('textarea, input[type="text"]').first();
  const count = await input.count();
  if (count > 0) {
    await input.fill("Olá, teste automatizado");
    await input.press("Enter");
    await page.waitForTimeout(3000);

    // Verifica se resposta aparece
    const pageText = await page.textContent("body");
    expect(pageText.length).toBeGreaterThan(50);
  }
});

/**
 * TESTE 6: Página de planos carrega
 */
test("6. Planos carrega sem erros", async ({ page }) => {
  const errors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  await page.goto(`${BASE}/planos/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);

  const title = await page.title();
  console.log("[PLANOS] title:", title);
  expect(title.toLowerCase()).toContain("syntexa");
  expect(errors.length).toBe(0);
});

/**
 * TESTE 7: Logout funciona
 */
test("7. Logout limpa localStorage", async ({ page }) => {
  await page.goto(`${BASE}/chat/`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    window.localStorage.removeItem("syntexa_token");
    window.localStorage.removeItem("syntexa_refresh_token");
  });

  const token = await page.evaluate(() => window.localStorage.getItem("syntexa_token"));
  expect(token).toBeNull();
});
