import { attendanceBill, attendanceDraft } from "./attendance-actions";
import { addCatalogItem } from "./category-actions";
import { openOtherTabs } from "./attendance-actions";
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
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: catalog } }));
  await page.route(/\/api\/attendance\/tabs\/(\?.*)?$/, route => route.fulfill({ json: { results: [{ ...detail, orders: undefined }], next_offset: null } }));
  await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ status: failRead ? 503 : 200, json: failRead ? { message: "Read failed" } : detail }));
  const posts: unknown[] = [];
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", route => { posts.push(route.request().postDataJSON()); return route.abort(); });
  await page.goto("/attendance"); await openOtherTabs(page);
  await page.getByRole("button", { name: /^Comanda de teste\s/ }).click();
  await attendanceBill(page);
  return { posts, detail, changePrice: () => { catalog = catalog.map(p => ({ ...p, price_cents: 9000 })); }, fail: () => { failRead = true; } };
}
async function review(page: Page) {
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  const region = page.getByRole("region", { name: "Repetir rodada", exact: true });
  await expect(region.getByRole("heading", { name: "Mais uma rodada.", exact: true })).toBeVisible();
  return region;
}
async function originalDraft(page: Page) {
  await page.getByRole("region", { name: "Comanda selecionada", exact: true }).getByRole("button", { name: "Voltar", exact: true }).click();
  await addCatalogItem(page, "Fritas", 0);
  return attendanceDraft(page);
}
for (const width of [360, 390, 430]) test(`Repeat explicit review preserves draft current price and original history at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const state = await setup(page);
  await page.getByRole("button", { name: "Voltar", exact: true }).click();
  await addCatalogItem(page, "Fritas"); await attendanceBill(page);
  let region = await review(page);
  await expect(region.getByText(/Anterior:.*72,00/)).toBeVisible();
  await expect(region.getByText("R$ 80,00 por unidade", { exact: true })).toBeVisible();
  await expect(region.getByText(/1 linha\(s\) canceladas/)).toBeVisible();
  await expect(region.getByText(/Preço ou descrição mudou/)).toBeVisible();
  await region.getByRole("button", { name: "Voltar", exact: true }).click();
  const draft = await originalDraft(page); await expect(draft.locator(".ux2ReviewRow")).toHaveCount(1);
  expect(state.posts).toHaveLength(0); await attendanceBill(page); region = await review(page);
  await layoutAndA11y(page);
  await region.getByRole("button", { name: "Repetir rodada · enviar", exact: true }).dblclick();
  await expect(region).toHaveCount(0); await expect.poll(() => state.posts.length).toBe(1);
  const payload = state.posts[0] as { idempotency_key: string; lines: unknown[] };
  expect(payload.idempotency_key).not.toBe("historical-order");
  expect(payload.lines).toEqual([{ product_id: "fries", quantity: 2, variant_id: null, modifier_option_ids: [], special_instructions: "Sem sal" }]);
  await expect(page.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
  // Resolve the same frozen intent before reopening the original draft.
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", route => {
    const replay = route.request().postDataJSON(); expect(replay).toEqual(payload);
    return route.fulfill({ json: { id: "repeat-confirmed", tab_id: "tab-test" } });
  });
  state.detail.orders.push({ ...state.detail.orders[0], id: "repeat-confirmed" });
  await page.getByRole("button", { name: "Verificar mesmo pedido", exact: true }).click();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  await addCatalogItem(page, "Fritas", 0); await attendanceDraft(page);
  await expect(draft.locator(".ux2ReviewRow")).toHaveCount(1);
  await expect(draft.getByText("1× Fritas", { exact: true })).toBeVisible();
  await page.screenshot({ path: `test-results/repeat-order-direct-${width}.png`, fullPage: true });
});
for (const mode of ["inactive", "unavailable", "absent", "legacy", "removed", "quantity"]) test(`Repeat blocks ${mode} without defaults or partial inclusion`, async ({ page }) => {
  const state = await setup(page, mode); const region = await review(page);
  await expect(region.getByRole("button", { name: "Repetir rodada · enviar", exact: true })).toBeDisabled();
  await expect(region.getByRole("alert")).not.toHaveCount(0);
  await region.getByRole("button", { name: "Voltar", exact: true }).click();
  const draft = await originalDraft(page);
  await expect(draft.getByRole("button", { name: "Adicione itens para enviar", exact: true })).toBeVisible();
  await expect(draft.locator(".ux2ReviewRow")).toHaveCount(0);
  expect(state.posts).toHaveLength(0);
});
test("Repeat rejects catalog change during review and read failure preserves existing draft", async ({ page }) => {
  const state = await setup(page); await page.getByRole("button", { name: "Voltar", exact: true }).click();
  await addCatalogItem(page, "Fritas"); await attendanceBill(page); const region = await review(page);
  state.changePrice(); await page.clock.runFor(15001);
  await expect(region.getByRole("button", { name: "Repetir rodada · enviar", exact: true })).toBeDisabled();
  await expect(region.getByText(/O contexto mudou/)).toBeVisible();
  await region.getByRole("button", { name: "Voltar", exact: true }).click(); state.fail();
  await page.getByRole("button", { name: "Repetir rodada 1", exact: true }).click();
  await expect(page.getByText(/Não foi possível conferir a rodada/)).toBeVisible();
  const draft = await originalDraft(page); await expect(draft.locator(".ux2ReviewRow")).toHaveCount(1);
  expect(state.posts).toHaveLength(0);
});
test("Repeat keeps historical variant modifier and note distinct from existing default draft", async ({ page }) => {
  const state = await setup(page, "configured"); await page.getByRole("button", { name: "Voltar", exact: true }).click();
  await addCatalogItem(page, "Fritas");
  await page.getByRole("dialog", { name: "Personalizar Fritas", exact: true }).getByRole("button", { name: /^Adicionar ·/ }).click();
  await attendanceBill(page); const region = await review(page);
  await expect(region.getByText("R$ 105,00 por unidade", { exact: true })).toBeVisible();
  await expect(region.getByText("Variação: Grande", { exact: true })).toBeVisible();
  await region.getByRole("button", { name: "Repetir rodada · enviar", exact: true }).click();
  await expect.poll(() => state.posts.length).toBe(1);
  expect((state.posts[0] as { lines: unknown[] }).lines).toEqual([{ product_id: "fries", quantity: 2, variant_id: "large", modifier_option_ids: ["extra"], special_instructions: "Sem sal" }]);
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
  const payload = state.posts[0];
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", route => { expect(route.request().postDataJSON()).toEqual(payload); return route.fulfill({ json: { id: "repeat-configured", tab_id: "tab-test" } }); });
  state.detail.orders.push({ ...state.detail.orders[0], id: "repeat-configured" });
  await page.getByRole("button", { name: "Verificar mesmo pedido", exact: true }).click();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  await addCatalogItem(page, "Fritas", 0); const draft = await attendanceDraft(page);
  await expect(draft.locator(".ux2ReviewRow")).toHaveCount(1);
  await expect(draft.getByText("Variação: Pequena", { exact: true })).toBeVisible();
  await expect(draft.getByText("Variação: Grande", { exact: true })).toHaveCount(0);
});
