import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const outcome of ["lost", "paid", "preparing"] as const) test(`Attendance removal handles ${outcome}`, async ({ page }) => {
 await fixture(page, "normal", true);
 const width = { lost: 360, paid: 390, preparing: 430 }[outcome];
 await page.setViewportSize({ width, height: 900 });
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
 const removalButton = page.getByRole("button", { name: "Remover 1× Item confirmado", exact: true });
 await expect(removalButton).toHaveText("");
 await expect(removalButton.locator("svg")).toHaveAttribute("aria-hidden", "true");
 const removalTarget = await removalButton.boundingBox();
 expect(removalTarget!.width).toBeGreaterThanOrEqual(44);
 expect(removalTarget!.height).toBeGreaterThanOrEqual(44);
 await page.screenshot({ path: `../../visual-artifacts/pilot-cohesion/attendance-sections-${width}.png`, fullPage: true });
 await removalButton.click();
 const form = page.getByRole("dialog", { name: "Remover 1× Item confirmado?" });
 await expect(form).toBeVisible();
 await page.keyboard.press("Escape");
 await expect(form).toHaveCount(0);
 await expect(page.getByRole("button", { name: /^Remover / })).toBeFocused();
 await page.getByRole("button", { name: /^Remover / }).click();
 await layoutAndA11y(page);
 await page.getByLabel("Motivo da remoção").selectOption("CUSTOMER_CHANGED_MIND");
 await form.getByRole("button", { name: "Confirmar remoção" }).click();
 if (outcome === "lost") {
  await expect(form.getByRole("button", { name: "Verificar mesma remoção" })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Mesas", exact: true, includeHidden: true })).toBeDisabled();
  await expect(page.getByLabel("Motivo da remoção")).toBeDisabled();
  await form.getByRole("button", { name: "Verificar mesma remoção" }).click();
  await expect(form).toHaveCount(0);
  expect(attempts).toHaveLength(2); expect(attempts[0]).toBe(attempts[1]);
  await expect(page.getByText("Cancelado", { exact: true })).toHaveCount(0);
  await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 0,00", { exact: true })).toBeVisible();
 } else {
  await expect(form.getByRole("status")).toContainText(outcome === "paid" ? "ele ainda não foi removido" : "exige fluxo");
  await form.getByRole("button", { name: "Voltar" }).click();
  await expect(form).toHaveCount(0);
  await expect(page.getByText("Cancelado", { exact: true })).toHaveCount(0);
  await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 7,50")).toBeVisible();
 }
});

for (const width of [360, 390, 430]) test(`Attendance removes selected units and keeps remaining at ${width}`, async ({ page }) => {
 await fixture(page, "normal", true);
 await page.setViewportSize({ width, height: 900 });
 let remaining = 3;
 const item = { id: "item-partial", product_name: "Item confirmado", quantity: 3, state: "NEW" };
 const applied = new Set<string>();
 const requests: string[] = [];
 const tab = () => ({ id: "tab-test", display_label: "Comanda de teste", state: "OPEN", version: 1, exposure_cents: remaining * 1200, payable_cents: remaining * 1200, original_subtotal_cents: 3600, orders: [{ id: "order-test", items: [item] }] });
 await page.route("**/api/attendance/tabs/", route => route.fulfill({ json: { results: [tab()] } }));
 await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ json: tab() }));
 await page.route("**/api/attendance/order-items/item-partial/corrections/cancel/", route => {
  const raw = route.request().postData()!;
  requests.push(raw);
  const body = JSON.parse(raw);
  if (!applied.has(body.idempotency_key)) { remaining -= body.quantity; applied.add(body.idempotency_key); }
  item.quantity = remaining || 3;
  item.state = remaining ? "NEW" : "CANCELLED";
  if (width === 360 && requests.length === 1) return route.abort();
  return route.fulfill({ json: { status: "APPLIED", order_item_state: item.state, quantity_cancelled: body.quantity, remaining_quantity: remaining } });
 });
 await page.goto("/attendance");
 await page.getByRole("button", { name: "Contas", exact: true }).click();
 await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
 await page.getByRole("button", { name: "Remover 3× Item confirmado", exact: true }).click();
 let dialog = page.getByRole("dialog");
 const count = dialog.getByRole("group", { name: "Quantidade a remover" }).locator("output");
 await expect(count).toHaveText("1");
 await expect(dialog.getByRole("button", { name: "Diminuir quantidade a remover" })).toBeDisabled();
 await dialog.getByRole("button", { name: "Aumentar quantidade a remover" }).click();
 await dialog.getByRole("button", { name: "Aumentar quantidade a remover" }).click();
 await expect(count).toHaveText("3");
 await expect(dialog.getByRole("button", { name: "Aumentar quantidade a remover" })).toBeDisabled();
 await dialog.getByRole("button", { name: "Diminuir quantidade a remover" }).click();
 await dialog.getByRole("button", { name: "Diminuir quantidade a remover" }).click();
 await layoutAndA11y(page);
 if (width === 390) await page.screenshot({ path: "../../visual-artifacts/pilot-cohesion/partial-removal-390.png", fullPage: false });
 await dialog.getByRole("button", { name: "Confirmar remoção" }).click();
 if (width === 360) {
  await expect(dialog.getByRole("button", { name: "Aumentar quantidade a remover" })).toBeDisabled();
  await expect(dialog.getByRole("button", { name: "Diminuir quantidade a remover" })).toBeDisabled();
  await dialog.getByRole("button", { name: "Verificar mesma remoção" }).click();
  expect(requests[0]).toBe(requests[1]);
 }
 await expect(page.getByRole("dialog")).toHaveCount(0);
 await expect(page.getByText("2× Item confirmado", { exact: true })).toBeVisible();
 expect(remaining).toBe(2);
 await page.getByRole("button", { name: "Remover 2× Item confirmado", exact: true }).click();
 dialog = page.getByRole("dialog");
 await dialog.getByRole("button", { name: "Aumentar quantidade a remover" }).click();
 await dialog.getByRole("button", { name: "Confirmar remoção" }).click();
 await expect(page.getByRole("dialog")).toHaveCount(0);
 await expect(page.getByText("Item confirmado", { exact: false })).toHaveCount(0);
 expect(remaining).toBe(0);
 const order = await page.locator(".attendanceSelectedTab").evaluate(element => {
  const summary = element.querySelector('[aria-label="Valores da comanda"]')!;
  const close = element.querySelector(".attendanceCloseTab")!;
  return summary.nextElementSibling === close && !close.nextElementSibling;
 });
 expect(order).toBe(true);
});
for (const width of [360, 390, 430]) test(`Wrong-entry removal is absent from bill details at ${width}`, async ({ page }) => {
 await fixture(page, "normal", true);
 await page.setViewportSize({ width, height: 900 });
 const tab = { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", version: 1, exposure_cents: 2400, payable_cents: 2400, original_subtotal_cents: 3600, corrections_cents: -1200, wrong_entry_removals_cents: -1200, orders: [] };
 await page.route("**/api/attendance/tabs/", route => route.fulfill({ json: { results: [tab] } }));
 await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ json: tab }));
 await page.goto("/attendance");
 await page.getByRole("button", { name: "Contas", exact: true }).click();
 await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
 const bill = page.getByRole("region", { name: "Valores da comanda" });
 await bill.getByText("Mais detalhes", { exact: true }).click();
 await expect(bill.getByText("Correções", { exact: true })).toHaveCount(0);
 await expect(bill.getByText("Itens retirados por engano", { exact: true })).toHaveCount(0);
 await expect(bill.getByText("R$ 24,00", { exact: true }).first()).toBeVisible();
 await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ json: { ...tab, corrections_cents: -1400, payable_cents: 2200, exposure_cents: 2200 } }));
 await page.reload();
 await page.getByRole("button", { name: "Contas", exact: true }).click();
 await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
 await bill.getByText("Mais detalhes", { exact: true }).click();
 await expect(bill.locator(".dataRow").filter({ has: page.getByText("Correções", { exact: true }) }).getByText("-R$ 2,00", { exact: true })).toBeVisible();
 await layoutAndA11y(page);
});
