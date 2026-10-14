import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";
const key = "rodada.intent.production-items.v1";
async function setup(page: Page, station = "KITCHEN") {
  await fixture(page, "normal", true);
  const snapshot = { product_id: "fries", product_name: "Fritas", fulfillment_station: station, variant: null, modifiers: [], special_instructions: "" };
  const rows = ["A", "B", "legacy"].map((id, index) => ({ id, product_id: "fries", product_name: "Fritas", state: index === 0 ? "PREPARING" : "NEW", quantity: 1,
    customization_snapshot: index === 2 ? {} : { ...snapshot, special_instructions: id }, snapshot_fingerprint: index === 2 ? undefined : "a".repeat(64), tab_label: id, created_at: "2026-10-08T20:00:00Z" }));
  await page.route(`**/api/pos/production/${station}/`, route => route.fulfill({ json: { results: rows } }));
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: [{ ...products[0], fulfillment_station: station }] } }));
  return rows;
}
function receipt(payload: any, rejected = false) { return { ...payload, command_id: `command-${payload.idempotency_key}`, status: rejected ? "REJECTED" : "APPLIED",
  lines: payload.lines.map((line: any) => ({ item_id: line.item_id, status: rejected ? "NOT_APPLIED" : "APPLIED", state: payload.target_state, conflicts: rejected ? ["STATE_CONFLICT"] : [] })) }; }
for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Independent item recovery ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const rows = await setup(page, station);
  let release!: () => void; const held = new Promise<void>(resolve => { release = resolve; });
  const attempts: any[] = [], receipts = new Map<string, unknown>();
  await page.route("**/api/pos/production/batches/", async route => {
    const p = route.request().postDataJSON(); attempts.push(p);
    const stored = await page.evaluate(key => JSON.parse(sessionStorage.getItem(key)!).entries, key);
    expect(stored.some((i: any) => JSON.stringify(i.payload) === JSON.stringify(p))).toBe(true);
    if (!receipts.has(p.idempotency_key)) { receipts.set(p.idempotency_key, receipt(p)); rows.find(row => row.id === p.lines[0].item_id)!.state = p.target_state; }
    if (attempts.length === 1) { await held; return route.abort(); }
    await route.fulfill({ json: receipts.get(p.idempotency_key) });
  });
  await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
  await page.getByRole("button", { name: "Pronto: 1 Fritas, A", exact: true }).click(); await expect.poll(() => attempts.length).toBe(1);
  await expect(page.getByRole("button", { name: "Pronto: 1 Fritas, A", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, B", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, legacy", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, B", exact: true }).dblclick();
  await expect.poll(() => attempts.length).toBe(2); await expect(page.getByText("Item confirmado. · B", { exact: true })).toBeVisible();
  expect(attempts[0].lines[0].item_id).toBe("A"); expect(attempts[1].lines[0].item_id).toBe("B");
  release(); await expect(page.getByRole("button", { name: "Verificar mesmo item: A", exact: true })).toBeEnabled();
  await page.reload(); await expect(page.getByRole("button", { name: "Verificar mesmo item: A", exact: true })).toBeEnabled();
  expect(await page.evaluate(key => JSON.parse(sessionStorage.getItem(key)!).entries.length, key)).toBe(1);
  await layoutAndA11y(page); await page.screenshot({ path: `test-results/production-independent-${station}-${width}.png` });
  await page.getByRole("button", { name: "Verificar mesmo item: A", exact: true }).dblclick();
  await expect(page.getByText("Item confirmado. · A", { exact: true })).toBeVisible(); expect(attempts).toHaveLength(3); expect(attempts[2]).toEqual(attempts[0]);
  expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBeNull();
  await expect(page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, legacy", exact: true })).toBeEnabled();
});
for (const mode of ["rejection", "snapshot", "readback", "tampered", "session", "storage"]) test(`Independent item protection ${mode}`, async ({ page }) => {
  if (mode === "storage") await page.addInitScript(() => { const original = Storage.prototype.setItem; Storage.prototype.setItem = function(key, value) { if (key.startsWith("rodada.intent.production-items")) throw new Error("Test storage failure"); return original.call(this, key, value); }; });
  const rows = await setup(page); const attempts: any[] = [];
  await page.route("**/api/pos/production/batches/", async route => {
    const p = route.request().postDataJSON(); attempts.push(p);
    if (["session", "tampered"].includes(mode) && attempts.length === 1) return route.abort();
    if (mode === "readback") await page.route("**/api/pos/production/KITCHEN/", r => r.fulfill({ status: 503, json: {} }));
    await route.fulfill({ status: ["rejection", "snapshot"].includes(mode) ? 409 : 200, json: receipt(p, ["rejection", "snapshot"].includes(mode)) });
  });
  await page.goto("/kitchen");
  if (mode === "storage") { await expect(page.getByText(/Não foi possível preservar as ações/)).toBeVisible(); await expect(page.getByRole("button", { name: "Pronto: 1 Fritas, A", exact: true })).toBeDisabled(); expect(attempts).toHaveLength(0); return; }
  await page.getByRole("button", { name: "Pronto: 1 Fritas, A", exact: true }).click();
  if (["rejection", "snapshot"].includes(mode)) {
    await expect(page.getByText(/Item não aplicado/)).toBeVisible(); await expect(page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, B", exact: true })).toBeEnabled();
    expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBeNull(); expect(rows[0].state).toBe("PREPARING"); return;
  }
  await expect(page.getByRole("button", { name: "Verificar mesmo item: A", exact: true })).toBeEnabled();
  let saved = await page.evaluate(key => sessionStorage.getItem(key), key);
  if (mode === "tampered") { await page.evaluate(key => { const bag = JSON.parse(sessionStorage.getItem(key)!); bag.entries[0].payload.lines[0].quantity = 99; sessionStorage.setItem(key, JSON.stringify(bag)); }, key); saved = await page.evaluate(key => sessionStorage.getItem(key), key); }
  if (mode === "session") await page.route("**/api/auth/me", route => route.fulfill({ json: { venue: { id: "venue-test" }, staff: { id: "operator-test" }, session: { id: "new-session" } } }));
  await page.getByRole("button", { name: "Verificar mesmo item: A", exact: true }).click();
  await expect(page.getByText(mode === "session" ? /pertencem à sessão original/ : /Resultado ainda não confirmado/)).toBeVisible();
  expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBe(saved);
  await expect.poll(() => attempts.length).toBe(mode === "readback" ? 2 : 1);
});
