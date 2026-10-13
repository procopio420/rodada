import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";

async function setup(page: Page, mode = "valid") {
  await fixture(page, "normal", true);
  const scope = { venue_id: "venue-test", session_id: "guest-session", table_id: "table-test", occupancy_id: "visit-test", generation: 1 };
  const item = { id: "historical-item", product_id: "fries", product_name: "Fritas anteriores", quantity: 2, unit_price_cents: 7200,
    line_total_cents: 14400, state: "DELIVERED", customization_snapshot: { variant: null, modifiers: [], special_instructions: "Sem sal" } };
  const tab = { id: "tab-test", display_label: "Minha comanda", state: "OPEN", exposure_cents: 14400, charges_cents: 14400, payments_cents: 0,
    consumption_blocked: false, remaining_capacity_cents: 50000, orders: [{ id: "historical-order", status: "CONFIRMED", items: [item] }] };
  const context = { session_scope: scope, table: { label: "24" }, occupancy_active: true, can_start_occupancy: false, tab,
    guest_policy: { emergency_blocked: false, table_ordering_enabled: true }, guest_session_token: "guest-test-credential" };
  let catalog = [{ ...products[0], price_cents: 8000 }];
  if (mode === "absent") catalog = [];
  if (mode === "unavailable") catalog[0].available = false;
  if (mode === "legacy") Object.assign(item, { customization_snapshot: {} });
  if (mode === "variant") Object.assign(item, { customization_snapshot: { variant: { id: "removed", name: "Grande" }, modifiers: [], special_instructions: "Sem sal" } });
  if (mode === "quantity") item.quantity = 100;
  if (mode === "configured") {
    Object.assign(catalog[0], { variants: [{ id: "small", name: "Pequena", price_cents: 8000, active: true, is_default: true, availability: "AVAILABLE", version: 1 },
      { id: "large", name: "Grande", price_cents: 10000, active: true, is_default: false, availability: "AVAILABLE", version: 1 }],
      modifier_groups: [{ id: "extras", name: "Adicionais", active: true, selection_mode: "MULTI", min_selections: 0, max_selections: 2, version: 1,
        options: [{ id: "extra", name: "Molho extra", price_delta_cents: 500, active: true, availability: "AVAILABLE", default_selected: false, semantic_kind: "ADD", version: 1 }] }] });
    Object.assign(item, { customization_snapshot: { variant: { id: "large", name: "Grande" }, modifiers: [{ option_id: "extra", name: "Molho extra", group_name: "Adicionais", semantic_kind: "ADD" }], special_instructions: "Sem sal" } });
  }
  let resolves = 0, fail = false, revoked = false;
  const attempts: string[] = [];
  await page.route("**/api/guest/qr/resolve/", route => { resolves++; return route.fulfill({ json: context }); });
  await page.route("**/api/guest/context/", route => route.fulfill({ status: revoked ? 403 : fail ? 503 : 200,
    json: revoked ? { code: "GUEST_SESSION_REVOKED" } : fail ? { message: "Leitura indisponível" } : context }));
  await page.route("**/api/guest/catalog/", route => route.fulfill({ json: { results: catalog } }));
  await page.route("**/api/guest/orders/confirm/", route => { attempts.push(route.request().postData()!); return route.abort(); });
  await page.goto("/guest/test-qr"); await expect(page.getByRole("button", { name: "Repetir rodada 1", exact: true })).toBeEnabled();
  return { context, attempts, resolves: () => resolves, price: () => { catalog = catalog.map(p => ({ ...p, price_cents: 9000 })); }, fail: () => { fail = true; }, revoke: () => { revoked = true; } };
}
for (const width of [360, 390, 430]) test(`Guest repeat explicit review draft preservation current price and pending guard at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const state = await setup(page);
  await page.getByRole("button", { name: /^Fritas / }).click();
  const draft = page.getByRole("heading", { name: "Revisar pedido", exact: true }).locator("..");
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" });
  await expect(dialog.getByText(/^Anterior:/)).toContainText("72,00"); await expect(dialog.getByText(/^Atual:/)).toContainText("80,00");
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click(); await expect(draft.getByText("1× Fritas", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  await dialog.getByRole("button", { name: "Adicionar ao carrinho" }).dblclick();
  await expect(dialog).toHaveCount(0); await expect(draft.getByText("2× Fritas", { exact: true })).toBeVisible();
  await expect(draft.getByText("1× Fritas", { exact: true })).toBeVisible(); await expect(draft.getByText("Observação: Sem sal")).toBeVisible();
  expect(state.attempts).toHaveLength(0); expect(state.resolves()).toBe(1);
  await layoutAndA11y(page); await page.screenshot({ path: `test-results/guest-repeat-draft-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect.poll(() => state.attempts.length).toBe(1);
  const payload = JSON.parse(state.attempts[0]); expect(payload.idempotency_key).not.toBe("historical-order");
  expect(payload.lines).toEqual([{ product_id: "fries", quantity: 1, variant_id: null, modifier_option_ids: [], special_instructions: "" },
    { product_id: "fries", quantity: 2, variant_id: null, modifier_option_ids: [], special_instructions: "Sem sal" }]);
  await expect(page.getByRole("button", { name: "Repetir rodada 1", exact: true })).toBeDisabled();
});
for (const mode of ["absent", "unavailable", "legacy", "variant", "quantity"]) test(`Guest repeat blocks ${mode} without automatic substitution`, async ({ page }) => {
  const state = await setup(page, mode); await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" }); await expect(dialog.getByRole("button", { name: "Adicionar ao carrinho" })).toBeDisabled();
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click(); expect(state.attempts).toHaveLength(0); expect(state.resolves()).toBe(1);
});
for (const change of ["price", "block", "emergency", "revoke", "fail", "scope", "tab", "token"]) test(`Guest repeat inclusion revalidates ${change} and preserves draft`, async ({ page }) => {
  const state = await setup(page); await page.getByRole("button", { name: /^Fritas / }).click();
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" }); await expect(dialog).toBeVisible();
  if (change === "price") state.price();
  if (change === "block") state.context.guest_policy.table_ordering_enabled = false;
  if (change === "emergency") state.context.guest_policy.emergency_blocked = true;
  if (change === "revoke") state.revoke(); if (change === "fail") state.fail();
  if (change === "scope") state.context.session_scope.generation++;
  if (change === "tab") state.context.tab.id = "other-tab";
  if (change === "token") await page.evaluate(() => sessionStorage.setItem("rodada.guest.session.test-qr", "other-token"));
  await dialog.getByRole("button", { name: "Adicionar ao carrinho" }).click();
  await expect(dialog.getByRole("button", { name: "Adicionar ao carrinho" })).toBeDisabled();
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
  await expect(page.getByText("2× Fritas", { exact: true })).toHaveCount(0); expect(state.attempts).toHaveLength(0); expect(state.resolves()).toBe(1);
});
test("Guest repeat keeps variant modifier note separate from the default draft", async ({ page }) => {
  const state = await setup(page, "configured"); await page.getByRole("button", { name: /^Fritas / }).click();
  await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" });
  await expect(dialog.getByText(/^Atual:/)).toContainText("105,00"); await dialog.getByRole("button", { name: "Adicionar ao carrinho" }).click();
  await expect(dialog).toHaveCount(0);
  await page.getByRole("button", { name: /^Enviar ·/ }).click(); await expect.poll(() => state.attempts.length).toBe(1);
  expect(JSON.parse(state.attempts[0]).lines).toEqual([{ product_id: "fries", quantity: 1, variant_id: "small", modifier_option_ids: [], special_instructions: "" },
    { product_id: "fries", quantity: 2, variant_id: "large", modifier_option_ids: ["extra"], special_instructions: "Sem sal" }]);
});
