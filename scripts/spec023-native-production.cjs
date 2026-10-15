// Test-only: real Web production UI for the canonical-menu native shift.
const { chromium } = require('../apps/web/node_modules/playwright');
const { readFile, writeFile, mkdir } = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const base = process.env.RODADA_NATIVE_SHIFT_WEB ?? 'http://127.0.0.1:3144';
  assert.equal(new URL(base).hostname, '127.0.0.1', 'Only the isolated local test server is accepted');
  const out = path.resolve(__dirname, '../visual-artifacts/spec023-024/runtime/native-ui');
  const saved = JSON.parse(await readFile(path.join(out, 'native-tab.json'), 'utf8'));
  const labels = saved.filter(n => n.text.startsWith('Spec023 test ')).map(n => n.text);
  assert.equal(labels.length, 1);
  const label = labels[0];
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ baseURL: base, viewport: { width: 1280, height: 800 } });
    await page.goto('/staff');
    await page.getByLabel('Estabelecimento').fill('release-demo');
    await page.getByLabel('Operador', { exact: true }).fill('release-owner');
    await page.getByLabel('PIN', { exact: true }).fill('2468');
    await page.getByRole('button', { name: 'Entrar', exact: true }).click();
    await page.getByText('Sessão operacional ativa').waitFor();
    for (const [station, name] of [['bar', 'Brahma 600 ml'], ['kitchen', 'Coxinha de Queijo com Alho']]) {
      await page.goto('/' + station);
      const order = page.getByRole('group', { name: 'Pedido: ' + label });
      await order.getByText('1 ' + name, { exact: true }).waitFor();
      await order.getByRole('button', { name: /^Iniciar preparo:/ }).click();
      await order.getByRole('button', { name: /^Pronto:/ }).waitFor();
      await order.getByRole('button', { name: /^Pronto:/ }).click();
      await page.locator('.stationPassRow').filter({ hasText: label }).getByText('1 ' + name, { exact: true }).waitFor();
      await mkdir(out, { recursive: true });
      await page.screenshot({ path: path.join(out, 'native-shift-production-' + station + '.png'), fullPage: true });
    }
    const result = await page.evaluate(async label => {
      const tabs = (await (await fetch('/api/pos/tabs/')).json()).results;
      const tab = tabs.find(t => t.display_label === label);
      return (await fetch('/api/pos/tabs/' + tab.id + '/')).json();
    }, label);
    assert.equal(result.orders.length, 1);
    assert.equal(result.orders[0].items.length, 2);
    assert.ok(result.orders[0].items.every(i => i.state === 'READY'));
    assert.equal(result.charges_cents, 1550);
    assert.equal(result.payments_cents, 0);
    await writeFile(path.join(out, 'production.result.json'), JSON.stringify({
      result: 'PASS', surface: 'real Web BAR/KITCHEN UI', nativeTab: result.id,
      orders: 1, items: 2, charges_cents: 1550, payments_cents: 0,
      items_ready: result.orders[0].items.map(i => ({ name: i.product_name, station: i.fulfillment_station, state: i.state, unit_price_cents: i.unit_price_cents })),
    }, null, 2) + '\n');
    console.log('PASS: native order prepared and marked ready through real BAR/KITCHEN UI');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
