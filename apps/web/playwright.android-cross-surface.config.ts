import { defineConfig } from "@playwright/test";

// This is an independent cross-client gate, not a variant of the Web-only
// fixture runner. The Android workflow owns the *same* PostgreSQL/Django stack.
export default defineConfig({
  testDir: "./tests/cross-surface",
  testMatch: "*.spec.ts",
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: [["list"], ["html", { outputFolder: "playwright-report/android-cross-surface", open: "never" }]],
  outputDir: "./test-results/android-cross-surface",
  use: {
    baseURL: "http://127.0.0.1:3110",
    browserName: "chromium",
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    viewport: { width: 390, height: 844 },
    trace: "on",
  },
});
