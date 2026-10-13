import { expect, test } from "./test";
for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Real independent production ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`); return response.json();
  }, { path, body });
  const name = `Independent ${station} ${width}`;
  const { product } = await api("catalog/resolve-or-create/", { name, price_cents: 100, fulfillment_station: station });
  const tabs = [];
  for (const suffix of ["A", "B"]) {
    const tab = await api("tabs/", { display_label: `${name} ${suffix}` });
    await api(`tabs/${tab.id}/orders/confirm/`, { idempotency_key: `${name}-${suffix}`, lines: [{ product_id: product.id, quantity: suffix === "A" ? 2 : 1, special_instructions: suffix }] });
    tabs.push(await api(`tabs/${tab.id}/`));
  }
  await api(`tabs/${tabs[0].id}/payments/`, { amount_cents: 100, method: "EXTERNAL_TERMINAL", idempotency_key: `${name}-payment` });
  const a = tabs[0].orders[0].items[0], b = tabs[1].orders[0].items[0];
  await api(`order-items/${a.id}/transition/`, { state: "PREPARING" });
  const before = await Promise.all(tabs.map(tab => api(`tabs/${tab.id}/`)));
  let release!: () => void; const held = new Promise<void>(resolve => { release = resolve; });
  const attempts: string[] = [], commandIds: string[] = [];
  await page.route("**/api/pos/production/batches/", async route => {
    const index = attempts.push(route.request().postData()!) - 1;
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(200); commandIds[index] = (await response.json()).command_id;
    if (index === 0) { await held; await route.abort(); } else await route.fulfill({ response });
  });
  try {
    await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
    await page.getByRole("button", { name: `Pronto: 2 ${name}, ${name} A`, exact: true }).click();
    await expect.poll(() => commandIds.length).toBe(1);
    await expect(page.getByRole("button", { name: `Pronto: 2 ${name}, ${name} A`, exact: true })).toBeDisabled();
    await page.getByRole("button", { name: `Iniciar preparo: 1 ${name}, ${name} B`, exact: true }).click();
    await expect(page.getByText(`Item confirmado. · ${b.id.slice(0, 8)}`, { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(2); release();
    const recover = page.getByRole("button", { name: `Verificar mesmo item: ${a.id.slice(0, 8)}`, exact: true });
    await expect(recover).toBeEnabled(); await page.reload(); await expect(recover).toBeEnabled();
    await page.screenshot({ path: `test-results/production-independent-real-${station}-${width}.png` });
    await recover.dblclick(); await expect(page.getByText(`Item confirmado. · ${a.id.slice(0, 8)}`, { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(3); expect(attempts[2]).toBe(attempts[0]); expect(commandIds[2]).toBe(commandIds[0]);
    await page.getByRole("button", { name: `Pronto: 1 ${name}, ${name} B`, exact: true }).click();
    await expect(page.getByText(`Item confirmado. · ${b.id.slice(0, 8)}`, { exact: true })).toBeVisible();
    const after = await Promise.all(tabs.map(tab => api(`tabs/${tab.id}/`)));
    for (let i = 0; i < 2; i++) {
      expect(after[i].orders[0].items[0].state).toBe("READY");
      expect(after[i].orders[0].items[0].customization_snapshot).toEqual(before[i].orders[0].items[0].customization_snapshot);
      for (const field of ["charges_cents", "payments_cents", "exposure_cents", "payments"]) expect(after[i][field]).toEqual(before[i][field]);
    }
    expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.production-items.v1"))).toBeNull();
    const dispatch = await api("dispatch/delivery/");
    expect(dispatch.results.filter((task: { order_item_id?: string }) => [a.id, b.id].includes(task.order_item_id))).toHaveLength(2);
  } finally { release(); }
});
