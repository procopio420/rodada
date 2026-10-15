import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const width of [360, 390, 430]) test(`compact tables expand on touch at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "operator-test", display_name: "Operador" }, venue: { id: "venue-test", name: "Bar" }, session: { id: "session-test" }, capabilities: ["tab.move", "table.manage", "tab.open"] } }));
  await page.route("**/api/attendance/tabs/tab-test/?*", route => route.fulfill({ json: { id: "tab-test", version: 1 } }));
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { table_service_enabled: true, results: [
    { id: "table-test", label: "01", status: "OCCUPIED", active_occupancy: { id: "visit", generation: 1, tabs: [{ id: "tab-test", display_label: "Comanda de teste", state: "OPEN", display_reference: "Comanda 001" }] } },
    { id: "free", label: "02", status: "AVAILABLE" },
    { id: "other", label: "03", status: "OCCUPIED", active_occupancy: { id: "other-visit", generation: 1, tabs: [] } },
  ] } }));
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  const table = page.getByRole("button", { name: /Mesa 01 Ocupada/ });
  await expect(table).toHaveAttribute("aria-expanded", "false");
  await expect(page.getByText("Pessoas na ocupação")).toHaveCount(0);
  await table.click();
  await expect(table).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByRole("button", { name: "Comanda de teste · Comanda 001", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await page.getByRole("button", { name: "Mover comanda", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Mover comanda", exact: true })).toBeVisible();
  await page.getByLabel("Mesa de destino").selectOption("other-visit");
  await expect(page.getByText("Confirmar: mesa 01 → mesa 03.", { exact: true })).toBeVisible();
  await page.getByLabel("Mesa de destino").selectOption("free");
  await expect(page.getByText("Confirmar: mesa 01 → mesa 02.", { exact: true })).toBeVisible();
  await page.screenshot({ path: `test-results/tables-mobile-${width}.png`, fullPage: true });
});
