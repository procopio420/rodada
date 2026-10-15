import { defineConfig } from "@playwright/test";

// This is an independent cross-client gate, not a variant of the Web-only
// fixture runner. The Android workflow owns the *same* PostgreSQL/Django stack.
const financial = process.env.RODADA_CROSS_PHASE === "financial";
export default defineConfig({
  testDir: financial ? "./tests/cross-surface-financial" : "./tests/cross-surface",
  testMatch: "*.spec.ts",
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: [["list"], ["html", { outputFolder: financial ? "playwright-report/android-cross-financial" : "playwright-report/android-cross-surface", open: "never" }]],
  outputDir: financial ? "./test-results/android-cross-financial" : "./test-results/android-cross-surface",
  use: {
    baseURL: "http://127.0.0.1:3110",
    browserName: "chromium",
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    viewport: { width: 390, height: 844 },
    trace: "on",
  },
});
