import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";

for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Production confirmed configuration grouping ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await fixture(page, "normal", true);
  const snapshot = { product_id: "fries", product_name: "Fritas", fulfillment_station: station, variant: null, modifiers: [], special_instructions: "", quantity: 1, unit_price_cents: 7200 };
  const row = (id: string, quantity: number, customization_snapshot: unknown) => ({ id, product_id: "fries", product_name: "Fritas", state: "NEW", quantity, customization_snapshot, tab_label: id, created_at: "2026-10-08T20:00:00Z" });
  const rows = [row("A", 1, snapshot), row("B", 2, { ...snapshot, unit_price_cents: 8000, quantity: 2 }),
    row("C", 2, { ...snapshot, variant: { id: "large", name: "Grande" } }),
    row("D", 1, { ...snapshot, special_instructions: "Sem sal" }),
    row("E", 1, { ...snapshot, modifiers: [{ group_id: "extra", group_name: "Adicionais", option_id: "cheese", name: "Queijo", semantic_kind: "ADD" }] }),
    row("F", 1, {}), row("G", 1, undefined)];
  const before = JSON.stringify(rows);
  const catalog = [{ ...products[0], fulfillment_station: station }];
  let changes = 0;
  await page.route(`**/api/pos/production/${station}/`, route => route.fulfill({ json: { results: rows } }));
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: catalog } }));
  await page.route("**/api/pos/catalog/products/fries/availability/", route => { changes++; catalog[0].availability = "UNAVAILABLE"; return route.fulfill({ json: { state: "UNAVAILABLE" } }); });
  await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
  const summary = page.locator(".stationBatches"); const groups = summary.locator(".stationDish");
  await expect(groups).toHaveCount(6); await expect(summary.locator(".stationQuantity")).toHaveText(["3", "2", "1", "1", "1", "1"]);
  await expect(groups.nth(1)).toContainText("Variação: Grande"); await expect(groups.nth(2)).toContainText("Observação: Sem sal"); await expect(groups.nth(3)).toContainText("+ Queijo");
  await expect(summary.getByText(/Configuração não registrada/)).toHaveCount(2);
  await expect(page.getByRole("button", { name: /^Iniciar preparo:/ })).toHaveCount(7);
  await layoutAndA11y(page); await page.screenshot({ path: `test-results/production-configuration-${station}-${width}.png` });
  await page.getByRole("navigation", { name: "Regiões da produção" }).getByRole("button", { name: /^Disponibilidade/ }).click();
  await page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true }).click(); await expect(page.getByRole("button", { name: "Reativar Fritas", exact: true })).toBeEnabled();
  await expect(groups).toHaveCount(6); await expect(groups.nth(1)).toContainText("Variação: Grande");
  expect(changes).toBe(1); expect(JSON.stringify(rows)).toBe(before);
});
