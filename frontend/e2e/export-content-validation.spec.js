/**
 * Pede uma resposta estruturada à IA, exporta TXT, CSV, PDF, Excel, Word e
 * ABRE os ficheiros no Node: extrai texto e verifica marcador + tabela mínima.
 *
 * npm run test:e2e:exports
 * SYNTEXA_E2E_BASE=... (opcional)
 */
const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");
const {
  readXlsxAllText,
  readCsvUtf8,
  readPdfText,
  readDocxText,
  validateMarker,
  looksLikePriceTable,
} = require("./helpers/validate-export-artifacts.cjs");

const MARKER = "SYNTEXA_E2E_MARKER_Q9Z";

const STRUCTURED_PROMPT = [
  "Responda em português. Regras obrigatórias:",
  "1) Inclua numa linha isolada o texto exato (sem alterar uma letra): " + MARKER,
  "2) Inclua uma pequena tabela de produtos com colunas: Produto, Preço (R$), Qtd — use três linhas de dados fictícios.",
  "3) Não envolva a resposta em cercas de código markdown (sem ```).",
  "Seja objetivo.",
].join("\n");

async function waitForChatIdle(page, replyTimeoutMs) {
  await page.getByRole("button", { name: "Enviando" }).waitFor({ state: "visible", timeout: 20_000 }).catch(function () {});
  await page.getByRole("button", { name: "Enviar" }).waitFor({ state: "visible", timeout: replyTimeoutMs });
}

test.describe.configure({ mode: "serial" });

test("exportações: conteúdo verificado (TXT, CSV, PDF, Excel, Word)", async function ({ page }) {
  test.setTimeout(15 * 60 * 1000);

  await page.goto("/chat/", { waitUntil: "networkidle", timeout: 90_000 });
  await page.getByRole("button", { name: "Aceitar cookies" }).click({ timeout: 8000 }).catch(function () {});
  await page.getByRole("button", { name: "Somente essenciais" }).click({ timeout: 3000 }).catch(function () {});
  var ta = page.locator('textarea[placeholder="Digite sua mensagem..."]');
  await expect(ta).toBeVisible();

  await ta.fill(STRUCTURED_PROMPT);
  await page.getByRole("button", { name: "Enviar" }).click();
  await waitForChatIdle(page, 240_000);

  var replyBubble = page.locator(".syntexa-bubble-assistant").filter({ hasText: MARKER }).last();
  await expect(replyBubble).toBeVisible({ timeout: 90_000 });

  var kinds = [
    { role: "TXT", ext: ".txt", validate: async function (p) {
      var t = fs.readFileSync(p, "utf8");
      var v = validateMarker(t, MARKER);
      var table = looksLikePriceTable(t);
      return { markerOk: v.ok, tableOk: table, preview: v.preview };
    }},
    { role: "CSV", ext: ".csv", validate: async function (p) {
      var t = readCsvUtf8(p);
      var v = validateMarker(t, MARKER);
      var table = looksLikePriceTable(t);
      return { markerOk: v.ok, tableOk: table, preview: v.preview };
    }},
    { role: "PDF", ext: ".pdf", validate: async function (p) {
      var t = await readPdfText(p);
      var v = validateMarker(t, MARKER);
      var table = looksLikePriceTable(t);
      return { markerOk: v.ok, tableOk: table, preview: v.preview };
    }},
    { role: "Excel", ext: ".xlsx", validate: async function (p) {
      var t = readXlsxAllText(p);
      var v = validateMarker(t, MARKER);
      var table = looksLikePriceTable(t);
      return { markerOk: v.ok, tableOk: table, preview: v.preview };
    }},
    { role: "Word", ext: ".docx", validate: async function (p) {
      var t = await readDocxText(p);
      var v = validateMarker(t, MARKER);
      var table = looksLikePriceTable(t);
      return { markerOk: v.ok, tableOk: table, preview: v.preview };
    }},
  ];

  var report = { marker: MARKER, files: [] };

  for (var i = 0; i < kinds.length; i++) {
    var k = kinds[i];
    if (i > 0) await page.waitForTimeout(600);
    var dl = await Promise.all([
      page.waitForEvent("download", { timeout: 120_000 }),
      replyBubble.getByRole("button", { name: k.role, exact: true }).click(),
    ]).then(function (x) {
      return x[0];
    });

    var fp = await dl.path();
    expect(fp, "path do download " + k.role).toBeTruthy();

    var st = fs.statSync(fp);
    expect(st.size, "ficheiro " + k.role + " não vazio").toBeGreaterThan(40);

    var result = await k.validate(fp);
    report.files.push({ kind: k.role, bytes: st.size, ...result });

    expect(
      result.markerOk,
      k.role + ": texto extraído deve conter o marcador " + MARKER + ". Prévia: " + (result.preview || "").slice(0, 400)
    ).toBe(true);

    expect(
      result.tableOk,
      k.role + ": deve parecer tabela (Produto/Preço/Qtd e separadores). Prévia: " + (result.preview || "").slice(0, 400)
    ).toBe(true);
  }

  fs.mkdirSync(path.join(process.cwd(), "test-results"), { recursive: true });
  fs.writeFileSync(
    path.join(process.cwd(), "test-results", "export-content-validation.json"),
    JSON.stringify(report, null, 2),
    "utf8"
  );
});
