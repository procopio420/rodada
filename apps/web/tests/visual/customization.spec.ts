import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const product = { id: "burger", name: "Hambúrguer", price_cents: 2000, available: true, availability: "AVAILABLE", fulfillment_station: "KITCHEN", active: true,
  variants: [{ id: "double", name: "Duplo", price_cents: 3000, active: true, availability: "AVAILABLE", is_default: true, version: 1 }],
  modifier_groups: [{ id: "cooking", name: "Ponto", selection_mode: "SINGLE", min_selections: 1, max_selections: 1, active: true, version: 1, options: [{ id: "medium", name: "Ao ponto", price_delta_cents: 0, active: true, availability: "AVAILABLE", semantic_kind: "CHOICE", default_selected: false, version: 1 }] },
    { id: "extras", name: "Adicionais", selection_mode: "MULTI", min_selections: 0, max_selections: 2, active: true, version: 1, options: [{ id: "bacon", name: "Bacon", price_delta_cents: 500, active: true, availability: "AVAILABLE", semantic_kind: "ADD", version: 1 }, { id: "cheese", name: "Queijo", price_delta_cents: 300, active: true, availability: "AVAILABLE", semantic_kind: "ADD", version: 1 }, { id: "onion", name: "Sem cebola", price_delta_cents: 0, active: true, availability: "UNAVAILABLE", semantic_kind: "REMOVE", version: 1 }] }] };
for (const width of [360, 390, 768]) {
  test(`customization choices and production text readable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    await page.route("**/api/guest/catalog/", route => route.fulfill({ json: { results: [product] } }));
    await page.goto("/guest/visual-test");
    await page.getByRole("button", { name: /Hambúrguer/ }).click();
    await expect(page.getByRole("button", { name: /^Adicionar ·/ })).toBeDisabled();
    await page.getByLabel("Ao ponto").check();
    await page.getByLabel(/Bacon/).check();
    await page.getByLabel(/Queijo/).check();
    await expect(page.getByLabel(/Sem cebola/)).toBeDisabled();
    await page.getByLabel("Pedido especial (opcional)").fill("Molho separado");
    await expect(page.getByRole("button", { name: /^Adicionar ·/ })).toContainText("38,00");
    await stable(page); await layoutAndA11y(page);
    await page.screenshot({ path: `test-results/customization-${width}.png`, fullPage: true });
    await page.getByRole("button", { name: /^Adicionar ·/ }).click();
    await expect(page.getByText("Observação: Molho separado")).toBeVisible();
    await page.route("**/api/pos/production/KITCHEN/", route => route.fulfill({ json: { results: [{ id: "custom-item", state: "PREPARING", quantity: 2, product_name: "Hambúrguer", tab_label: "Mesa 27", created_at: "2026-10-08T20:00:00Z", customization_snapshot: { variant: { name: "Duplo" }, modifiers: [{ name: "Bacon", group_name: "Adicionais", semantic_kind: "ADD" }, { name: "Queijo", group_name: "Adicionais", semantic_kind: "ADD" }], special_instructions: "Molho separado" } }] } }));
    await page.goto("/kitchen");
    await expect(page.getByText("+ Bacon", { exact: true })).toBeVisible();
    await expect(page.getByText("Variação: Duplo")).toBeVisible();
    await expect(page.getByText("Observação: Molho separado")).toBeVisible();
    await stable(page); await layoutAndA11y(page);
    await page.screenshot({ path: `test-results/customization-kitchen-${width}.png`, fullPage: true });
  });
}
for (const width of [360, 390]) {
  test(`manager customization editor remains accessible at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    await page.route("**/api/pos/catalog/products/**", async route => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith("/customization/")) return route.fulfill({ json: { ...product, reusable_groups: [] } });
      return route.fulfill({ json: { results: [product] } });
    });
    await page.goto("/manage/catalog");
    await page.getByLabel("Produto", { exact: true }).selectOption("burger");
    await page.getByRole("button", { name: "Criar grupo", exact: true }).click();
    await page.getByLabel("Nome", { exact: true }).fill("Ponto da carne");
    await page.getByLabel("Mínimo (1 ou mais = obrigatório)").fill("1");
    await stable(page); await layoutAndA11y(page);
    await page.screenshot({ path: `test-results/customization-manager-${width}.png`, fullPage: true });
  });
}

test("optional single choice can be removed and stale choices require explicit review", async ({ page }) => {
  await fixture(page);
  const optional = { ...product.modifier_groups[1], id: "optional", name: "Molho", selection_mode: "SINGLE", min_selections: 0, max_selections: 1, options: [{ ...product.modifier_groups[1].options[0], id: "sauce", name: "Molho extra", price_delta_cents: 200, default_selected: false }] };
  const menu = { ...product, modifier_groups: [optional] };
  await page.route("**/api/guest/catalog/", route => route.fulfill({ json: { results: [menu] } }));
  await page.goto("/guest/visual-test");
  await page.getByRole("button", { name: /Hambúrguer/ }).click();
  await page.getByLabel(/Molho extra/).check();
  await expect(page.getByRole("button", { name: /^Adicionar ·/ })).toContainText("32,00");
  await page.getByLabel(/Molho extra/).uncheck();
  await expect(page.getByRole("button", { name: /^Adicionar ·/ })).toContainText("30,00");
  await page.getByLabel(/Molho extra/).check();
  await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  optional.options[0].availability = "UNAVAILABLE";
  await page.getByRole("button", { name: "Atualizar comanda" }).click();
  await expect(page.getByRole("button", { name: /^Enviar ·/ })).toBeDisabled();
  await page.getByRole("button", { name: "Editar", exact: true }).click();
  await expect(page.getByLabel(/Molho extra/)).toBeDisabled();
  await page.getByRole("button", { name: "Remover escolhas indisponíveis" }).click();
  await expect(page.getByRole("button", { name: /^Adicionar ·/ })).toBeEnabled();
  await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await expect(page.getByRole("button", { name: /^Enviar ·/ })).toBeEnabled();
});
