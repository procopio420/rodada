import { defineConfig } from "@playwright/test";
const apiPort = Number(process.env.RODADA_E2E_API_PORT ?? 8100);
const webPort = Number(process.env.RODADA_E2E_WEB_PORT ?? 3110);

export default defineConfig({
  testDir: "./tests/integration",
  outputDir: "./test-results/integration",
  workers: 1, fullyParallel: false, forbidOnly: !!process.env.CI, retries: 0,
  reporter: [["list"], ["html", { outputFolder: "playwright-report/integration", open: "never" }]],
  use: { baseURL: `http://127.0.0.1:${webPort}`, browserName: "chromium", locale: "pt-BR", timezoneId: "America/Sao_Paulo", viewport: { width: 390, height: 844 }, trace: "retain-on-failure" },
  webServer: [
    { command: `"${process.env.RODADA_TEST_PYTHON ?? "python"}" tests/integration/start_api.py`, url: `http://127.0.0.1:${apiPort}/ready/`, reuseExistingServer: false, timeout: 120_000 },
    { command: `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port ${webPort}`, url: `http://127.0.0.1:${webPort}/staff`, reuseExistingServer: false, timeout: 120_000, env: { RODADA_API_BASE_URL: `http://127.0.0.1:${apiPort}` } },
  ],
});
