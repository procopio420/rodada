import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/integration",
  outputDir: "./test-results/integration",
  workers: 1, fullyParallel: false, forbidOnly: !!process.env.CI, retries: 0,
  reporter: [["list"], ["html", { outputFolder: "playwright-report/integration", open: "never" }]],
  use: { baseURL: "http://127.0.0.1:3110", browserName: "chromium", locale: "pt-BR", timezoneId: "America/Sao_Paulo", viewport: { width: 390, height: 844 }, trace: "retain-on-failure" },
  webServer: [
    { command: `"${process.env.RODADA_TEST_PYTHON ?? "python"}" tests/integration/start_api.py`, url: "http://127.0.0.1:8100/ready/", reuseExistingServer: false, timeout: 120_000 },
    { command: "node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3110", url: "http://127.0.0.1:3110/staff", reuseExistingServer: false, timeout: 120_000, env: { RODADA_API_BASE_URL: "http://127.0.0.1:8100" } },
  ],
});
