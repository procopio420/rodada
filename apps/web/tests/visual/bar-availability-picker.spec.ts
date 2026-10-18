import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";
import { chooseBarAvailability, closeBarAvailability } from "./station-availability-actions";

async function setup(page: Page) {
  await fixture(page, "normal", true);
  const catalog = [
    { ...products[2], category: "Bebidas", availability_version: 1 },
    { ...products[2], id: "juice", name: "Suco do catálogo", category: "Sucos", availability_version: 1 },
    { ...products[2], id: "inactive", name: "Produto inativo", active: false, category: "Bebidas", availability_version: 1 },
    { ...products[0], category: "Cozinha", availability_version: 1 },
  ];
  await page.route("**/api/pos/catalog/products/", r => r.fulfill({ json: { results: catalog } }));
  await page.route("**/api/pos/production/BAR/", r => r.fulfill({ json: { results: [] } }));
  return catalog;
}

for (const width of [360, 390, 430, 1280]) test(`Bar availability categories and confirmed return ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const catalog = await setup(page);
  const sends: unknown[] = [];
  await page.route("**/api/pos/catalog/products/*/availability/", async route => {
    const p = route.request().postDataJSON(), id = route.request().url().split("/").at(-3)!;
    sends.push(p); const product = catalog.find(c => c.id === id)!;
    product.availability = p.state; product.availability_version++;
    await route.fulfill({ json: { command_id: "command-test", product_id: id, ...p, requested_state: p.state, state: p.state, version: product.availability_version, status: "APPLIED", changed: true, conflicts: [] } });
  });
  await page.goto("/bar");
  await expect(page.getByRole("button", { name: "Indisponibilizar Bebida de teste", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Indisponibilizar item", exact: true }).click();
  const nav = page.getByRole("navigation", { name: "Categorias da disponibilidade" });
  await expect(nav.getByRole("button").first()).toHaveText("Todos2 itens");
  await expect(nav.getByRole("button", { name: /Cozinha/ })).toHaveCount(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `test-results/bar-availability-categories-${width}.png` });
  await nav.getByRole("button", { name: /^Todos/ }).click();
  await expect(page.getByRole("button", { name: "Indisponibilizar Produto inativo", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Indisponibilizar Bebida de teste", exact: true }).click();
  expect(sends).toHaveLength(0);
  await page.getByRole("button", { name: "Voltar", exact: true }).click();
  expect(sends).toHaveLength(0);
  await page.getByRole("button", { name: "Indisponibilizar Suco do catálogo", exact: true }).click();
  await layoutAndA11y(page);
  await page.screenshot({ path: `test-results/bar-availability-confirm-${width}.png` });
  await page.getByRole("button", { name: "Sim, indisponibilizar", exact: true }).dblclick();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(page.getByRole("main")).toBeFocused();
  expect(await page.evaluate(() => window.scrollY)).toBeLessThan(10);
  expect(sends).toHaveLength(1); expect(catalog[1].availability).toBe("UNAVAILABLE");
  await chooseBarAvailability(page, "Suco do catálogo", true);
  await expect(page.getByRole("button", { name: "Sim, reativar", exact: true })).toBeEnabled();
  await closeBarAvailability(page); expect(sends).toHaveLength(1);
});

test("Bar availability category search shows empty feedback", async ({ page }) => {
  await setup(page); await page.goto("/bar");
  await page.getByRole("button", { name: "Indisponibilizar item", exact: true }).click();
  await page.getByRole("navigation", { name: "Categorias da disponibilidade" }).getByRole("button", { name: /^Sucos/ }).click();
  await page.getByLabel("Buscar item no cardápio", { exact: true }).fill("Bebida");
  await expect(page.getByText("Nenhum item encontrado nesta categoria.")).toBeVisible();
  await page.getByRole("button", { name: "Voltar", exact: true }).click();
  await page.getByRole("navigation", { name: "Categorias da disponibilidade" }).getByRole("button", { name: /^Todos/ }).click();
  await expect(page.getByRole("button", { name: "Indisponibilizar Bebida de teste", exact: true })).toBeVisible();
  await page.keyboard.press("Escape"); await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Indisponibilizar item", exact: true })).toBeFocused();
});

for (const failure of ["conflict", "readback"]) test(`Bar availability keeps confirmation on ${failure}`, async ({ page }) => {
  const catalog = await setup(page); let failRead = true;
  const attempts: unknown[] = [];
  await page.route("**/api/pos/catalog/products/beer/availability/", async route => {
    const p = route.request().postDataJSON(); attempts.push(p);
    if (failure === "readback") {
      catalog[0].availability = p.state; catalog[0].availability_version = 2;
      await page.route("**/api/pos/catalog/products/", r => failRead ? r.fulfill({ status: 503, json: {} }) : r.fulfill({ json: { results: catalog } }));
    }
    await route.fulfill({ status: failure === "conflict" ? 409 : 200, json: { command_id: "command-test", product_id: "beer", ...p, requested_state: p.state, state: failure === "conflict" ? "AVAILABLE" : p.state, version: 2, status: failure === "conflict" ? "REJECTED" : "APPLIED", changed: failure !== "conflict", conflicts: failure === "conflict" ? ["VERSION_CONFLICT"] : [] } });
  });
  await page.goto("/bar"); await chooseBarAvailability(page, "Bebida de teste");
  await page.getByRole("button", { name: "Sim, indisponibilizar", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  if (failure === "conflict") await expect(page.getByRole("dialog").getByText(/Disponibilidade não aplicada/)).toBeVisible();
  else {
    const retry = page.getByRole("dialog").getByRole("button", { name: "Verificar mesma disponibilidade", exact: true });
    await expect(retry).toBeEnabled(); failRead = false; await retry.click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(attempts).toHaveLength(2); expect(attempts[1]).toEqual(attempts[0]);
  }
});

for (const change of ["version", "inactive", "removed"]) test(`Bar availability blocks changed selection ${change}`, async ({ page }) => {
  const catalog = await setup(page); let sends = 0;
  await page.route("**/api/pos/catalog/products/*/availability/", route => { sends++; return route.fulfill({ status: 500, json: {} }); });
  await page.goto("/bar"); await chooseBarAvailability(page, "Bebida de teste");
  if (change === "version") catalog[0].availability_version++;
  else if (change === "inactive") catalog[0].active = false;
  else catalog.splice(0, 1);
  await page.evaluate(() => window.dispatchEvent(new Event("online")));
  await expect(page.getByRole("dialog").getByText("O produto mudou. Volte e escolha o item novamente.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sim, indisponibilizar", exact: true })).toBeDisabled();
  expect(sends).toBe(0);
});
