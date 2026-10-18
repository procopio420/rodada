import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

// Dedicated disposable tenant from scripts/spec033-native-shell-fixture.py.
// Uses the same canonical Django/PostgreSQL fixture as native MainActivity.
// No HTTP mocking, seed/reset, payment, order submission or domain mutation.
for (const width of [360, 390, 430, 1280]) test(`canonical shell journey and contextual return ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  const domainWrites: string[] = [];
  page.on('request', request => {
    const path = new URL(request.url()).pathname;
    if (request.method() !== 'GET' && /^\/api\/attendance\//.test(path)) domainWrites.push(path);
  });
  await page.goto('/attendance');
  await page.getByLabel('Estabelecimento', { exact: true }).fill('spec033-native-shell-parity');
  await page.getByLabel('Operador', { exact: true }).fill('spec033-web-shell-operator');
  await page.getByLabel('PIN', { exact: true }).fill('2468');
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Agora', exact: true })).toBeVisible();
  const identity = await page.evaluate(async () => (await fetch('/api/auth/me')).json());
  expect(identity.venue.slug).toBe('spec033-native-shell-parity');
  const detail = await page.evaluate(async () => {
    const response = await fetch('/api/attendance/tabs/e4766bd9-05cd-43d8-ae49-c3f8712a66f1/');
    if (!response.ok) throw new Error(`Canonical readback ${response.status}`);
    return response.json();
  });
  expect(detail).toMatchObject({ id: 'e4766bd9-05cd-43d8-ae49-c3f8712a66f1', display_label: 'Marina', exposure_cents: 5600, effective_limit_cents: 20000 });
  const out = '../../docs/development/evidence/spec033-web-canonical-shell';
  await mkdir(out, { recursive: true });
  const capture = async (state: string) => page.screenshot({ path: `${out}/web-${state}-${width}.png`, fullPage: true });
  await capture('now');
  await page.getByRole('button', { name: 'Mesas', exact: true }).click();
  await expect(page.getByRole('button', { name: /Mesa 08 Ocupada/ })).toBeVisible();
  await capture('tables');
  await page.getByRole('button', { name: /Mesa 08 Ocupada/ }).click();
  await expect(page.getByRole('heading', { name: 'Mesa 08', exact: true })).toBeVisible();
  await capture('table');
  await page.locator('button[data-tab-id="e4766bd9-05cd-43d8-ae49-c3f8712a66f1"]').click();
  const workspace = page.getByRole('region', { name: 'Comanda selecionada', exact: true });
  await expect(workspace.getByRole('heading', { name: 'Marina', exact: true })).toBeVisible();
  await capture('tab');
  await workspace.getByRole('button', { name: '＋ Adicionar itens', exact: true }).click();
  await workspace.getByRole('button', { name: 'Adicionar Chopp Pilsen', exact: true }).click();
  await expect(workspace.getByRole('button', { name: /Enviar 1 item/ })).toBeEnabled();
  await expect(workspace.locator('.ux2Lede')).toHaveText('Marina · Mesa 08 · Destino fixo');
  await expect(workspace.getByText(/Mesa Mesa/)).toHaveCount(0);
  await capture('catalog');
  await workspace.getByRole('button', { name: 'Ver resumo', exact: true }).click();
  await expect(workspace.getByText('1× Chopp Pilsen', { exact: true })).toBeVisible();
  await capture('review');
  await workspace.getByRole('button', { name: 'Voltar', exact: true }).click();
  await expect(workspace.getByRole('button', { name: /Enviar 1 item/ })).toBeEnabled();
  await workspace.getByRole('button', { name: 'Voltar', exact: true }).click();
  await expect(workspace.getByRole('heading', { name: 'Marina', exact: true })).toBeVisible();
  await workspace.getByRole('button', { name: 'Voltar', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Mesa 08', exact: true })).toBeVisible();
  expect(domainWrites).toEqual([]);
});
