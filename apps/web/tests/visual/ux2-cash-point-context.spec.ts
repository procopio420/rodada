import { expect, test } from '@playwright/test';
import { fixture } from './fixtures';

for (const lostAck of [false, true]) test(`UX2 keeps cash context after point removal, lost ACK ${lostAck}`, async ({ page }) => {
  await fixture(page, 'normal', true);
  const tab = { id: 'point-tab', display_label: 'Marina', table_label: '08', state: 'OPEN', version: 1, exposure_cents: 2400, orders: [], payments: [] as { id: string; method: string; status: string; amount_cents: number }[] };
  let points = [{ id: 'point-a', label: 'Caixa A', active_shift: { id: 'shift-a' } }, { id: 'point-b', label: 'Caixa B', active_shift: { id: 'shift-b' } }];
  await page.route('**/api/attendance/cash/points/', route => route.fulfill({ json: { results: points } }));
  await page.route('**/api/attendance/hospitality/tables/', route => route.fulfill({ json: { table_service_enabled: true, results: [{ id: 'point-table', label: '08', status: 'OCCUPIED', active_occupancy: { id: 'point-visit', generation: 1, tabs: [tab] } }] } }));
  await page.route(/\/api\/attendance\/tabs\/point-tab\/(\?.*)?$/, route => route.fulfill({ json: tab }));
  const requests: { cash_point_id: string; amount_cents: number; idempotency_key: string }[] = [];
  const confirmed = new Map<string, typeof tab.payments[number]>();
  await page.route('**/api/attendance/tabs/point-tab/payments/', route => {
    const request = route.request().postDataJSON(); requests.push(request);
    let payment = confirmed.get(request.idempotency_key);
    if (!payment) {
      payment = { id: `payment-${confirmed.size + 1}`, method: 'CASH', status: 'CONFIRMED', amount_cents: request.amount_cents };
      confirmed.set(request.idempotency_key, payment);
      tab.payments.push(payment); tab.exposure_cents -= request.amount_cents; tab.version++;
    }
    if (lostAck && requests.length === 1) return route.abort();
    return route.fulfill({ json: payment });
  });
  await page.goto('/attendance');
  await page.getByRole('button', { name: 'Mesas', exact: true }).click();
  await page.getByRole('button', { name: /Mesa 08 Ocupada/ }).click();
  await page.locator('button[data-tab-id="point-tab"]').click();
  await page.getByRole('button', { name: 'Conferir / fechar conta', exact: true }).click();
  const receipt = page.getByRole('region', { name: 'Recebimento em dinheiro', exact: true });
  await receipt.getByRole('button', { name: 'Receber R$ 24,00', exact: true }).click();
  await receipt.getByLabel('Caixa aberto', { exact: true }).selectOption('point-b');
  await receipt.getByLabel('Valor recebido (R$)', { exact: true }).fill('5,00');
  await receipt.getByRole('button', { name: 'Registrar recebimento', exact: true }).click();
  if (lostAck) {
    const verify = receipt.getByRole('button', { name: 'Verificar mesmo recebimento', exact: true });
    await expect(verify).toBeEnabled();
    const original = await page.evaluate(() => sessionStorage.getItem('rodada.intent.pos-cash.v1'));
    points = [points[0]]; await page.clock.runFor(16000);
    expect(await page.evaluate(() => sessionStorage.getItem('rodada.intent.pos-cash.v1'))).toBe(original);
    await verify.click();
    await expect(receipt.getByText('Recebimento confirmado. Saldo atualizado.', { exact: true })).toBeVisible();
    expect(requests[1]).toEqual(requests[0]);
    expect(tab.payments).toHaveLength(1); expect(tab.exposure_cents).toBe(1900);
  }
  await expect(receipt.getByText('Recebimento confirmado. Saldo atualizado.', { exact: true })).toBeVisible();
  const firstAttempts = lostAck ? 2 : 1;
  expect(requests).toHaveLength(firstAttempts); expect(requests[0]).toMatchObject({ cash_point_id: 'point-b', amount_cents: 500 });
  await receipt.getByRole('button', { name: 'Receber R$ 19,00', exact: true }).click();
  points = [points[0]];
  await page.clock.runFor(16000);
  await expect(receipt.getByLabel('Caixa aberto', { exact: true }).getByRole('option', { name: 'Caixa B', exact: true })).toHaveCount(0);
  await expect(receipt.getByRole('button', { name: 'Receber e encerrar comanda', exact: true })).toBeDisabled();
  await expect(receipt.getByRole('button', { name: 'Só registrar; manter comanda aberta', exact: true })).toBeDisabled();
  expect(requests).toHaveLength(firstAttempts);
  await receipt.getByLabel('Caixa aberto', { exact: true }).selectOption('point-a');
  await receipt.getByLabel('Valor recebido (R$)', { exact: true }).fill('4,00');
  await receipt.getByRole('button', { name: 'Registrar recebimento', exact: true }).click();
  await expect(receipt.getByText('Recebimento confirmado. Saldo atualizado.', { exact: true })).toBeVisible();
  expect(requests).toHaveLength(firstAttempts + 1); expect(requests.at(-1)).toMatchObject({ cash_point_id: 'point-a', amount_cents: 400 });
});
