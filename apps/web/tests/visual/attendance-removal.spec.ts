import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const outcome of ["lost", "paid", "preparing"] as const) test(`Attendance removal handles ${outcome}`, async ({ page }) => {
 await fixture(page, "normal", true);
 const item = { id: "item-cancel", product_name: "Item confirmado", quantity: 1, state: "NEW" };
 let payable = 750, attempts: string[] = [];
 await page.route("**/api/attendance/tabs/", route => route.fulfill({ json: { results: [{ id: "tab-test", display_label: "Comanda de teste", state: "OPEN", version: 1, exposure_cents: payable, payable_cents: payable, original_subtotal_cents: 1000, discounts_cents: 250, orders: [{ id: "order-test", items: [item] }] }] } }));
 await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ json: { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", version: 1, exposure_cents: payable, payable_cents: payable, original_subtotal_cents: 1000, discounts_cents: 250, orders: [{ id: "order-test", items: [item] }] } }));
 await page.route("**/api/attendance/order-items/item-cancel/corrections/cancel/", async route => {
  attempts.push(route.request().postData() || "");
  if (outcome === "paid") return route.fulfill({ status: 202, json: { status: "REQUESTED", financial_disposition: "REFUND_REQUIRED", order_item_state: "NEW" } });
  if (outcome === "preparing") { item.state = "PREPARING"; return route.fulfill({ status: 409, json: { code: "CORRECTION_STAGE_REQUIRES_APPROVAL", message: "Este estágio exige fluxo de correção autorizado." } }); }
  item.state = "CANCELLED"; payable = 0;
  if (attempts.length === 1) return route.abort();
  return route.fulfill({ json: { status: "APPLIED", financial_disposition: "REVERSED", order_item_state: "CANCELLED" } });
 });
 await page.goto("/attendance");
 await page.getByRole("button", { name: "Contas", exact: true }).click();
 await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
 const bill = page.getByRole("region", { name: "Valores da comanda" });
 await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 7,50")).toBeVisible();
 await page.getByRole("button", { name: "Remover", exact: true }).click();
 const form = page.getByRole("region", { name: "Remover item confirmado" });
 await layoutAndA11y(page);
 await page.getByLabel("Motivo da remoção").selectOption("CUSTOMER_CHANGED_MIND");
 await form.getByRole("button", { name: "Confirmar remoção" }).click();
 if (outcome === "lost") {
  await expect(form.getByRole("button", { name: "Verificar mesma remoção" })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Mesas", exact: true })).toBeDisabled();
  await expect(page.getByLabel("Motivo da remoção")).toBeDisabled();
  await form.getByRole("button", { name: "Verificar mesma remoção" }).click();
  await expect(form).toHaveCount(0);
  expect(attempts).toHaveLength(2); expect(attempts[0]).toBe(attempts[1]);
  await expect(page.getByText("Cancelado", { exact: true })).toBeVisible();
  await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 0,00", { exact: true })).toBeVisible();
 } else {
  await expect(form.getByRole("status")).toContainText(outcome === "paid" ? "ele ainda não foi removido" : "exige fluxo");
  await expect(page.getByText("Cancelado", { exact: true })).toHaveCount(0);
  await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 7,50")).toBeVisible();
 }
});
