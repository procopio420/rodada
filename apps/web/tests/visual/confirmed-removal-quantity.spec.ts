import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const outcome of ["lost", "conflict"] as const) for (const width of [360, 390, 430]) {
  test(`confirmed removal quantity ${outcome} at ${width}`, async ({ page }) => {
    await fixture(page, "normal", true);
    await page.setViewportSize({ width, height: 900 });
    const item = { id: "item-test", product_name: "Item confirmado", quantity: 3, state: "NEW" };
    const tab = () => ({ id: "tab-removal", display_label: "Comanda de teste", table_label: "08", state: "OPEN", version: 1, exposure_cents: item.state === "CANCELLED" ? 0 : item.quantity * 1200, payable_cents: item.state === "CANCELLED" ? 0 : item.quantity * 1200, orders: [{ id: "order-test", items: [item] }], payments: [] });
    await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { table_service_enabled: true, results: [{ id: "table-test", label: "08", status: "OCCUPIED", active_occupancy: { id: "occupancy-test", generation: 1, tabs: [tab()] } }] } }));
    await page.route(/\/api\/attendance\/tabs\/tab-removal\/(\?.*)?$/, route => route.fulfill({ json: tab() }));
    const attempts: string[] = [];
    await page.route("**/api/attendance/order-items/item-test/corrections/cancel/", route => {
      attempts.push(route.request().postData()!);
      if (attempts.length === 1) {
        if (outcome === "lost") { item.state = "CANCELLED"; return route.abort(); }
        item.quantity = 1;
        return route.fulfill({ status: 409, json: { code: "VERSION_CONFLICT", message: "Quantidade mudou. Confira o pedido." } });
      }
      item.state = "CANCELLED";
      return route.fulfill({ json: { status: "APPLIED", order_item_state: "CANCELLED", quantity_cancelled: JSON.parse(attempts.at(-1)!).quantity, remaining_quantity: 0 } });
    });
    await page.goto("/attendance");
    await page.getByRole("button", { name: "Mesas", exact: true }).click();
    await page.getByRole("button", { name: /Mesa 08 Ocupada/ }).click();
    await page.locator('button[data-tab-id="tab-removal"]').click();
    await page.getByRole("button", { name: "Conferir / fechar conta", exact: true }).click();
    await page.getByRole("button", { name: "Remover Item confirmado", exact: true }).click();
    const dialog = page.getByRole("dialog", { name: /^Remover / });
    await dialog.getByRole("button", { name: "Aumentar quantidade a remover" }).click();
    await dialog.getByRole("button", { name: "Aumentar quantidade a remover" }).click();
    await expect(dialog.getByRole("heading")).toHaveText("Remover 3× Item confirmado?");
    await layoutAndA11y(page);
    await dialog.getByRole("button", { name: "Confirmar remoção" }).click();
    if (outcome === "lost") {
      await expect(dialog.getByRole("button", { name: "Verificar mesma remoção" })).toBeEnabled();
      await expect(dialog.getByRole("button", { name: "Diminuir quantidade a remover" })).toBeDisabled();
      await expect(dialog.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
      await page.keyboard.press("Escape");
      await expect(dialog).toBeVisible();
      await dialog.getByRole("button", { name: "Verificar mesma remoção" }).click();
      expect(attempts[1]).toBe(attempts[0]);
    } else {
      await expect(dialog.getByRole("status").filter({ hasText: "Quantidade mudou." })).toContainText("Quantidade mudou.");
      await expect(dialog.getByRole("heading")).toHaveText("Remover 1× Item confirmado?");
      await dialog.getByRole("button", { name: "Confirmar remoção" }).click();
      expect(JSON.parse(attempts[1]).quantity).toBe(1);
      expect(JSON.parse(attempts[1]).idempotency_key).not.toBe(JSON.parse(attempts[0]).idempotency_key);
    }
    await expect(dialog).toHaveCount(0);
    expect(attempts).toHaveLength(2);
    expect(JSON.parse(attempts[0]).quantity).toBe(3);
  });
}
