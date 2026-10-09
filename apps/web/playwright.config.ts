import { defineConfig } from "@playwright/test";
const appPort = Number(process.env.RODADA_VISUAL_PORT ?? 3100);
const referencePort = Number(process.env.RODADA_REFERENCE_PORT ?? 3101);

export default defineConfig({
  testDir: "./tests/visual",
  outputDir: "./test-results/visual",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: `http://127.0.0.1:${appPort}`,
    browserName: "chromium",
    deviceScaleFactor: 1,
    viewport: { width: 390, height: 844 },
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    colorScheme: "dark",
    trace: "retain-on-failure",
  },
  webServer: [{
    command: `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port ${appPort}`,
    url: `http://127.0.0.1:${appPort}`,
    reuseExistingServer: false,
    timeout: 120_000,
  }, {
    command: `python3 -m http.server ${referencePort} --bind 127.0.0.1 --directory ../..`,
    url: `http://127.0.0.1:${referencePort}/prototype/references/`,
    reuseExistingServer: false,
  }],
});
