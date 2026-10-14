import { expect, test, type Page } from "./fixtures";

async function api(page: Page, path: string, body?: unknown) {
  return page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(`${response.status} ${JSON.stringify(result)}`);
    return result;
  }, { path, body });
}

for (const correction of [false, true]) for (const width of [360, 390, 430]) test(`PostgreSQL ${correction ? "correction" : "manual refund"} lost committed response recovers at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const key = `refund-${correction}-${width}`;
  const point = (await api(page, "cash/points/")).results[0];
  const shift = point.active_shift ?? await api(page, "cash/shifts/", {
    cash_point_id: point.id, opening_float_cents: 0, business_date: "2026-10-12", idempotency_key: `${key}-shift`,
  });
  const beforeShift = await api(page, `cash/shifts/${shift.id}/`);
  const products = (await api(page, "catalog/products/")).results.filter((p: { name: string }) => ["Kitchen E2E item", "Bar E2E item"].includes(p.name));
  expect(products).toHaveLength(2);
  const tab = await api(page, "tabs/", { display_label: `Refund recovery ${correction ? "correction" : "manual"} ${width}` });
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: `${key}-order`, lines: products.map((p: { id: string }) => ({ product_id: p.id, quantity: 1 })) });
  const payment = await api(page, `tabs/${tab.id}/payments/`, { amount_cents: 1000, method: "CASH", cash_point_id: point.id, idempotency_key: `${key}-payment` });
  const before = await api(page, `tabs/${tab.id}/`);
  expect(before.exposure_cents).toBe(500);
  let pending: { id: string } | null = null;
  if (correction) {
    const item = before.orders[0].items.find((i: { product_name: string }) => i.product_name === "Kitchen E2E item");
    pending = await api(page, `order-items/${item.id}/corrections/cancel/`, { kind: "CANCEL_ITEM", reason_code: "WRONG_ENTRY", idempotency_key: `${key}-cancel` });
  }
  const bodies: string[] = []; let refundId = "";
  const endpoint = correction ? `corrections/${pending!.id}/settle-refund` : `payments/${payment.id}/refunds`;
  await page.route(new RegExp(`/api/pos/${endpoint}/?$`), async route => {
    bodies.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(bodies.length === 1 ? 201 : 200);
    const body = await response.json(); const id = correction ? body.refund_id : body.id;
    if (!refundId) refundId = id; else expect(id).toBe(refundId);
    if (bodies.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption(tab.id);
  await page.getByLabel("PIN do gerente").fill("2468");
  await page.getByRole("button", { name: "Confirmar PIN", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("PIN confirmado");
  if (!correction) {
    await page.getByLabel("Valor a estornar").fill("5,00");
    await page.getByLabel("Motivo do estorno").fill("Isolated refund recovery test");
  }
  await page.getByRole("button", { name: correction ? "Estornar R$ 5,00" : "Confirmar estorno", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo estorno" }); await expect(verify).toBeEnabled();
  const committed = await api(page, `tabs/${tab.id}/`);
  expect(committed.refunds_cents).toBe(500); expect(committed.exposure_cents).toBe(correction ? 0 : 1000);
  expect(committed.payments).toHaveLength(1); expect(committed.payments[0].id).toBe(payment.id);
  expect(committed.payments[0].amount_cents).toBe(1000);
  expect(committed.payments[0].confirmed_at).toBe(before.payments[0].confirmed_at);
  expect(committed.payments[0].refunds).toHaveLength(1); expect(committed.payments[0].refunds[0].id).toBe(refundId);
  await page.reload(); await expect(verify).toBeEnabled(); expect(bodies).toHaveLength(1);
  await verify.click(); await expect(page.getByText(/^Estorno confirmado\./)).toBeVisible();
  expect(bodies[1]).toBe(bodies[0]);
  const after = await api(page, `tabs/${tab.id}/`);
  expect(after.payments).toEqual(committed.payments);
  expect(after.exposure_cents).toBe(committed.exposure_cents);
  expect(after.adjustments_cents).toBe(correction ? -1000 : 0);
  const afterShift = await api(page, `cash/shifts/${shift.id}/`);
  expect(afterShift.expected_cents - beforeShift.expected_cents).toBe(500);
  expect(afterShift.movements.filter((m: { refund_id: string }) => m.refund_id === refundId)).toHaveLength(1);
  expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.refund.v1"))).toBeNull();
});
