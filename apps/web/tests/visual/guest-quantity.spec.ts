import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";

async function setup(page: Page, configured = false) {
  await fixture(page, "normal", true);
  const context = { session_scope: { venue_id: "venue-test", session_id: "session-test", table_id: "table-test", occupancy_id: "visit-test", generation: 1 },
    table: { label: "24" }, occupancy_active: true, can_start_occupancy: false, guest_session_token: "quantity-test-token",
    guest_policy: { emergency_blocked: false, table_ordering_enabled: true },
    tab: { id: "tab-test", display_label: "Minha comanda", state: "OPEN", exposure_cents: 0, charges_cents: 0, payments_cents: 0,
      consumption_blocked: false, remaining_capacity_cents: 1000000, orders: [] } };
  const catalog = [{ ...products[0] }]; let readStatus = 200;
  if (configured) Object.assign(catalog[0], {
    variants: ["small", "large"].map(id => ({ id, name: id, price_cents: 7200, active: true, availability: "AVAILABLE", is_default: id === "small", version: 1 })),
    modifier_groups: [{ id: "extras", name: "Adicionais", active: true, selection_mode: "MULTI", min_selections: 0, max_selections: 2, version: 1,
      options: ["one", "two"].map(id => ({ id, name: id, price_delta_cents: 100, active: true, availability: "AVAILABLE", default_selected: false, semantic_kind: "ADD", version: 1 })) }],
  });
  const attempts: string[] = [];
  await page.route("**/api/guest/qr/resolve/", route => route.fulfill({ json: context }));
  await page.route("**/api/guest/context/", route => route.fulfill({ status: readStatus, json: readStatus === 403 ? { code: "GUEST_SESSION_REVOKED" } : context }));
  await page.route("**/api/guest/catalog/", route => route.fulfill({ json: { results: catalog } }));
  await page.route("**/api/guest/orders/confirm/", route => { attempts.push(route.request().postData()!); return route.abort(); });
  await page.goto("/guest/test-qr");
  const product = page.getByRole("button", { name: /^Fritas / });
  await product.click();
  if (configured) await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  return { context, catalog, attempts, product, fail: () => { readStatus = 503; }, revoke: () => { readStatus = 403; } };
}
for (const width of [360, 390, 430]) test(`Guest grouped quantity controls zero removal and pending payload ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const state = await setup(page);
  const draft = page.getByRole("region", { name: "Pedido atual" });
  await state.product.dblclick(); await expect(draft.getByRole("group")).toHaveCount(1);
  await expect(draft.getByText("3× Fritas", { exact: true })).toBeVisible();
  await draft.getByRole("button", { name: "Diminuir quantidade de Fritas" }).click();
  await draft.getByRole("button", { name: "Aumentar quantidade de Fritas" }).click();
  await expect(page.getByRole("button", { name: /^Enviar ·/ })).toContainText("216,00");
  await layoutAndA11y(page); await page.screenshot({ path: `test-results/guest-quantity-${width}.png`, fullPage: true });
  for (let i = 0; i < 3; i++) await draft.getByRole("button", { name: "Diminuir quantidade de Fritas" }).click();
  await expect(draft).toHaveCount(0); await expect(page.getByRole("button", { name: /^Enviar ·/ })).toBeDisabled();
  await state.product.dblclick(); await page.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect.poll(() => state.attempts.length).toBe(1);
  await expect(draft.getByRole("button", { name: "Aumentar quantidade de Fritas" })).toBeDisabled();
  await expect(draft.getByRole("button", { name: "Diminuir quantidade de Fritas" })).toBeDisabled();
  await expect(draft.getByRole("button", { name: "Editar" })).toBeDisabled();
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect.poll(() => state.attempts.length).toBe(2); expect(state.attempts[1]).toBe(state.attempts[0]);
  expect(JSON.parse(state.attempts[0]).lines[0].quantity).toBe(2);
});

test("Guest editing keeps exact notes distinct and merges only identical configurations", async ({ page }) => {
  const state = await setup(page); await state.product.click();
  const draft = page.getByRole("region", { name: "Pedido atual" });
  await draft.getByRole("button", { name: "Editar" }).click();
  await page.getByLabel("Pedido especial (opcional)").fill("Sem sal"); await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await state.product.click(); await expect(draft.getByRole("group")).toHaveCount(2);
  await draft.getByRole("group", { name: "Item 2 do pedido", exact: true }).getByRole("button", { name: "Editar" }).click();
  await page.getByLabel("Pedido especial (opcional)").fill("Sem sal "); await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await expect(draft.getByRole("group")).toHaveCount(2);
  await draft.getByRole("group", { name: "Item 2 do pedido", exact: true }).getByRole("button", { name: "Editar" }).click();
  await page.getByLabel("Pedido especial (opcional)").fill("Sem sal"); await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await expect(draft.getByRole("group")).toHaveCount(1); await expect(draft.getByText("3× Fritas", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(0);
});

for (const change of ["unavailable", "table", "emergency", "consumption", "closed", "offline", "revoked"]) test(`Guest quantity guards ${change}`, async ({ page }) => {
  const state = await setup(page);
  if (change === "unavailable") state.catalog[0].available = false;
  if (change === "table") state.context.guest_policy.table_ordering_enabled = false;
  if (change === "emergency") state.context.guest_policy.emergency_blocked = true;
  if (change === "consumption") state.context.tab.consumption_blocked = true;
  if (change === "closed") state.context.tab.state = "CLOSED";
  if (change === "offline") state.fail(); if (change === "revoked") state.revoke();
  await page.getByRole("button", { name: "Atualizar comanda" }).click();
  if (change === "revoked") await expect(page.getByRole("heading", { name: "Não foi possível abrir o pedido" })).toBeVisible();
  else {
    const draft = page.getByRole("region", { name: "Pedido atual" });
    await expect(draft.getByRole("button", { name: "Aumentar quantidade de Fritas" })).toBeDisabled();
    await expect(page.getByRole("button", { name: /^Enviar ·/ })).toBeDisabled();
    await draft.getByRole("button", { name: "Diminuir quantidade de Fritas" }).click();
    await expect(draft).toHaveCount(0);
  }
  expect(state.attempts).toHaveLength(0);
});

test("Guest 99 limit rejects another catalog unit without losing the draft", async ({ page }) => {
  const state = await setup(page);
  const plus = page.getByRole("button", { name: "Aumentar quantidade de Fritas" });
  for (let i = 1; i < 99; i++) await plus.click();
  await expect(plus).toBeDisabled(); await state.product.click();
  await expect(page.getByText(/A quantidade agrupada ultrapassa 99/)).toBeVisible();
  await expect(page.getByText("99× Fritas", { exact: true })).toBeVisible(); expect(state.attempts).toHaveLength(0);
  const draft = page.getByRole("region", { name: "Pedido atual" });
  await draft.getByRole("button", { name: "Editar" }).click();
  await page.getByLabel("Pedido especial (opcional)").fill("Sem sal"); await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await state.product.click();
  await draft.getByRole("group", { name: "Item 2 do pedido", exact: true }).getByRole("button", { name: "Editar" }).click();
  await page.getByLabel("Pedido especial (opcional)").fill("Sem sal"); await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await expect(page.getByLabel("Pedido especial (opcional)")).toBeVisible();
  await page.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(draft.getByRole("group")).toHaveCount(2);
  await expect(draft.getByText("99× Fritas", { exact: true })).toBeVisible();
  await expect(draft.getByText("1× Fritas", { exact: true })).toBeVisible();
});

test("Guest grouping uses variant and unordered option IDs, preserving different selections", async ({ page }) => {
  const state = await setup(page, true);
  const add = async (variant: string, options: string[]) => {
    await state.product.click(); await page.getByRole("radio", { name: new RegExp(`^${variant}`) }).check();
    for (const option of options) await page.getByRole("checkbox", { name: new RegExp(`^${option}`) }).check();
    await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  };
  await add("small", ["one", "two"]); await add("small", ["two", "one"]);
  await add("large", ["one", "two"]); await add("small", ["one"]);
  const draft = page.getByRole("region", { name: "Pedido atual" });
  await expect(draft.getByRole("group")).toHaveCount(4);
  await expect(draft.getByText("2× Fritas", { exact: true })).toHaveCount(1);
  await page.getByRole("button", { name: /^Enviar ·/ }).click(); await expect.poll(() => state.attempts.length).toBe(1);
  const lines = JSON.parse(state.attempts[0]).lines;
  expect(lines.map((line: { quantity: number }) => line.quantity)).toEqual([1, 2, 1, 1]);
  expect(lines.map((line: { variant_id: string }) => line.variant_id)).toEqual(["small", "small", "large", "small"]);
  expect(lines.map((line: { modifier_option_ids: string[] }) => line.modifier_option_ids)).toEqual([[], ["one", "two"], ["one", "two"], ["one"]]);
});

test("Guest repeat grouped historical overflow preserves all existing units", async ({ page }) => {
  const state = await setup(page);
  const historical = { id: "history-item", product_id: "fries", product_name: "Fritas", quantity: 99,
    unit_price_cents: 7200, line_total_cents: 712800, state: "NEW", customization_snapshot: { variant: null, modifiers: [], special_instructions: "" } };
  Object.assign(state.context.tab, { orders: [{ id: "history-test", status: "CONFIRMED", items: [historical, { ...historical, id: "history-extra", quantity: 1, line_total_cents: 7200 }] }] });
  await page.getByRole("button", { name: "Atualizar comanda" }).click();
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  await page.getByRole("dialog", { name: "Conferir rodada" }).getByRole("button", { name: "Confirmar e enviar rodada" }).click();
  await expect(page.getByRole("dialog", { name: "Conferir rodada" })).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(page.getByText(/A quantidade agrupada ultrapassa 99/)).toBeVisible();
  await expect(page.getByRole("region", { name: "Pedido atual" }).getByText("1× Fritas", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(0);
});
