// @ts-check
const { defineConfig, devices } = require("@playwright/test");

/** Base URL: produção por omissão; override: SYNTEXA_E2E_BASE=http://localhost:3000 */
const baseURL = process.env.SYNTEXA_E2E_BASE || "https://syntexabr.com.br";

module.exports = defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 150_000,
  expect: { timeout: 30_000 },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
    ["json", { outputFile: "test-results/e2e-results.json" }],
  ],
  use: {
    ...devices["Desktop Chrome"],
    baseURL,
    locale: "pt-BR",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    ignoreHTTPSErrors: false,
    /** Microfone falso no Chromium (teste «Voz (IA)» sem hardware). */
    launchOptions: {
      args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"],
    },
  },
});
