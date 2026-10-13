import { expect, test, type Page } from "@playwright/test";

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

test("Manager resolves 38/10/8 correction with no refund through real Web and PostgreSQL", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  for (const [name, price] of [["Correction target E2E", 800], ["Correction remainder E2E", 3000]] as const)
    await api(page, "catalog/resolve-or-create/", { name, price_cents: price, fulfillment_station: "BAR" });
  const products = (await api(page, "catalog/products/")).results.filter((p: { name: string }) => p.name.startsWith("Correction "));
  const tab = await api(page, "tabs/", { display_label: "Partial payment review E2E" });
  await api(page, "auth/reauthenticate/", { pin: "2468" });
  await api(page, `tabs/${tab.id}/limit-override/`, { limit_cents: 5000, reason: "Isolated correction test",
    expires_at: new Date(Date.now() + 3600000).toISOString(), idempotency_key: "review-e2e-limit" });
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: "review-e2e-order", lines: products.map((p: { id: string }) => ({ product_id: p.id, quantity: 1 })) });
  await api(page, `tabs/${tab.id}/payments/`, { amount_cents: 1000, method: "EXTERNAL_TERMINAL", idempotency_key: "review-e2e-payment" });
  const before = await api(page, `tabs/${tab.id}/`);
  const target = before.orders[0].items.find((item: { product_name: string }) => item.product_name === "Correction target E2E");
  const pending = await api(page, `order-items/${target.id}/corrections/cancel/`, { kind: "CANCEL_ITEM", reason_code: "WRONG_ENTRY", idempotency_key: "review-e2e-cancel" });
  expect(pending.financial_disposition).toBe("MANUAL_REVIEW_REQUIRED");
  expect(pending.exposure_cents).toBe(2800);
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption(tab.id);
  const approve = page.getByRole("button", { name: "Aprovar correção de Correction target E2E sem estorno" });
  await page.getByLabel("PIN do gerente").fill("2468");
  await page.getByRole("button", { name: "Confirmar PIN", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("PIN confirmado");
  await approve.click();
  await expect(page.getByRole("region", { name: "Revisões sem devolução" })).toHaveCount(0);
  const after = await api(page, `tabs/${tab.id}/`);
  expect(after.exposure_cents).toBe(2000); expect(after.payable_cents).toBe(3000);
  expect(after.refunds_cents).toBe(0); expect(after.payments).toEqual(before.payments);
  expect(after.orders[0].items.find((item: { id: string }) => item.id === target.id).state).toBe("CANCELLED");
  const replay = await api(page, `corrections/${pending.id}/settle-without-refund/`, {});
  expect(replay.exposure_cents).toBe(2000); expect(replay.refund_id).toBeNull();
  const remainder = after.orders[0].items.find((item: { id: string }) => item.id !== target.id);
  expect(remainder.state).toBe("NEW");
  await page.goto("/bar");
  await page.getByRole("button", { name: /^Iniciar preparo: 1 Correction remainder E2E/ }).click();
  await page.getByRole("button", { name: /^Pronto: 1 Correction remainder E2E/ }).click();
  await expect.poll(async () => {
    const produced = await api(page, `tabs/${tab.id}/`);
    return produced.orders[0].items.find((item: { id: string }) => item.id === remainder.id).state;
  }).toBe("READY");
});
