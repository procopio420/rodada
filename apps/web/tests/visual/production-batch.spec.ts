import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";
const key = "rodada.intent.production-batch.v1";
async function setup(page: Page, station = "KITCHEN") {
  await fixture(page, "normal", true);
  const snapshot = { product_id: "fries", product_name: "Fritas", fulfillment_station: station, variant: null, modifiers: [], special_instructions: "Sem sal" };
  const rows = ["A", "B"].map((id, index) => ({ id, product_id: "fries", product_name: "Fritas", state: index ? "ACCEPTED" : "NEW", quantity: index ? 1 : 2,
    customization_snapshot: snapshot, snapshot_fingerprint: "a".repeat(64), tab_label: `Destino ${id}`, created_at: "2026-10-08T20:00:00Z" }));
  await page.route(`**/api/pos/production/${station}/`, route => route.fulfill({ json: { results: rows } }));
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: [{ ...products[0], fulfillment_station: station }] } }));
  return rows;
}
for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) test(`Batch review replay ${station} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const rows = await setup(page, station);
  const requests: any[] = []; const receipts = new Map<string, unknown>(); let effects = 0;
  await page.route("**/api/pos/production/batches/", async route => {
    const payload = route.request().postDataJSON(); requests.push(payload);
    const stored = await page.evaluate(key => JSON.parse(sessionStorage.getItem(key)!), key);
    expect(stored.payload).toEqual(payload); expect(Object.keys(stored).sort()).toEqual(["captured_at", "payload", "schema", "session", "staff", "venue"]);
    if (!receipts.has(payload.idempotency_key)) {
      effects++; payload.lines.forEach((line: any) => { rows.find(row => row.id === line.item_id)!.state = payload.target_state; });
      receipts.set(payload.idempotency_key, { command_id: `command-${effects}`, ...payload, status: "APPLIED", lines: payload.lines.map((line: any) => ({ item_id: line.item_id, status: "APPLIED", state: payload.target_state, conflicts: [] })) });
      if (effects === 1) return route.abort();
    }
    await route.fulfill({ json: receipts.get(payload.idempotency_key) });
  });
  await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
  await page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("checkbox").first()).not.toBeChecked();
  await expect(dialog.getByRole("button", { name: "Iniciar preparo selecionado", exact: true })).toBeDisabled();
  expect(requests).toHaveLength(0);
  await dialog.getByRole("checkbox").first().check(); await dialog.getByRole("checkbox").last().check();
  await expect(dialog).toContainText("2 linhas · 3 unidades selecionadas"); await expect(dialog).toContainText("Observação: Sem sal");
  await layoutAndA11y(page); await page.screenshot({ path: `test-results/production-batch-review-${station}-${width}.png` });
  await dialog.getByRole("button", { name: "Iniciar preparo selecionado", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo lote", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true })).toBeDisabled();
  await page.reload(); await page.getByRole("button", { name: "Verificar mesmo lote", exact: true }).click();
  await expect(page.getByText("Lote confirmado.", { exact: true })).toBeVisible(); expect(requests[1]).toEqual(requests[0]); expect(effects).toBe(1);
  expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBeNull();
  await page.getByRole("button", { name: "Selecionar prontos: Fritas", exact: true }).click();
  await dialog.getByRole("checkbox").first().check(); await dialog.getByRole("checkbox").last().check();
  await dialog.getByRole("button", { name: "Marcar selecionados como prontos", exact: true }).click();
  await expect(page.getByRole("button", { name: "Selecionar prontos: Fritas", exact: true })).toHaveCount(0);
  await expect(page.getByText("Lote confirmado.", { exact: true })).toBeVisible(); expect(effects).toBe(2); expect(requests[2].idempotency_key).not.toBe(requests[0].idempotency_key);
  await expect(page.locator(".stationPassRow")).toHaveCount(2); await layoutAndA11y(page);
});

test("Batch stale review requires new selection", async ({ page }) => {
  const rows = await setup(page); await page.goto("/kitchen");
  await page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true }).click();
  const dialog = page.getByRole("dialog"); await dialog.getByRole("checkbox").first().check();
  rows[0].quantity = 1; await page.clock.runFor(16000);
  await expect(dialog.getByText("A fila mudou. Volte e selecione novamente.")).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Iniciar preparo selecionado", exact: true })).toBeDisabled();
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click(); await page.clock.runFor(50);
  await expect(page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true })).toBeFocused();
});

test("Batch storage unavailable prevents sending", async ({ page }) => {
  await page.addInitScript(() => { const original = Storage.prototype.setItem; Storage.prototype.setItem = function(key, value) { if (key.startsWith("rodada.intent.production")) throw new Error("Test storage failure"); return original.call(this, key, value); }; });
  await setup(page); let requests = 0; await page.route("**/api/pos/production/batches/", route => { requests++; return route.abort(); });
  await page.goto("/kitchen"); await expect(page.getByText(/Não foi possível preservar o lote/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true })).toBeDisabled(); expect(requests).toBe(0);
});

for (const mode of ["session", "revoked", "tampered", "server", "receipt", "readback", "rejection", "other-station", "malformed"]) test(`Batch protection ${mode}`, async ({ page }) => {
  const rows = await setup(page); let calls = 0;
  if (mode === "malformed") await page.addInitScript(key => sessionStorage.setItem(key, '{"schema":1}'), key);
  await page.route("**/api/pos/production/batches/", async route => {
    calls++; const p = route.request().postDataJSON();
    if (mode === "server") return route.fulfill({ status: 503, json: { code: "TEMPORARY", message: "Test temporary failure" } });
    if (calls === 1 && mode !== "rejection") return route.abort();
    if (mode === "readback") await page.route("**/api/pos/production/KITCHEN/", r => r.fulfill({ status: 503, json: {} }));
    await route.fulfill({ status: mode === "rejection" ? 409 : 200, json: { command_id: "test-command", ...p, status: mode === "rejection" ? "REJECTED" : "APPLIED",
      lines: p.lines.map((l: any) => ({ item_id: l.item_id, state: mode === "receipt" ? "NEW" : p.target_state, status: mode === "rejection" ? "NOT_APPLIED" : "APPLIED", conflicts: mode === "rejection" ? ["STATE_CONFLICT"] : [] })) } });
  });
  await page.goto("/kitchen");
  if (mode === "malformed") { await expect(page.getByText(/Não foi possível preservar o lote/)).toBeVisible(); expect(calls).toBe(0); return; }
  await page.getByRole("button", { name: "Selecionar preparo: Fritas", exact: true }).click(); await page.getByRole("dialog").getByRole("checkbox").first().check();
  await page.getByRole("button", { name: "Iniciar preparo selecionado", exact: true }).click();
  if (mode === "rejection") { await expect(page.getByText(/Lote não aplicado/)).toBeVisible(); expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBeNull(); expect(rows[0].state).toBe("NEW"); return; }
  await expect(page.getByRole("button", { name: "Verificar mesmo lote", exact: true })).toBeVisible();
  let saved = await page.evaluate(key => sessionStorage.getItem(key), key);
  if (mode === "tampered") { await page.evaluate(key => { const value = JSON.parse(sessionStorage.getItem(key)!); value.payload.lines[0].quantity = 99; sessionStorage.setItem(key, JSON.stringify(value)); }, key); saved = await page.evaluate(key => sessionStorage.getItem(key), key); }
  if (mode === "revoked") await page.route("**/api/auth/me", route => route.fulfill({ status: 401, json: { code: "AUTH_REQUIRED", message: "Test revoked session" } }));
  if (mode === "other-station") { await page.goto("/bar"); await expect(page.getByRole("link", { name: "Retomar na estação original" })).toHaveAttribute("href", "/kitchen"); expect(calls).toBe(1); return; }
  if (mode === "session") await page.route("**/api/auth/me", route => route.fulfill({ json: { venue: { id: "venue-test" }, staff: { id: "operator-test" }, session: { id: "different-session" } } }));
  await page.getByRole("button", { name: "Verificar mesmo lote", exact: true }).click();
  await expect(page.getByText(mode === "session" ? /pertence à sessão original/ : mode === "revoked" ? /Confira sua sessão/ : /Resultado ainda não confirmado/)).toBeVisible();
  // The previous error notice can remain visible while the retry authenticates.
  // Wait for the expected request count instead of reading it before POST starts.
  await expect.poll(() => calls).toBe(["session", "revoked", "tampered"].includes(mode) ? 1 : 2);
  expect(await page.evaluate(key => sessionStorage.getItem(key), key)).toBe(saved);
});
