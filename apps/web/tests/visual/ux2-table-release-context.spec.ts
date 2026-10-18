import { expect, test } from '@playwright/test';
import { fixture } from './fixtures';
for (const ready of [true, false]) test(`table release requires resolved canonical deliveries, ready ${ready}`, async ({ page }) => {
  await fixture(page, 'normal', true);
  await page.route('**/api/auth/me', route => route.fulfill({ json: { staff: {id:'operator-test',display_name:'Operador'}, venue:{id:'venue-test',name:'Teste'}, session:{id:'session-test'}, capabilities:['table.manage','tab.open'] } }));
  const tab = { id: 'closed-tab', display_label: 'Marina', display_reference: '#1048', state: 'CLOSED', exposure_cents: 0, version: 2, orders: [], payments: [] };
  const table = { id: 'table-release', label: '08', status: 'OCCUPIED', active_occupancy: { id: 'occupancy-current', generation: 7, tabs: [tab] } };
  await page.route('**/api/attendance/hospitality/tables/', route => route.fulfill({ json: { table_service_enabled: true, results: [table] } }));
  let currentReady = ready;
  await page.route('**/api/attendance/dispatch/delivery/', route => route.fulfill({ json: { results: [{ id: 'ready-one', task_type: 'DELIVERY', state: 'OPEN', claimed_by_id: null, target_version: 1, target: { kind: 'TAB', tab_id: tab.id, table_id: table.id, occupancy_id: currentReady ? 'occupancy-current' : 'occupancy-old', generation: currentReady ? 7 : 6 }, product_name: 'Água', quantity: 1, age_seconds: 60, destination_label: 'Mesa 08', tab_label: 'Marina' }] } }));
  await page.route(/\/api\/attendance\/tabs\/closed-tab\/(\?.*)?$/, route => route.fulfill({ json: tab }));
  const writes: string[] = [];
  page.on('request', request => { if (request.method() !== 'GET' && request.url().includes('/api/attendance/')) writes.push(request.url()); });
  await page.goto('/attendance');
  await page.getByRole('button', { name: 'Mesas', exact: true }).click();
  await page.getByRole('button', { name: /Mesa 08 Ocupada/ }).click();
  if (ready) {
    await expect(page.getByText('1 entrega(s) ainda prontas.', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Grupo saiu · Liberar mesa', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Ver entregas prontas', exact: true }).click();
    await expect(page.getByRole('button', { name: /Entregas/ })).toHaveAttribute('aria-pressed', 'true');
    expect(writes).toEqual([]);
  } else {
    await expect(page.getByRole('button', { name: 'Grupo saiu · Liberar mesa', exact: true })).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Ver entregas prontas', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Grupo saiu · Liberar mesa', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Liberar mesa 08?', exact: true });
    await expect(dialog.getByRole('button', { name: 'Confirmar liberação', exact: true })).toBeEnabled();
    currentReady = true;
    await page.clock.runFor(16000);
    await expect(dialog.getByRole('button', { name: 'Confirmar liberação', exact: true })).toBeDisabled();
    await expect(dialog.getByText('Há comandas abertas ou entregas prontas. Cancele e confira a mesa.')).toBeVisible();
    currentReady = false;
    table.active_occupancy.id = 'occupancy-replacement';
    table.active_occupancy.generation = 8;
    await page.clock.runFor(16000);
    await expect(dialog.getByRole('button', { name: 'Confirmar liberação', exact: true })).toBeDisabled();
    await expect(dialog.getByText('A ocupação mudou. Cancele e confira a mesa novamente.')).toBeVisible();
    await dialog.getByRole('button', { name: 'Voltar', exact: true }).click();
    await page.locator('button[data-tab-id="closed-tab"]').click();
    await expect(page.getByRole('heading', { name: 'Marina', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: '＋ Adicionar itens', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Ver conta encerrada', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Conta encerrada.', exact: true })).toBeVisible();
    expect(writes).toEqual([]);
  }
});

 test('release sends the confirmed occupancy identity without a compatibility fallback', async ({page}) => {
  await fixture(page,'normal',true);
  await page.route('**/api/auth/me',r=>r.fulfill({json:{staff:{id:'operator-test'},venue:{id:'venue-test'},session:{id:'session-test'},capabilities:['table.manage','tab.open']}}));
  const occupancy={id:'18a56bf8-3043-4ed5-a5de-33bab1407df6',generation:7,tabs:[]};
  const table={id:'table-fenced',label:'08',status:'OCCUPIED',active_occupancy:occupancy};
  await page.route('**/api/attendance/hospitality/tables/',r=>r.fulfill({json:{table_service_enabled:true,results:[table]}}));
  await page.route('**/api/attendance/dispatch/delivery/',r=>r.fulfill({json:{results:[]}}));
  const bodies:unknown[]=[];
  await page.route('**/api/attendance/hospitality/tables/table-fenced/release/',r=>{bodies.push(r.request().postDataJSON());return r.fulfill({status:409,json:{code:'STALE_OCCUPANCY',message:'A ocupação mudou. Confira a mesa.'}});});
  await page.goto('/attendance'); await page.getByRole('button',{name:'Mesas',exact:true}).click();await page.getByRole('button',{name:/Mesa 08 Ocupada/}).click();
  await page.getByRole('button',{name:'Grupo saiu · Liberar mesa',exact:true}).click();
  await page.getByRole('button',{name:'Confirmar liberação',exact:true}).click();
  await expect(page.getByRole('dialog',{name:'Liberar mesa 08?',exact:true}).getByRole('alert')).toContainText('A ocupação mudou. Confira a mesa.');
  expect(bodies).toEqual([{expected_occupancy_id:occupancy.id,expected_generation:7}]);
  await expect(page.getByRole('heading',{name:'Mesa 08',exact:true})).toBeVisible();
 });
