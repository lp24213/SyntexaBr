/**
 * Auditoria navegável: visita rotas, captura screenshots, consolida erros de console/rede.
 * Isto corre só na tua máquina/CI — NÃO é publicado no site. O deploy (`deploy-syntexa.ps1 deploy-front`)
 * envia apenas o build Next (`out/`), nunca esta pasta `e2e/`.
 *
 * Para passar 100% sem #418: `npm run build`, servir `out/` e SYNTEXA_E2E_BASE=http://127.0.0.1:PORTO
 *
 * Executar: npx playwright test e2e/syntexa-site-audit.spec.js
 * Screenshots: test-results/audit-screenshots/
 */
const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

/** Rotas públicas do app (Next static export, trailingSlash). */
const ROUTES = [
  "/",
  "/chat/",
  "/login/",
  "/register/",
  "/cadastro/",
  "/forgot-password/",
  "/recuperar-senha/",
  "/verify-email/",
  "/activate-reset/",
  "/activate-signup/",
  "/download/",
  "/planos/",
  "/plans/",
  "/config/",
  "/portal/",
  "/profile/",
  "/perfil/",
  "/educacao/",
  "/educacao/aluno/",
  "/educacao/professor/",
  "/educacao/ciencia/",
  "/educacao/concursos/",
  "/educacao/governo/",
  "/educacao/laboratorios/",
  "/admin/",
  "/admin/ia-soberana/",
  "/admin/institucional/",
  "/H9vKp3mLt8Qw/",
  "/K9pT2vRa8mQd/",
  "/N8qVb4sRm2Yt/",
  "/D5rZw7mQx2Lc/",
  "/Q7n2mLx9A4r/",
  "/R4nZx6qLp1Md/",
  "/M6cKp1uXe9Ha/",
  "/J7pLs3mQd2Nx/",
  "/B-I7hUkBMF0d/",
  "/P8yLm3qRs6Td/",
  "/W3dLp2xQn8Zk/",
  "/B_4mhVUCNloA/",
  "/V2nKx7pLa4Qm/",
  "/X8cMv2aRp9Tq/",
  "/C4hPt9nVa1Xe/",
];

function shotName(route) {
  var s = route.replace(/^\/+|\/+$/g, "") || "home";
  return s.replace(/\//g, "_") + ".png";
}

function attachListeners(page, bucket) {
  page.on("console", function (msg) {
    var t = msg.type();
    if (t === "error" || t === "warning") {
      bucket.console.push({ type: t, text: msg.text(), location: msg.location() });
    }
  });
  page.on("pageerror", function (err) {
    bucket.pageErrors.push(String(err && err.message ? err.message : err));
  });
  page.on("requestfailed", function (req) {
    bucket.requestFailed.push({
      url: req.url(),
      failure: req.failure() && req.failure().errorText,
    });
  });
}

test.describe("Syntexa BR — auditoria de rotas", function () {
  test.beforeAll(function () {
    var dir = path.join(process.cwd(), "test-results", "audit-screenshots");
    fs.mkdirSync(dir, { recursive: true });
  });

  for (var i = 0; i < ROUTES.length; i++) {
    (function (route) {
      test("GET " + route + " — screenshot + erros", async function ({ page, baseURL }) {
        var bucket = { console: [], pageErrors: [], requestFailed: [] };
        attachListeners(page, bucket);

        var res = await page.goto(route, { waitUntil: "networkidle", timeout: 90_000 });
        expect(res, "response").toBeTruthy();
        var status = res.status();
        expect(status, "HTTP status").toBeLessThan(500);

        await page.waitForTimeout(800);

        var out = path.join(process.cwd(), "test-results", "audit-screenshots", shotName(route));
        await page.screenshot({ path: out, fullPage: true });

        var summary = {
          route,
          url: page.url(),
          status,
          consoleErrors: bucket.console.filter(function (c) {
            return c.type === "error";
          }),
          consoleWarnings: bucket.console.filter(function (c) {
            return c.type === "warning";
          }),
          pageErrors: bucket.pageErrors,
          requestFailed: bucket.requestFailed,
        };

        fs.writeFileSync(
          path.join(process.cwd(), "test-results", "audit-screenshots", shotName(route).replace(/\.png$/, ".json")),
          JSON.stringify(summary, null, 2),
          "utf8"
        );

        expect(summary.pageErrors, "sem exceções JS na página (corrija o app, não silencie o teste)").toEqual([]);
      });
    })(ROUTES[i]);
  }
});

test.describe("Chat — envio e resposta", function () {
  test("mensagem de teste e estado final", async function ({ page, baseURL }) {
    var bucket = { console: [], pageErrors: [], requestFailed: [] };
    attachListeners(page, bucket);

    await page.goto("/chat/", { waitUntil: "networkidle", timeout: 90_000 });

    var ta = page.locator('textarea[placeholder="Digite sua mensagem..."]');
    await expect(ta).toBeVisible();
    await ta.fill(
      "Responda em uma frase curta em português: qual é a capital do Brasil?"
    );

    await page.getByRole("button", { name: "Enviar" }).click();

    await page.getByRole("button", { name: "Enviando" }).waitFor({ state: "visible", timeout: 15_000 }).catch(function () {});
    await page.getByRole("button", { name: "Enviar" }).waitFor({ state: "visible", timeout: 120_000 });

    await page.waitForTimeout(1500);

    var out = path.join(process.cwd(), "test-results", "audit-screenshots", "chat_after_reply.png");
    await page.screenshot({ path: out, fullPage: true });

    fs.writeFileSync(
      path.join(process.cwd(), "test-results", "audit-screenshots", "chat_after_reply.json"),
      JSON.stringify(
        {
          url: page.url(),
          pageErrors: bucket.pageErrors,
          console: bucket.console,
          requestFailed: bucket.requestFailed,
        },
        null,
        2
      ),
      "utf8"
    );

    expect(bucket.pageErrors, "sem exceções JS no chat").toEqual([]);
  });
});
