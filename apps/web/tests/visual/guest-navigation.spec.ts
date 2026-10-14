import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`Guest persistent navigation preserves draft and canonical status ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await fixture(page, "normal", true);
  const context = { table: { label: "24" }, occupancy_active: true, can_start_occupancy: false,
    guest_policy: { emergency_blocked: false, table_ordering_enabled: true },
    tab: { id: "tab-test", display_label: "Minha comanda", state: "OPEN", exposure_cents: 7200,
      charges_cents: 7200, payments_cents: 0, remaining_capacity_cents: 100000, consumption_blocked: false,
      orders: [{ id: "order-test", status: "CONFIRMED", items: ["NEW", "ACCEPTED", "PREPARING", "READY", "PICKED_UP", "DELIVERED", "CANCELLED", "FUTURE"].map((state, i) => ({ id: `item-${i}`, product_name: `Produto ${i}`, quantity: 1, line_total_cents: 900, state })) }] } };
  await page.route("**/api/guest/qr/resolve/", route => route.fulfill({ json: context }));
  await page.route("**/api/guest/context/", route => route.fulfill({ json: context }));
  let mutations = 0;
  await page.route("**/api/guest/orders/confirm/", route => { mutations++; return route.abort(); });
  await page.goto("/guest/test-qr");
  await page.getByRole("button", { name: /^Fritas / }).click();
  const nav = page.getByRole("navigation", { name: "Navegação do cliente" });
  for (const name of ["Pedidos", "Conta", "Cardápio"]) {
    await nav.getByRole("button", { name, exact: true }).click();
    await expect(page.getByRole("region", { name, exact: true })).toBeFocused();
    await expect(nav).toBeInViewport();
  }
  await expect(page.getByRole("region", { name: "Pedido atual" }).getByText("1× Fritas", { exact: true })).toBeVisible();
  await expect(page.locator(".statusBadge").filter({ hasText: /^Recebido$/ })).toHaveCount(2);
  await expect(page.locator(".statusBadge").filter({ hasText: /^Pronto \/ chegando$/ })).toHaveCount(2);
  await expect(page.getByText("Preparando", { exact: true })).toBeVisible();
  await expect(page.getByText("Estado indisponível", { exact: true })).toBeVisible();
  expect(mutations).toBe(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `test-results/guest-navigation-${width}.png`, fullPage: true });
});

for (const required of [false, true]) test(`Guest modifier quick-add respects mandatory choice ${required}`, async ({ page }) => {
  await fixture(page, "normal", true);
  const product = { id: "optional", name: "Produto com opções", price_cents: 1000, available: true, fulfillment_station: "BAR",
    modifier_groups: [{ id: "group", name: "Adicionais", active: true, selection_mode: "SINGLE", min_selections: required ? 1 : 0,
      max_selections: 1, version: 1, sort_order: 0, options: [{ id: "option", name: "Limão", price_delta_cents: 100, active: true,
        availability: "AVAILABLE", default_selected: false, semantic_kind: "ADD", version: 1, sort_order: 0 }] }] };
  const context = { table: { label: "24" }, occupancy_active: true, can_start_occupancy: false,
    guest_policy: { emergency_blocked: false, table_ordering_enabled: true },
    tab: { id: "tab-test", display_label: "Minha comanda", state: "OPEN", exposure_cents: 0,
      charges_cents: 0, payments_cents: 0, remaining_capacity_cents: 100000, consumption_blocked: false, orders: [] } };
  await page.route("**/api/guest/qr/resolve/", route => route.fulfill({ json: context }));
  await page.route("**/api/guest/context/", route => route.fulfill({ json: context }));
  await page.route("**/api/guest/catalog/", route => route.fulfill({ json: { results: [product] } }));
  await page.goto("/guest/test-qr");
  await page.getByRole("button", { name: /^Produto com opções/ }).click();
  if (required) {
    await expect(page.getByRole("region", { name: "Configurar Produto com opções" })).toBeVisible();
    await expect(page.getByRole("button", { name: /^Adicionar ·/ })).toBeDisabled();
  } else {
    const draft = page.getByRole("region", { name: "Pedido atual" });
    await expect(draft.getByText("1× Produto com opções", { exact: true })).toBeVisible();
    await expect(page.getByRole("region", { name: "Configurar Produto com opções" })).toHaveCount(0);
    await draft.getByRole("button", { name: "Editar" }).click();
    await expect(page.getByRole("region", { name: "Configurar Produto com opções" })).toBeVisible();
    await page.getByRole("checkbox", { name: /Limão/ }).check();
    await page.getByRole("button", { name: /^Adicionar ·/ }).click();
    await expect(draft.getByText("+ Limão", { exact: true })).toBeVisible();
  }
});
