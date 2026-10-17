import { expect, test } from "./fixtures";
import { openNamedAttendanceTab, selectExistingAttendanceTab } from "./attendance-helpers";
import { addCatalogItem } from "../visual/category-actions";

for (const width of [360, 390, 430, 1280]) test(`real order reference and historical station survive reload ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  const name = `Canonical order status ${width}`;
  await openNamedAttendanceTab(page, name);
  await addCatalogItem(page, "Kitchen E2E item");
  await addCatalogItem(page, "Bar E2E item");
  const popup = page.locator(".ux2Workspace");
  await popup.getByRole("button", { name: /^Enviar / }).click();
  await expect(popup.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  const status = page.getByRole("region", { name: "Último pedido confirmado" });
  await expect(status).toContainText("Cozinha · Na fila");
  await expect(status).toContainText("Bar · Na fila");
  const confirmed = await page.evaluate(async label => {
    const list = await (await fetch(`/api/attendance/tabs/?q=${encodeURIComponent(label)}`)).json();
    const tab = list.results.find((value: { display_label: string }) => value.display_label === label);
    return (await fetch(`/api/attendance/tabs/${tab.id}/`)).json();
  }, name);
  expect(confirmed.orders).toHaveLength(1);
  expect(confirmed.orders[0].items).toHaveLength(2);
  expect(confirmed.exposure_cents).toBe(1500);
  expect(confirmed.payments).toHaveLength(0);
  await expect(status).toContainText(`#${confirmed.orders[0].id}`);
  await page.screenshot({ path: `test-results/integration/033-order-${width}.png`, fullPage: true });
  await page.reload(); await selectExistingAttendanceTab(page, name);
  await expect(status).toContainText(`#${confirmed.orders[0].id}`);
  // Canonical production transition, no mocked transport or inferred READY.
  const item = confirmed.orders[0].items.find((value: { fulfillment_station_snapshot: string }) => value.fulfillment_station_snapshot === "BAR");
  const result = await page.evaluate(async id => {
    for (const state of ["PREPARING", "READY"]) {
      const response = await fetch(`/api/pos/order-items/${id}/transition/`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ state }),
      });
      if (!response.ok) return response.status;
    }
    return 200;
  }, item.id);
  expect(result).toBe(200);
  await expect(status).toContainText("Bar · Pronto", { timeout: 25000 });
  await expect(status).toContainText("Cozinha · Na fila");
});
