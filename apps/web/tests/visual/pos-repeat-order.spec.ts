import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";

async function setup(page: Page, mode = "valid") {
  await fixture(page, "normal", true);
  let catalog = [{ ...products[0], price_cents: 8000 }];
  const item = { id: "historical-item", product_id: "fries", product_name: "Fritas anteriores", quantity: 2, unit_price_cents: 7200, state: "DELIVERED",
    customization_snapshot: { variant: null, modifiers: [], special_instructions: "Sem sal" } };
  const detail = { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", version: 1, exposure_cents: 14400, charges_cents: 14400, payments_cents: 0,
    orders: [{ id: "historical-order", items: [item, { ...item, id: "cancelled", state: "CANCELLED" }] }], payments: [], refund_required_corrections: [] };
  if (mode === "inactive") catalog[0].active = false;
  if (mode === "unavailable") catalog[0].availability = "UNAVAILABLE";
  if (mode === "absent") catalog = [];
  if (mode === "legacy") Object.assign(item, { customization_snapshot: {} });
  if (mode === "removed") Object.assign(item, { customization_snapshot: { variant: { id: "removed", name: "Grande" }, modifiers: [], special_instructions: "" } });
  if (mode === "quantity") item.quantity = 100;
  if (mode === "configured") {
    Object.assign(catalog[0], {
      variants: [{ id: "small", name: "Pequena", price_cents: 8000, active: true, is_default: true, availability: "AVAILABLE", version: 1 },
        { id: "large", name: "Grande", price_cents: 10000, active: true, is_default: false, availability: "AVAILABLE", version: 1 }],
      modifier_groups: [{ id: "extras", name: "Adicionais", active: true, selection_mode: "MULTI", min_selections: 0, max_selections: 2, version: 1,
        options: [{ id: "extra", name: "Molho extra", price_delta_cents: 500, active: true, availability: "AVAILABLE", default_selected: false, semantic_kind: "ADD", version: 1 }] }],
    });
    Object.assign(item, { customization_snapshot: { variant: { id: "large", name: "Grande" },
      modifiers: [{ option_id: "extra", name: "Molho extra", group_name: "Adicionais", semantic_kind: "ADD" }], special_instructions: "Sem sal" } });
  }
  let failRead = false;
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: catalog } }));
  await page.route(/\/api\/pos\/tabs\/(\?.*)?$/, route => route.fulfill({ json: { results: [{ ...detail, orders: undefined }], next_offset: null } }));
  await page.route("**/api/pos/tabs/tab-test/", route => route.fulfill({ status: failRead ? 503 : 200, json: failRead ? { message: "Read failed" } : detail }));
  const posts: unknown[] = [];
  await page.route("**/api/pos/tabs/tab-test/orders/confirm/", route => { posts.push(route.request().postDataJSON()); return route.abort(); });
  await page.goto("/pos");
  await page.getByRole("button", { name: /^Comanda de teste ·/ }).click();
  return { posts, detail, changePrice: () => { catalog = catalog.map(p => ({ ...p, price_cents: 9000 })); }, fail: () => { failRead = true; } };
}
for (const width of [360, 390, 430]) test(`POS repeat explicit review preserves draft current price and original history at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const state = await setup(page);
  await page.getByRole("button", { name: /^Fritas/ }).click();
  const draft = page.getByRole("region", { name: "Pedido atual" }); await expect(draft.locator(".dataRow")).toHaveCount(1);
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" });
  await expect(dialog.getByText(/Anterior: Fritas anteriores/)).toContainText("72,00");
  await expect(dialog.getByText(/^Atual:/)).toContainText("80,00");
  await expect(dialog.getByText(/1 linha\(s\) canceladas/)).toBeVisible();
  await expect(dialog.getByText("Preço ou descrição mudou. Confira os valores atuais.")).toBeVisible();
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(draft.locator(".dataRow")).toHaveCount(1); expect(state.posts).toHaveLength(0);
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  await dialog.getByRole("button", { name: "Adicionar ao carrinho", exact: true }).dblclick();
  await expect(dialog).toHaveCount(0); await expect(draft.locator(".dataRow")).toHaveCount(2);
  await expect(draft.getByText("2× Fritas", { exact: true })).toBeVisible();
  await expect(draft.getByText("Observação: Sem sal")).toBeVisible(); expect(state.posts).toHaveLength(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `test-results/pos-repeat-order-draft-${width}.png`, fullPage: true });
  await draft.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect.poll(() => state.posts.length).toBe(1);
  const payload = state.posts[0] as { idempotency_key: string; lines: unknown[] };
  expect(payload.idempotency_key).not.toBe("historical-order");
  expect(payload.lines).toEqual([
    { product_id: "fries", quantity: 1, variant_id: null, modifier_option_ids: [], special_instructions: "" },
    { product_id: "fries", quantity: 2, variant_id: null, modifier_option_ids: [], special_instructions: "Sem sal" },
  ]);
  await expect(page.getByRole("button", { name: "Repetir rodada 1", exact: true })).toBeDisabled();
});
for (const mode of ["inactive", "unavailable", "absent", "legacy", "removed", "quantity"]) test(`POS repeat blocks ${mode} without defaults or partial inclusion`, async ({ page }) => {
  const state = await setup(page, mode); await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" });
  await expect(dialog.getByRole("button", { name: "Adicionar ao carrinho" })).toBeDisabled();
  await dialog.getByRole("button", { name: "Voltar" }).click();
  await expect(page.getByRole("region", { name: "Pedido atual" }).locator(".dataRow")).toHaveCount(0);
  expect(state.posts).toHaveLength(0);
});
test("POS repeat rejects catalog change during review and read failure preserves existing draft", async ({ page }) => {
  const state = await setup(page); await page.getByRole("button", { name: /^Fritas/ }).click();
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" });
  state.changePrice(); await page.clock.runFor(15001);
  await expect(dialog.getByRole("button", { name: "Adicionar ao carrinho" })).toBeDisabled();
  await expect(dialog.getByText(/O contexto mudou/)).toBeVisible();
  await dialog.getByRole("button", { name: "Voltar" }).click(); state.fail();
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  await expect(page.getByText(/Não foi possível conferir a rodada/)).toBeVisible();
  await expect(page.getByRole("region", { name: "Pedido atual" }).locator(".dataRow")).toHaveCount(1);
  expect(state.posts).toHaveLength(0);
});

test("POS repeat blocks an ambiguous cash receipt and does not confirm an order", async ({ page }) => {
  const state = await setup(page);
  await page.route("**/api/pos/tabs/tab-test/payments/", route => route.abort());
  await page.getByLabel("Valor do pagamento").fill("10,00");
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo recebimento" })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Repetir rodada 1", exact: true })).toBeDisabled();
  expect(state.posts).toHaveLength(0);
});

test("POS repeat disables receipt during review and closes when the Tab closes", async ({ page }) => {
  const state = await setup(page);
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  await expect(page.getByLabel("Valor do pagamento")).toBeDisabled();
  state.detail.state = "CLOSED"; await page.clock.runFor(15001);
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" });
  await expect(dialog.getByRole("button", { name: "Adicionar ao carrinho" })).toBeDisabled();
  await dialog.getByRole("button", { name: "Voltar" }).click();
  expect(state.posts).toHaveLength(0);
});
