import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
test("Batch review 51 lines keeps explicit selection capped at 50", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 }); await fixture(page, "normal", true);
  const snapshot = { product_id: "fries", product_name: "Fritas", fulfillment_station: "KITCHEN", variant: null, modifiers: [], special_instructions: "" };
  const rows = Array.from({ length: 51 }, (_, index) => ({ id: `line-${index}`, product_id: "fries", product_name: "Fritas", state: "NEW", quantity: 1,
    customization_snapshot: snapshot, snapshot_fingerprint: "a".repeat(64), tab_label: `Destino ${index}`, created_at: "2026-10-08T20:00:00Z" }));
  await page.route("**/api/pos/production/KITCHEN/", route => route.fulfill({ json: { results: rows } }));
  let commands = 0; await page.route("**/api/pos/production/batches/", route => { commands++; return route.abort(); });
  await page.goto("/kitchen"); await page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true }).click();
  const dialog = page.getByRole("dialog"), boxes = dialog.getByRole("checkbox");
  await expect(boxes).toHaveCount(51); await expect(dialog.getByRole("button", { name: "Iniciar preparo selecionado", exact: true })).toBeDisabled();
  for (let index = 0; index < 50; index++) await boxes.nth(index).check();
  await expect(boxes.nth(50)).toBeDisabled(); await expect(dialog).toContainText("50 linhas · 50 unidades selecionadas");
  await boxes.nth(0).uncheck(); await expect(boxes.nth(50)).toBeEnabled(); await boxes.nth(50).check();
  await layoutAndA11y(page); expect(commands).toBe(0);
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click(); await page.clock.runFor(50);
  await expect(page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true })).toBeFocused();
  expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.production-batch.v1"))).toBeNull();
});
