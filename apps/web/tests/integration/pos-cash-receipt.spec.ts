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

test("POS lost cash response after PostgreSQL commit survives reload with one drawer effect", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const point = (await api(page, "cash/points/")).results[0];
  const shift = point.active_shift ?? await api(page, "cash/shifts/", {
    cash_point_id: point.id, opening_float_cents: 0, business_date: "2026-10-12", idempotency_key: "t03-cash-shift",
  });
  const beforeShift = await api(page, `cash/shifts/${shift.id}/`);
  const product = (await api(page, "catalog/products/")).results.find((p: { name: string }) => p.name === "Kitchen E2E item");
  const tab = await api(page, "tabs/", { display_label: "Cash recovery E2E" });
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: "t03-cash-order", lines: [{ product_id: product.id, quantity: 2 }] });
  const requests: string[] = []; let paymentId = "";
  await page.route(new RegExp(`/api/pos/tabs/${tab.id}/payments/?$`), async route => {
    requests.push(route.request().postData()!);
    // Fetch the canonical URL directly so the interception includes the commit,
    // rather than only Next's trailing-slash redirect.
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(201);
    const body = await response.json();
    if (!paymentId) paymentId = body.id; else expect(body.id).toBe(paymentId);
    if (requests.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.goto("/pos");
  await page.getByRole("button", { name: /Cash recovery E2E ·/ }).click();
  await page.getByLabel("Valor do pagamento").fill("10,00");
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo recebimento" });
  await expect(verify).toBeEnabled();
  const committed = await api(page, `tabs/${tab.id}/`);
  expect(committed.payments).toHaveLength(1); expect(committed.payments[0].id).toBe(paymentId);
  expect(committed.exposure_cents).toBe(1000);
  await page.reload(); await expect(verify).toBeEnabled(); expect(requests).toHaveLength(1);
  await verify.click();
  await expect(page.getByText("Recebimento confirmado. Saldo atualizado.")).toBeVisible();
  expect(requests[1]).toBe(requests[0]);
  const recovered = await api(page, `tabs/${tab.id}/`);
  expect(recovered.payments).toEqual(committed.payments); expect(recovered.exposure_cents).toBe(1000);
  const afterShift = await api(page, `cash/shifts/${shift.id}/`);
  expect(afterShift.expected_cents - beforeShift.expected_cents).toBe(1000);
  expect(afterShift.movements.filter((m: { payment_id: string }) => m.payment_id === paymentId)).toHaveLength(1);
});
