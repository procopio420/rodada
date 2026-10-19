import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/parity', workers: 1, retries: 0,
  outputDir: './test-results/canonical-parity', reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:3136', browserName: 'chromium', locale: 'pt-BR', timezoneId: 'America/Sao_Paulo', trace: 'retain-on-failure' },
});
