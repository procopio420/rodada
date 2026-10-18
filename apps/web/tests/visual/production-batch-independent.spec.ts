import type { Intent, BatchLine } from "@/lib/client/production-batch-intent";
import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";
import { expectBarAvailabilityBlocked } from "./station-availability-actions";
for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Independent item beside batch ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await fixture(page, "normal", true);
  const snapshot = { product_id: "fries", product_name: "Fritas", fulfillment_station: station, variant: null, modifiers: [], special_instructions: "" };
  const rows = ["A", "B", "C", "legacy"].map(id => ({ id, product_id: "fries", product_name: "Fritas", state: "NEW", quantity: 1, customization_snapshot: id === "legacy" ? {} : snapshot,
    snapshot_fingerprint: id === "legacy" ? undefined : "a".repeat(64), tab_label: id, created_at: "2026-10-08T20:00:00Z" }));
  await page.route(`**/api/pos/production/${station}/`, route => route.fulfill({ json: { results: rows } }));
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: [{ ...products[0], fulfillment_station: station }] } }));
  const attempts: Intent["payload"][] = [], receipts = new Map<string, unknown>();
  await page.route("**/api/pos/production/batches/", async route => {
    const p = route.request().postDataJSON(); attempts.push(p);
    if (!receipts.has(p.idempotency_key)) {
      p.lines.forEach((line: BatchLine) => { rows.find(row => row.id === line.item_id)!.state = p.target_state; });
      receipts.set(p.idempotency_key, { ...p, command_id: p.idempotency_key, status: "APPLIED", lines: p.lines.map((line: BatchLine) => ({ item_id: line.item_id, status: "APPLIED", state: p.target_state, conflicts: [] })) });
    }
    if (attempts.length <= 2) return route.abort();
    await route.fulfill({ json: receipts.get(p.idempotency_key) });
  });
  await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
  await page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true }).click();
  const dialog = page.getByRole("dialog"); await dialog.getByRole("checkbox").nth(0).check(); await dialog.getByRole("checkbox").nth(1).check();
  await dialog.getByRole("button", { name: "Iniciar preparo selecionado", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo lote", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, A", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, legacy", exact: true })).toBeDisabled();
  if (station === "BAR") await expectBarAvailabilityBlocked(page, "Fritas");
  else await expect(page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, C", exact: true }).dblclick();
  await expect(page.getByRole("button", { name: "Verificar mesmo item: C", exact: true })).toBeEnabled();
  expect(attempts).toHaveLength(2); await page.reload(); await layoutAndA11y(page);
  await page.screenshot({ path: `test-results/production-batch-independent-${station}-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: "Verificar mesmo item: C", exact: true }).click();
  await expect(page.getByText("Item confirmado. · C", { exact: true })).toBeVisible(); expect(attempts[2]).toEqual(attempts[1]);
  await expect(page.getByRole("button", { name: "Pronto: 1 Fritas, A", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Verificar mesmo lote", exact: true }).click();
  await expect(page.getByText("Lote confirmado.", { exact: true })).toBeVisible(); expect(attempts[3]).toEqual(attempts[0]);
  await expect(page.getByRole("button", { name: "Pronto: 1 Fritas, A", exact: true })).toBeEnabled();
});
for (const mode of ["session", "malformed", "tampered"]) test(`Independent batch barrier ${mode}`, async ({ page }) => {
  await fixture(page, "normal", true);
  const batch = { schema: 1, venue: "venue-test", staff: "operator-test", session: mode === "session" ? "original-session" : "session-test", captured_at: "2026-10-08T20:00:00Z", payload: { station: "KITCHEN", target_state: "PREPARING", idempotency_key: "batch-test", lines: [{ item_id: "A", expected_state: "NEW", quantity: 1, snapshot_fingerprint: "a".repeat(64) }] } };
  await page.addInitScript(({ batch, mode }) => sessionStorage.setItem("rodada.intent.production-batch.v1", mode === "malformed" ? "{}" : JSON.stringify(batch)), { batch, mode });
  await page.route("**/api/pos/production/KITCHEN/", route => route.fulfill({ json: { results: [{ id: "C", product_name: "Fritas", tab_label: "C", state: "NEW", quantity: 1, snapshot_fingerprint: "a".repeat(64), customization_snapshot: { product_id: "fries", product_name: "Fritas", fulfillment_station: "KITCHEN", variant: null, modifiers: [], special_instructions: "" }, product_id: "fries" }] } }));
  let sends = 0; await page.route("**/api/pos/production/batches/", route => { sends++; return route.abort(); });
  await page.goto("/kitchen"); const button = page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, C", exact: true });
  if (mode === "session") { await button.click(); await expect(page.getByText(/O lote pendente pertence à sessão original/)).toBeVisible(); }
  else {
    if (mode === "tampered") { await page.evaluate(() => sessionStorage.setItem("rodada.intent.production-batch.v1", "{}")); await page.clock.runFor(16000); }
    await expect(button).toBeDisabled();
  }
  expect(sends).toBe(0);
});
