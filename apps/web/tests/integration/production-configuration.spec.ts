import { expect, test } from "./fixtures";

for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Real confirmed production configurations ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`); return response.json();
  }, { path, body });
  const name = `Configuration ${station} ${width}`;
  const { product } = await api("catalog/resolve-or-create/", { name, price_cents: 100, fulfillment_station: station });
  const configure = (body: unknown) => api(`catalog/products/${product.id}/customization/`, body);
  await configure({ kind: "variant", values: { name: "Simples", price_cents: 100, is_default: true } });
  await configure({ kind: "variant", values: { name: "Grande", price_cents: 200 } });
  await configure({ kind: "group", values: { name: "Adicionais", selection_mode: "MULTI", min_selections: 0, max_selections: 2 } });
  let schema = await configureSchema();
  const group = schema.modifier_groups[0];
  await configure({ kind: "option", group_id: group.id, values: { name: "Queijo", price_delta_cents: 50, semantic_kind: "ADD" } });
  schema = await configureSchema();
  const small = schema.variants.find((v: { name: string }) => v.name === "Simples"), large = schema.variants.find((v: { name: string }) => v.name === "Grande"), option = schema.modifier_groups[0].options[0];
  async function configureSchema() { return (await api("catalog/products/")).results.find((p: { id: string }) => p.id === product.id); }
  const tab = await api("tabs/", { display_label: `T${width}${station[0]}` });
  const plain = { product_id: product.id, variant_id: small.id, quantity: 1 };
  const payload = { idempotency_key: `configuration-${station}-${width}`, lines: [plain, { ...plain, quantity: 2 }, { ...plain, variant_id: large.id }, { ...plain, special_instructions: "Sem sal" }, { ...plain, modifier_option_ids: [option.id] }] };
  const order = await api(`tabs/${tab.id}/orders/confirm/`, payload);
  expect((await api(`tabs/${tab.id}/orders/confirm/`, payload)).id).toBe(order.id);
  const before = await api(`tabs/${tab.id}/`);
  await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
  const groups = page.locator(".stationDish").filter({ has: page.locator(".stationDishHeading strong", { hasText: name }) });
  await expect(groups).toHaveCount(4); await expect(groups.locator(".stationQuantity")).toHaveText(["3", "1", "1", "1"]);
  await expect(groups.nth(0)).toContainText("Variação: Simples"); await expect(groups.nth(1)).toContainText("Variação: Grande"); await expect(groups.nth(2)).toContainText("Observação: Sem sal"); await expect(groups.nth(3)).toContainText("+ Queijo");
  expect(await api(`tabs/${tab.id}/`)).toEqual(before);
  await page.screenshot({ path: `test-results/production-configuration-real-${station}-${width}.png` });
  await configure({ kind: "variant", id: large.id, expected_version: large.version, values: { name: "Grande revisado", price_cents: 300 } });
  await api(`catalog/products/${product.id}/availability/`, { state: "UNAVAILABLE" });
  await page.reload(); await expect(groups).toHaveCount(4); await expect(groups.nth(1)).toContainText("Variação: Grande"); await expect(groups.nth(1)).not.toContainText("revisado");
  expect(await api(`tabs/${tab.id}/`)).toEqual(before);
  expect(before.orders).toHaveLength(1); expect(before.orders[0].items).toHaveLength(5); expect(before.charges_cents).toBe(750); expect(before.payments_cents).toBe(0);
  await page.getByRole("navigation", { name: "Regiões da produção" }).getByRole("button", { name: /^Fila/ }).click();
  await page.getByRole("button", { name: new RegExp(`^Iniciar preparo:.*${name}`) }).first().click();
  await expect(page.getByRole("button", { name: new RegExp(`^Pronto:.*${name}`) })).toBeEnabled();
  const after = await api(`tabs/${tab.id}/`);
  expect(after.orders[0].items.filter((i: { state: string }) => i.state === "PREPARING")).toHaveLength(1);
  expect(after.orders[0].items.map((i: { customization_snapshot: unknown }) => i.customization_snapshot)).toEqual(before.orders[0].items.map((i: { customization_snapshot: unknown }) => i.customization_snapshot));
  for (const field of ["exposure_cents", "charges_cents", "payments_cents", "payments"]) expect(after[field]).toEqual(before[field]);
});
