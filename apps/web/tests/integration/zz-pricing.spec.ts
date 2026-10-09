import { test, expect, type Page } from "@playwright/test";
async function api(page: Page, path: string, data?: unknown, method?: string) {
  const result = await page.evaluate(async ({ path, data, method }) => {
    const r = await fetch(`/api/pos${path}`, { method: method ?? (data ? "POST" : "GET"), headers: { "Content-Type": "application/json" }, body: data ? JSON.stringify(data) : undefined });
    return { status: r.status, body: await r.json() };
  }, { path, data, method });
  expect(result.status, JSON.stringify(result.body)).toBeLessThan(300);
  return result.body;
}
test("cashier bill shows canonical discount service partial payment correction and final reconciliation", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  await page.evaluate(() => fetch("/api/auth/reauthenticate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pin: "2468" }) }));
  const policy = await api(page, "/pricing/policy/"); const { version, ...fields } = policy;
  await api(page, "/pricing/policy/", { ...fields, expected_version: version, service_enabled: true, service_basis_points: 1000, allow_post_payment: true }, "PUT");
  const { results } = await api(page, "/catalog/products/"); const product = results.find((p: { name: string }) => p.name === "Bar E2E item");
  const tab = await api(page, "/tabs/", { display_label: "Pricing reconciliation" });
  await api(page, `/tabs/${tab.id}/orders/confirm/`, { idempotency_key: "pricing-order", lines: [{ product_id: product.id, quantity: 2 }] });
  await page.goto("/pos"); await page.getByRole("button", { name: /Pricing reconciliation/ }).click();
  await page.getByLabel("Valor (R$)").fill("1,00"); await page.getByLabel("Motivo", { exact: true }).fill("CUSTOMER_REQUEST");
  await page.getByRole("button", { name: "Conferir antes de aplicar" }).click(); await page.getByRole("button", { name: "Confirmar ajuste" }).click();
  await expect(page.getByText("Ajuste aplicado.")).toBeVisible();
  const apply = async (kind: string, value: number, key: string) => { const detail = await api(page, `/tabs/${tab.id}/`); return api(page, `/tabs/${tab.id}/pricing/`, { kind, value, expected_version: detail.version, idempotency_key: key, reason_code: "CUSTOMER_REQUEST" }); };
  await apply("SERVICE_CHARGE", 1000, "service");
  await api(page, `/tabs/${tab.id}/payments/`, { amount_cents: 400, method: "OTHER", idempotency_key: "partial" });
  await apply("TAB_DISCOUNT", 100, "correction"); await apply("SERVICE_CHARGE", 1000, "refresh");
  const beforeFinal = await api(page, `/tabs/${tab.id}/`);
  expect([beforeFinal.original_subtotal_cents, beforeFinal.discounts_cents, beforeFinal.service_charge_cents, beforeFinal.payments_cents, beforeFinal.exposure_cents]).toEqual([1000, 200, 80, 400, 480]);
  await api(page, `/tabs/${tab.id}/payments/`, { amount_cents: 480, method: "OTHER", idempotency_key: "final" }); await api(page, `/tabs/${tab.id}/close/`, {});
  const day = (await api(page, "/management/calendar/")).business_date;
  const report = await api(page, `/management/reports/?start=${day}&end=${day}`);
  expect(report.totals.tab_discounts_cents).toBeGreaterThanOrEqual(200);
  expect(report.totals.service_pass_through_cents).toBeGreaterThanOrEqual(80);
  expect((await api(page, `/tabs/${tab.id}/`)).exposure_cents).toBe(0);
});
