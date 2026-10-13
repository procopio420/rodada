import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";
const key = "rodada.intent.availability.v1";
async function setup(page: Page, station = "KITCHEN") {
  await fixture(page, "normal", true);
  const catalog = products.slice(0, 2).map(p => ({ ...p, fulfillment_station: station, availability_version: 1 }));
  await page.route("**/api/pos/catalog/products/", r => r.fulfill({ json: { results: catalog } }));
  const rows = [{ id: "A", product_id: "fries", product_name: "Fritas", state: "NEW", quantity: 1, tab_label: "A", created_at: "2026-10-08T20:00:00Z",
    snapshot_fingerprint: "a".repeat(64), customization_snapshot: { product_id: "fries", product_name: "Fritas", fulfillment_station: station, variant: null, modifiers: [], special_instructions: "" } }];
  await page.route(`**/api/pos/production/${station}/`, r => r.fulfill({ json: { results: rows } }));
  return { catalog, rows };
}
function receipt(id: string, p: any, rejected = false) { return { command_id: `command-${p.idempotency_key}`, product_id: id, ...p, requested_state: p.state,
  state: rejected ? "AVAILABLE" : p.state, version: p.expected_version + 1, status: rejected ? "REJECTED" : "APPLIED", changed: !rejected, conflicts: rejected ? ["VERSION_CONFLICT"] : [] }; }
for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Availability independent recovery ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const { catalog, rows } = await setup(page, station);
  let release!: () => void; const held = new Promise<void>(resolve => { release = resolve; }); const attempts: any[] = [], receipts = new Map();
  await page.route("**/api/pos/catalog/products/*/availability/", async route => {
    const id = route.request().url().split("/").at(-3)!; const p = route.request().postDataJSON(); attempts.push({ id, p });
    expect(await page.evaluate(({ key, p }) => JSON.parse(sessionStorage.getItem(key)!).entries.some((i: any) => JSON.stringify(i.payload) === JSON.stringify(p)), { key, p })).toBe(true);
    if (!receipts.has(p.idempotency_key)) { receipts.set(p.idempotency_key, receipt(id, p)); const product = catalog.find(c => c.id === id)!; product.availability = p.state; product.availability_version++; }
    if (attempts.length === 1) { await held; return route.abort(); } await route.fulfill({ json: receipts.get(p.idempotency_key) });
  });
  await page.route("**/api/pos/production/batches/", async route => { const p = route.request().postDataJSON(); rows[0].state = p.target_state;
    await route.fulfill({ json: { ...p, command_id: "item-command", status: "APPLIED", lines: p.lines.map((l: any) => ({ item_id: l.item_id, status: "APPLIED", state: p.target_state, conflicts: [] })) } }); });
  try {
    await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
    await page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true }).click(); await expect.poll(() => attempts.length).toBe(1);
    await expect(page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true })).toBeDisabled();
    await page.getByRole("button", { name: "Indisponibilizar Omelete", exact: true }).dblclick();
    await expect(page.getByText("Disponibilidade confirmada. · omelette", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, A", exact: true }).click(); await expect(page.getByText("Item confirmado. · A", { exact: true })).toBeVisible();
    release(); const retry = page.getByRole("button", { name: "Verificar mesma disponibilidade: fries", exact: true }); await expect(retry).toBeEnabled();
    await page.reload(); await expect(retry).toBeEnabled(); await expect(page.getByRole("button", { name: "Reativar Fritas", exact: true })).toBeDisabled();
    await layoutAndA11y(page); await page.screenshot({ path: `test-results/availability-${station}-${width}.png` });
    await retry.dblclick(); await expect(page.getByText("Disponibilidade confirmada. · fries", { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(3); expect(attempts[2]).toEqual(attempts[0]); expect(catalog[0].availability_version).toBe(2);
    expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBeNull();
  } finally { release(); }
});
for (const mode of ["rejection", "receipt", "readback", "tampered", "session", "storage", "invalid"]) test(`Availability protection ${mode}`, async ({ page }) => {
  if (mode === "storage") await page.addInitScript(() => { const original = Storage.prototype.setItem; Storage.prototype.setItem = function(k, v) { if (k.startsWith("rodada.intent.availability")) throw new Error("Test storage failure"); return original.call(this, k, v); }; });
  if (mode === "invalid") await page.addInitScript(key => sessionStorage.setItem(key, '{"schema":1,"entries":[{}]}'), key);
  await setup(page); const attempts: any[] = [];
  await page.route("**/api/pos/catalog/products/fries/availability/", async route => {
    const p = route.request().postDataJSON(); attempts.push(p);
    if (["session", "tampered"].includes(mode)) return route.abort();
    if (mode === "readback") await page.route("**/api/pos/catalog/products/", r => r.fulfill({ status: 503, json: {} }));
    const r = receipt("fries", p, mode === "rejection"); if (mode === "receipt") r.product_id = "wrong";
    await route.fulfill({ status: mode === "rejection" ? 409 : 200, json: r });
  });
  await page.goto("/kitchen");
  if (["storage", "invalid"].includes(mode)) { await expect(page.getByText(/Não foi possível preservar a disponibilidade/)).toBeVisible(); await expect(page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true })).toBeDisabled(); expect(attempts).toHaveLength(0); return; }
  await page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true }).click();
  if (mode === "rejection") { await expect(page.getByText(/Disponibilidade não aplicada/)).toBeVisible(); expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBeNull(); return; }
  const retry = page.getByRole("button", { name: "Verificar mesma disponibilidade: fries", exact: true }); await expect(retry).toBeEnabled();
  if (mode === "tampered") await page.evaluate(key => { const b = JSON.parse(sessionStorage.getItem(key)!); b.entries[0].payload.expected_version = 99; sessionStorage.setItem(key, JSON.stringify(b)); }, key);
  const saved = await page.evaluate(key => sessionStorage.getItem(key), key);
  if (mode === "session") await page.route("**/api/auth/me", r => r.fulfill({ json: { venue: { id: "venue-test" }, staff: { id: "operator-test" }, session: { id: "different" } } }));
  await retry.click(); expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBe(saved);
  await expect.poll(() => attempts.length).toBe(["session", "tampered"].includes(mode) ? 1 : 2);
});

for (const mode of ["batch", "item", "other-session", "invalid-item", "no-op"]) test(`Availability scope coexistence ${mode}`, async ({ page }) => {
  await setup(page);
  const production = { schema: 1, venue: "venue-test", staff: "operator-test", session: mode === "other-session" ? "previous-session" : "session-test", captured_at: "2026-10-08T20:00:00Z",
    payload: { station: "KITCHEN", target_state: "PREPARING", idempotency_key: "pending-production", lines: [{ item_id: "A", expected_state: "NEW", quantity: 1, snapshot_fingerprint: "a".repeat(64) }] } };
  if (mode !== "no-op") await page.addInitScript(({ production, mode }) => {
    if (mode === "batch" || mode === "other-session") sessionStorage.setItem("rodada.intent.production-batch.v1", JSON.stringify(production));
    else sessionStorage.setItem("rodada.intent.production-items.v1", JSON.stringify({ schema: 1, entries: mode === "invalid-item" ? [{}] : [production] }));
  }, { production, mode });
  let sends = 0;
  await page.route("**/api/pos/catalog/products/fries/availability/", async route => {
    sends++; const p = route.request().postDataJSON(), r = receipt("fries", p);
    if (mode === "no-op") { r.changed = false; r.version = p.expected_version; }
    await route.fulfill({ json: r });
  });
  await page.goto("/kitchen"); const action = page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true });
  if (mode === "invalid-item") { await expect(action).toBeDisabled(); expect(sends).toBe(0); return; }
  await action.click();
  if (mode === "other-session") { await expect(page.getByText(/Não foi possível preservar esta disponibilidade/)).toBeVisible(); expect(sends).toBe(0); return; }
  await expect(page.getByText("Disponibilidade confirmada. · fries", { exact: true })).toBeVisible(); expect(sends).toBe(1);
  if (["batch", "item"].includes(mode)) {
    expect(await page.evaluate(mode => sessionStorage.getItem(mode === "batch" ? "rodada.intent.production-batch.v1" : "rodada.intent.production-items.v1"), mode)).not.toBeNull();
    await expect(page.getByRole("button", { name: "Iniciar preparo: 1 Fritas, A", exact: true })).toBeDisabled();
  }
});
