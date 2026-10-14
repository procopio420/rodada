import { expect, test } from "./fixtures";
for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Real production batch recovery ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`); return response.json();
  }, { path, body });
  const name = `Batch ${station} ${width}`;
  const { product } = await api("catalog/resolve-or-create/", { name, price_cents: 100, fulfillment_station: station });
  const tab = await api("tabs/", { display_label: `Batch ${width} ${station}` });
  await api(`tabs/${tab.id}/orders/confirm/`, { idempotency_key: `batch-order-${station}-${width}`, lines: [
    { product_id: product.id, quantity: 2, special_instructions: "Sem sal" },
    { product_id: product.id, quantity: 1, special_instructions: "Sem sal" }] });
  await api(`tabs/${tab.id}/payments/`, { amount_cents: 100, method: "EXTERNAL_TERMINAL", idempotency_key: `batch-test-payment-${station}-${width}` });
  const before = await api(`tabs/${tab.id}/`); await api(`catalog/products/${product.id}/availability/`, { state: "UNAVAILABLE" });
  await api(`catalog/products/${product.id}/availability/`, { state: "AVAILABLE" });
  const independent = await api("tabs/", { display_label: `Independent ${station} ${width}` });
  await api(`tabs/${independent.id}/orders/confirm/`, { idempotency_key: `independent-batch-${station}-${width}`, lines: [{ product_id: product.id, quantity: 1, special_instructions: "Outra configuração" }] });
  const independentBefore = await api(`tabs/${independent.id}/`);
  await api(`catalog/products/${product.id}/availability/`, { state: "UNAVAILABLE" });
  const attempts: string[] = []; const commandIds: string[] = [];
  await page.route("**/api/pos/production/batches/", async route => {
    attempts.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(200); const receipt = await response.json(); commandIds.push(receipt.command_id);
    if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
  const select = page.getByRole("button", { name: `Selecionar preparo: ${name}`, exact: true }); await select.click();
  const dialog = page.getByRole("dialog"); await expect(dialog.getByRole("checkbox").first()).not.toBeChecked();
  await dialog.getByRole("checkbox").first().check(); await dialog.getByRole("checkbox").last().check();
  await page.screenshot({ path: `test-results/production-batch-real-${station}-${width}.png` });
  await dialog.getByRole("button", { name: "Iniciar preparo selecionado", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo lote", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: `Iniciar preparo: 1 ${name}, Independent ${station} ${width}`, exact: true }).click();
  await expect(page.getByText(/Item confirmado/)).toBeVisible();
  await page.reload(); await page.getByRole("button", { name: "Verificar mesmo lote", exact: true }).dblclick();
  await expect(page.getByText("Lote confirmado.", { exact: true })).toBeVisible();
  expect(attempts).toHaveLength(3); expect(attempts[0]).toBe(attempts[2]); expect(commandIds[0]).toBe(commandIds[2]);
  await page.getByRole("button", { name: `Selecionar prontos: ${name}`, exact: true }).click();
  await dialog.getByRole("checkbox").first().check(); await dialog.getByRole("checkbox").last().check();
  await dialog.getByRole("button", { name: "Marcar selecionados como prontos", exact: true }).click();
  await expect(page.getByRole("button", { name: `Selecionar prontos: ${name}`, exact: true })).toHaveCount(0);
  await expect(page.getByText("Lote confirmado.", { exact: true })).toBeVisible();
  const after = await api(`tabs/${tab.id}/`);
  expect(after.orders[0].items.map((item: { state: string }) => item.state)).toEqual(["READY", "READY"]);
  expect(after.orders[0].items.map((item: { customization_snapshot: unknown }) => item.customization_snapshot)).toEqual(before.orders[0].items.map((item: { customization_snapshot: unknown }) => item.customization_snapshot));
  for (const field of ["charges_cents", "payments_cents", "exposure_cents", "payments"]) expect(after[field]).toEqual(before[field]);
  const pending = await page.evaluate(() => sessionStorage.getItem("rodada.intent.production-batch.v1")); expect(pending).toBeNull();
  const independentAfter = await api(`tabs/${independent.id}/`);
  expect(independentAfter.orders[0].items[0].state).toBe("PREPARING");
  expect(independentAfter.orders[0].items[0].customization_snapshot).toEqual(independentBefore.orders[0].items[0].customization_snapshot);
  for (const field of ["charges_cents", "payments_cents", "exposure_cents", "payments"]) expect(independentAfter[field]).toEqual(independentBefore[field]);
  const dispatch = await api("dispatch/delivery/");
  expect(dispatch.results.filter((task: { order_item_id?: string }) => after.orders[0].items.some((item: { id: string }) => task.order_item_id === item.id))).toHaveLength(2);
});
