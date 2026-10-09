import { test, expect } from "@playwright/test";
import { fixture, stable, layoutAndA11y } from "./fixtures";
test("pricing command waits for canonical pricing to finish loading", async ({ page }) => {
  await fixture(page);
  await page.route("**/api/pos/tabs/", r => r.fulfill({ json: { results: [{ id: "slow-tab", version: 1, display_label: "Slow pricing", state: "OPEN", exposure_cents: 1000 }] } }));
  await page.route("**/api/pos/tabs/slow-tab/", r => r.fulfill({ json: { id: "slow-tab", version: 1, display_label: "Slow pricing", state: "OPEN", exposure_cents: 1000, charges_cents: 1000, payments_cents: 0, orders: [], payments: [], refund_required_corrections: [] } }));
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/pos/tabs/slow-tab/pricing/", async r => {
    await gate;
    await r.fulfill({ json: { version: 1, policy: { service_basis_points: 1000 }, history: [], charges: [] } });
  });
  await page.goto("/pos");
  await page.getByRole("button", { name: /Slow pricing/ }).click();
  await expect(page.getByRole("button", { name: "Conferir antes de aplicar" })).toBeDisabled();
  release();
  await expect(page.getByRole("button", { name: "Conferir antes de aplicar" })).toBeEnabled();
});
for (const width of [360, 390, 768]) {
  test(`commercial bill and preview accessible at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    const bill = { id: "tab-test", version: 1, display_label: "Conta ajustada", state: "OPEN", original_subtotal_cents: 10000, charges_cents: 10000, discounts_cents: 2000, courtesy_cents: 1000, service_charge_cents: 700, payable_cents: 7700, payments_cents: 3000, refunds_cents: 0, exposure_cents: 4700 };
    await page.route("**/api/pos/tabs/", r => r.fulfill({ json: { results: [bill] } }));
    await page.route("**/api/pos/tabs/tab-test/pricing/", r => r.fulfill({ json: { version: 1, policy: { service_basis_points: 1000 }, history: [], charges: [{ charge_id: "item", gross: 10000 }] } }));
    await page.route("**/api/pos/tabs/tab-test/pricing/preview/", r => r.fulfill({ json: { before_payable_cents: 7700, after_payable_cents: 7600, after_remaining_cents: 4600, approval_required: true } }));
    await page.goto("/pos");
    await page.getByRole("button", { name: /Conta ajustada/ }).click();
    await expect(page.getByText("Subtotal original", { exact: true })).toBeVisible();
    await expect(page.getByText("Cortesias", { exact: true })).toBeVisible();
    await page.getByLabel("Valor (R$)").fill("1,00");
    await page.getByLabel("Motivo", { exact: true }).fill("Pedido do cliente");
    await page.getByRole("button", { name: "Conferir antes de aplicar" }).click();
    await expect(page.getByRole("button", { name: "Solicitar aprovação" })).toBeVisible();
    await stable(page); await layoutAndA11y(page);
    await page.screenshot({ path: `test-results/pricing-${width}.png`, fullPage: true });
  });
}
for (const width of [360, 390, 768]) {
  test(`pricing policy and manager approval readable at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 }); await fixture(page);
    await page.route("**/api/pos/pricing/policy/", r => r.fulfill({ json: { version: 1, service_enabled: true, service_basis_points: 750, service_max_basis_points: 10000, service_opt_out: true, service_removal_requires_manager: true, service_treatment: "PASS_THROUGH", service_refundable: true, staff_discount_basis_points: 0, cashier_discount_basis_points: 1000, maximum_discount_basis_points: 10000, allow_post_payment: true } }));
    await page.route("**/api/pos/pricing/approvals/", r => r.fulfill({ json: { results: [{ id: "request", label: "Mesa 24", requester: "Atendimento", command: { kind: "TAB_DISCOUNT", reason_code: "Pedido do cliente" }, preview: { before_payable_cents: 11000, after_payable_cents: 9900 } }] } }));
    await page.goto("/manage/pricing");
    await expect(page.getByLabel("Serviço padrão (%)")).toHaveValue("7.5");
    await expect(page.getByRole("button", { name: "Aprovar com PIN" })).toBeDisabled();
    await stable(page); await layoutAndA11y(page);
    await page.screenshot({ path: `test-results/pricing-management-${width}.png`, fullPage: true });
  });
}
