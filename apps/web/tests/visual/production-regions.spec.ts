import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y, products, queue } from "./fixtures";

for (const station of ["KITCHEN", "BAR"]) for (const width of [360, 390, 430]) {
  test(`Production peak region navigation ${station} ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await fixture(page, "normal", true);
    const items = Array.from({ length: 30 }, (_, i) => ({ ...queue[0], id: `peak-${i}`, order_id: `ticket-${i}`, state: i % 2 ? "NEW" : "PREPARING" }));
    const ready = { ...queue[1], id: "ready-test" };
    const catalog = products.map(product => ({ ...product, fulfillment_station: station }));
    const mutations: string[] = [];
    await page.route(`**/api/pos/production/${station}/`, route => route.fulfill({ json: { results: [...items, ready] } }));
    await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: catalog } }));
    await page.route("**/api/pos/catalog/products/*/availability/", async route => {
      mutations.push(route.request().postData()!);
      await route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Ação não autorizada." } });
    });
    await page.goto(station === "KITCHEN" ? "/kitchen" : "/bar");
    const nav = page.getByRole("navigation", { name: "Regiões da produção" });
    await expect(nav.getByRole("button", { name: "Fila 30", exact: true })).toBeVisible();
    const pass = page.getByRole("region", { name: "Pronto para retirada" });
    expect((await pass.boundingBox())!.y).toBeGreaterThan(900);
    await nav.getByRole("button", { name: "Prontos 1", exact: true }).click();
    await expect(pass).toBeFocused();
    expect((await pass.boundingBox())!.y).toBeGreaterThanOrEqual((await nav.boundingBox())!.height);
    await expect(nav).toBeInViewport();
    const availability = page.getByRole("region", { name: "Disponibilidade agora" });
    await nav.getByRole("button", { name: "Disponibilidade 3", exact: true }).click();
    await expect(availability).toBeFocused();
    await expect(nav).toBeInViewport();
    expect(mutations).toHaveLength(0);
    await layoutAndA11y(page);
    await page.screenshot({ path: `test-results/production-regions-${station}-${width}.png` });
    await availability.getByRole("button", { name: "Indisponibilizar Fritas", exact: true }).click();
    await expect(page.getByRole("alert").filter({ hasText: "CAPABILITY_REQUIRED" })).toContainText("Ação não autorizada");
    await expect(availability.getByRole("button", { name: "Indisponibilizar Fritas", exact: true })).toBeDisabled();
    await nav.getByRole("button", { name: "Fila 30", exact: true }).click();
    await expect(page.getByRole("region", { name: "Fila de pedidos" })).toBeFocused();
    await expect(page.getByRole("button", { name: /^Iniciar preparo:/ }).first()).toBeDisabled();
    expect(items.filter(item => item.state === "NEW")).toHaveLength(15);
    expect(mutations).toEqual(['{"state":"UNAVAILABLE"}']);
  });
}

for (const state of ["loading", "empty"] as const) test(`Production regions ${state}`, async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 900 }); await fixture(page, state, true); await page.goto("/kitchen");
  const nav = page.getByRole("navigation", { name: "Regiões da produção" });
  await expect(nav.getByRole("button", { name: `Prontos ${state === "loading" ? "—" : "0"}`, exact: true })).toBeVisible();
  await nav.getByRole("button", { name: /^Disponibilidade/ }).click();
  const region = page.getByRole("region", { name: "Disponibilidade agora" }); await expect(region).toBeFocused();
  await expect(region).toContainText(state === "loading" ? "Carregando disponibilidade" : "Nenhum produto roteado");
});
