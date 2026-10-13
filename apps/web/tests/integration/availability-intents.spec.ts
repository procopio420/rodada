import { expect, test } from "./test";
for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Real availability recovery ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`); return response.json();
  }, { path, body });
  const name = `Availability ${station} ${width}`;
  const { product } = await api("catalog/resolve-or-create/", { name, price_cents: 100, fulfillment_station: station });
  const { product: other } = await api("catalog/resolve-or-create/", { name: `${name} other`, price_cents: 200, fulfillment_station: station });
  const tab = await api("tabs/", { display_label: name });
  await api(`tabs/${tab.id}/orders/confirm/`, { idempotency_key: `${name}-order`, lines: [{ product_id: product.id, quantity: 2 }] });
  await api(`tabs/${tab.id}/payments/`, { amount_cents: 100, method: "EXTERNAL_TERMINAL", idempotency_key: `${name}-payment` });
  const before = await api(`tabs/${tab.id}/`), item = before.orders[0].items[0];
  let release!: () => void; const held = new Promise<void>(resolve => { release = resolve; }); const attempts: string[] = [], receipts: any[] = [];
  await page.route(`**/api/pos/catalog/products/${product.id}/availability/`, async route => {
    const index = attempts.push(route.request().postData()!) - 1;
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(200); receipts[index] = await response.json();
    if (index === 0) { await held; return route.abort(); } await route.fulfill({ response });
  });
  try {
    await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
    await page.getByRole("button", { name: `Indisponibilizar ${name}`, exact: true }).click(); await expect.poll(() => receipts.length).toBe(1);
    await page.getByRole("button", { name: `Indisponibilizar ${name} other`, exact: true }).click();
    await expect(page.getByText(`Disponibilidade confirmada. · ${other.id.slice(0, 8)}`, { exact: true })).toBeVisible();
    await page.getByRole("button", { name: `Iniciar preparo: 2 ${name}, ${name}`, exact: true }).click(); await expect(page.getByText(`Item confirmado. · ${item.id.slice(0, 8)}`, { exact: true })).toBeVisible();
    release(); const retry = page.getByRole("button", { name: `Verificar mesma disponibilidade: ${product.id.slice(0, 8)}`, exact: true });
    await expect(retry).toBeEnabled(); await page.reload(); await expect(retry).toBeEnabled();
    await page.screenshot({ path: `test-results/availability-real-${station}-${width}.png`, fullPage: true });
    await retry.dblclick(); await expect(page.getByText(`Disponibilidade confirmada. · ${product.id.slice(0, 8)}`, { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(2); expect(attempts[1]).toBe(attempts[0]); expect(receipts[1]).toEqual(receipts[0]);
    const catalog = await api("catalog/products/"); expect(catalog.results.find((p: any) => p.id === product.id).availability_version).toBe(receipts[0].version);
    const after = await api(`tabs/${tab.id}/`);
    expect(after.orders[0].items[0].state).toBe("PREPARING"); expect(after.orders[0].items[0].customization_snapshot).toEqual(item.customization_snapshot);
    for (const field of ["charges_cents", "payments_cents", "exposure_cents", "payments"]) expect(after[field]).toEqual(before[field]);
    expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.availability.v1"))).toBeNull();
  } finally { release(); }
});
