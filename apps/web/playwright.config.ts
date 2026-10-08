import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/visual",
  outputDir: "./test-results",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:3100",
    browserName: "chromium",
    deviceScaleFactor: 1,
    viewport: { width: 390, height: 844 },
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    colorScheme: "dark",
  },
  webServer: {
    command: "npm run dev -- --hostname 127.0.0.1 --port 3100",
    url: "http://127.0.0.1:3100",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
