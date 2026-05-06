/**
 * Checkup total: todas as rotas (screenshot + consola) + N rodadas de chat.
 *
 * SYNTEXA_E2E_BASE, SYNTEXA_E2E_CHAT_ROUNDS (default 100), SYNTEXA_E2E_CHAT_DELAY_MS,
 * SYNTEXA_E2E_REPLY_MS, SYNTEXA_E2E_SKIP_VOICE, SYNTEXA_E2E_SKIP_EXPORTS, SYNTEXA_E2E_FULL_CONSOLE
 *
 * Relatório: test-results/full-checkup-report.json
 */
const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");
const { buildCheckupPrompts } = require("./data/prompts-checkup");

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

function attachTelemetryOnce(page, bucket) {
  page.on("console", function (msg) {
    var t = msg.type();
    var full = process.env.SYNTEXA_E2E_FULL_CONSOLE === "1";
    if (full || t === "error" || t === "warning") {
      bucket.console.push({
        type: t,
        text: msg.text(),
        t: Date.now(),
        location: msg.location(),
      });
    }
  });
  page.on("pageerror", function (err) {
    bucket.pageErrors.push({ msg: String(err && err.message ? err.message : err), t: Date.now() });
  });
  page.on("requestfailed", function (req) {
    bucket.requestFailed.push({
      url: req.url(),
      failure: req.failure() && req.failure().errorText,
      t: Date.now(),
    });
  });
  page.on("response", function (res) {
    try {
      var u = res.url();
      if (!/syntexabr\.com\.br/i.test(u)) return;
      if (bucket.apiResponses.length < 5000) {
        bucket.apiResponses.push({
          url: u.split("?")[0],
          status: res.status(),
          t: Date.now(),
        });
      }
    } catch (_) {}
  });
}

async function waitForChatIdle(page, replyTimeoutMs) {
  await page.getByRole("button", { name: "Enviando" }).waitFor({ state: "visible", timeout: 20_000 }).catch(function () {});
  await page.getByRole("button", { name: "Enviar" }).waitFor({ state: "visible", timeout: replyTimeoutMs });
}

test.describe.configure({ mode: "serial" });

test.describe("Syntexa — checkup total (rotas + chat longo)", function () {
  test("fluxo completo", async function ({ page, context, baseURL }, testInfo) {
    test.setTimeout(5 * 60 * 60 * 1000);

    var rounds = parseInt(process.env.SYNTEXA_E2E_CHAT_ROUNDS || "100", 10);
    if (isNaN(rounds) || rounds < 1) rounds = 100;
    var delayMs = parseInt(process.env.SYNTEXA_E2E_CHAT_DELAY_MS || "2500", 10);
    var replyMs = parseInt(process.env.SYNTEXA_E2E_REPLY_MS || "180000", 10);
    var skipVoice = process.env.SYNTEXA_E2E_SKIP_VOICE === "1";
    var skipExports = process.env.SYNTEXA_E2E_SKIP_EXPORTS === "1";

    try {
      await context.grantPermissions(["microphone"], {
        origin: new URL(baseURL || "https://syntexabr.com.br").origin,
      });
    } catch (_) {}

    var bucket = { console: [], pageErrors: [], requestFailed: [], apiResponses: [] };
    attachTelemetryOnce(page, bucket);

    var report = {
      baseURL: baseURL || "",
      roundsRequested: rounds,
      startedAt: new Date().toISOString(),
      routes: [],
      chatRounds: [],
      voiceProbe: null,
      exportProbes: [],
      imageProbes: [],
      ttsProbes: [],
      finalTelemetry: null,
    };

    var routesDir = path.join(process.cwd(), "test-results", "checkup-routes");
    fs.mkdirSync(routesDir, { recursive: true });

    for (var r = 0; r < ROUTES.length; r++) {
      var route = ROUTES[r];
      var pe0 = bucket.pageErrors.length;
      var c0 = bucket.console.length;
      var rf0 = bucket.requestFailed.length;

      var res = await page.goto(route, { waitUntil: "networkidle", timeout: 90_000 });
      var status = res ? res.status() : 0;
      await page.waitForTimeout(600);
      var png = path.join(routesDir, shotName(route));
      await page.screenshot({ path: png, fullPage: true });

      report.routes.push({
        route: route,
        httpStatus: status,
        screenshot: png,
        pageErrors: bucket.pageErrors.slice(pe0),
        consoleIssues: bucket.console.slice(c0),
        requestFailed: bucket.requestFailed.slice(rf0),
      });
      expect(status, route + " status").toBeLessThan(500);
    }

    var prompts = buildCheckupPrompts(rounds);

    await page.goto("/chat/", { waitUntil: "networkidle", timeout: 90_000 });
    var ta = page.locator('textarea[placeholder="Digite sua mensagem..."]');
    await expect(ta).toBeVisible();

    for (var i = 0; i < prompts.length; i++) {
      var prompt = prompts[i];
      var t0 = Date.now();
      var roundLog = {
        index: i + 1,
        promptPreview: prompt.slice(0, 220),
        ok: false,
        durationMs: null,
        note: null,
      };

      try {
        await ta.fill(prompt);
        await page.getByRole("button", { name: "Enviar" }).click();
        await waitForChatIdle(page, replyMs);
        roundLog.ok = true;
        roundLog.durationMs = Date.now() - t0;

        var pl = prompt.toLowerCase();
        if (pl.indexOf("imagem") !== -1 || pl.indexOf("crie uma imagem") !== -1 || pl.indexOf("gere uma imagem") !== -1) {
          var hadImg = await page
            .locator('img[alt="Imagem gerada"]')
            .first()
            .isVisible()
            .catch(function () {
              return false;
            });
          report.imageProbes.push({ round: i + 1, visible: !!hadImg });
        }

        if (!skipExports && (i + 1) % 25 === 0) {
          try {
            var pdfBtn = page.getByRole("button", { name: "PDF" }).last();
            await expect(pdfBtn).toBeVisible({ timeout: 8000 });
            var dlPromise = page.waitForEvent("download", { timeout: 90_000 });
            await pdfBtn.click();
            var dlPdf = await dlPromise;
            var dp = await dlPdf.path();
            var st = dp && fs.existsSync(dp) ? fs.statSync(dp) : null;
            report.exportProbes.push({
              round: i + 1,
              kind: "pdf",
              bytes: st ? st.size : 0,
              ok: !!(st && st.size > 80),
            });
          } catch (ex) {
            report.exportProbes.push({
              round: i + 1,
              kind: "pdf",
              ok: false,
              err: String(ex && ex.message ? ex.message : ex),
            });
          }
        }

        if (!skipVoice && i === Math.min(49, prompts.length - 1)) {
          try {
            var voz = page.getByRole("button", { name: "Voz (IA)" });
            await voz.click({ timeout: 15_000 });
            await page.waitForTimeout(2000);
            var parar = page.getByRole("button", { name: "Parar" });
            await parar.click({ timeout: 15_000 });
            await waitForChatIdle(page, replyMs);
            report.voiceProbe = { ok: true };
          } catch (ev) {
            report.voiceProbe = { ok: false, err: String(ev && ev.message ? ev.message : ev) };
          }
        }

        if ((i + 1) % 30 === 0) {
          try {
            var ouvir = page.getByRole("button", { name: "Ouvir" }).last();
            if (await ouvir.isVisible()) {
              await ouvir.click();
              await page.waitForTimeout(2500);
              report.ttsProbes.push({ round: i + 1, audioCount: await page.locator("audio").count() });
            }
          } catch (eo) {
            report.ttsProbes.push({ round: i + 1, err: String(eo && eo.message ? eo.message : eo) });
          }
        }
      } catch (err) {
        roundLog.ok = false;
        roundLog.note = String(err && err.message ? err.message : err);
        roundLog.durationMs = Date.now() - t0;
      }

      report.chatRounds.push(roundLog);
      if (delayMs > 0) await page.waitForTimeout(delayMs);
    }

    await page.screenshot({
      path: path.join(process.cwd(), "test-results", "checkup-chat-final.png"),
      fullPage: true,
    });

    report.finalTelemetry = {
      pageErrors: bucket.pageErrors,
      console: bucket.console,
      requestFailed: bucket.requestFailed,
      apiSampleTail: bucket.apiResponses.slice(-500),
    };
    report.endedAt = new Date().toISOString();

    var outJson = path.join(process.cwd(), "test-results", "full-checkup-report.json");
    fs.writeFileSync(outJson, JSON.stringify(report, null, 2), "utf8");

    await testInfo.attach("full-checkup-report.json", {
      path: outJson,
      contentType: "application/json",
    });

    expect(bucket.pageErrors, "sem erros JS — corrigir hidratação no app").toEqual([]);

    var failedRounds = report.chatRounds.filter(function (x) {
      return !x.ok;
    });
    expect(
      failedRounds.length,
      "falhas no chat: " + JSON.stringify(failedRounds.slice(0, 5), null, 0)
    ).toBe(0);
  });
});
