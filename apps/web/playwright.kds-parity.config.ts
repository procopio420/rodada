import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/kds-parity",
  outputDir: "./test-results/kds-parity",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env.CI,
  reporter: [["list"], ["html", { open: "never", outputFolder: "test-results/kds-parity-html" }]],
  timeout: 60_000,
  use: {
    browserName: "chromium",
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    locale: "pt-BR",
    timezoneId: "America/Fortaleza",
    colorScheme: "dark",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "infra", testMatch: "infrastructure.spec.ts" },
    { name: "application", testMatch: "application.spec.ts" },
  ],
});
