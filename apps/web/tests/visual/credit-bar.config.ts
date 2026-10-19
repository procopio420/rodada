import { defineConfig } from "@playwright/test";
/** Standalone real React render: no production test route, API, or financial mutation. */
export default defineConfig({
  testDir: ".", testMatch: "attendance-credit-bar.spec.ts", workers: 1,
  outputDir: "../../test-results/credit-bar", reporter: "list",
  use: { browserName: "chromium", viewport: { width: 390, height: 844 }, locale: "pt-BR", colorScheme: "dark" },
});
