import { test, expect, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const products = [
  { id: "drink", name: "Bebida do catálogo", category: "Bebidas", normalized_name: "bebida do catalogo", price_cents: 1200, fulfillment_station: "BAR", availability: "AVAILABLE", active: true },
  { id: "food", name: "Porção do catálogo", category: "Porções", normalized_name: "porcao do catalogo", price_cents: 2400, fulfillment_station: "KITCHEN", availability: "UNAVAILABLE", active: true },
];
async function setup(page: Page, capabilities = ["catalog.icon.manage", "catalog.product.create"]) {
  await fixture(page);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { capabilities } }));
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: products } }));
}

for (const width of [360, 390, 430, 1280]) test(`management catalog category picker ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await setup(page);
  const writes: string[] = [];
  page.on("request", request => { if (["POST", "PATCH", "PUT"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/manage/products");
  await expect(page.getByRole("button", { name: "Adicionar produto", exact: true })).toHaveCount(1);
  await expect(page.getByRole("button", { name: "+ Item", exact: true })).toHaveCount(0);
  const edit = page.getByRole("button", { name: "Editar produto e ícone", exact: true });
  await edit.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("button", { name: /Todos/ })).toBeVisible();
  const allTile = await dialog.getByRole("button", { name: /Todos/ }).boundingBox();
  const categoryTile = await dialog.getByRole("button", { name: /Bebidas/ }).boundingBox();
  expect(categoryTile!.y).toBe(allTile!.y);
  expect(categoryTile!.x).toBeGreaterThan(allTile!.x);
  await layoutAndA11y(page);
  await stable(page);
  await page.screenshot({ path: `../../visual-artifacts/catalog-editor/categories-${width}.png`, fullPage: true });
  await dialog.getByRole("button", { name: /Bebidas/ }).click();
  await expect(dialog.getByRole("button", { name: "Editar Porção do catálogo" })).toHaveCount(0);
  await dialog.getByRole("button", { name: "Editar Bebida do catálogo", exact: true }).click();
  await expect(dialog.getByLabel("Nome do produto")).toHaveValue("Bebida do catálogo");
  await expect(dialog.getByLabel("Nome do produto")).toBeFocused();
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/catalog-editor/item-${width}.png`, fullPage: true });
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "Editar Bebida do catálogo" })).toBeFocused();
  await page.keyboard.press("Escape");
  await dialog.getByRole("button", { name: /Todos/ }).click();
  await expect(dialog.getByRole("button", { name: /^Editar / })).toHaveCount(2);
  await page.screenshot({ path: `../../visual-artifacts/catalog-editor/products-${width}.png`, fullPage: true });
  await dialog.getByRole("button", { name: "Editar Porção do catálogo" }).click();
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "Editar Porção do catálogo" })).toBeFocused();
  await page.keyboard.press("Escape");
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(edit).toBeFocused();
  expect(writes).toEqual([]);
});

test("catalog edit preserves typed name during polling and saves selected item", async ({ page }) => {
  await setup(page);
  let catalog = products;
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: catalog } }));
  const payloads: unknown[] = [];
  let release: (() => void) | undefined;
  await page.route("**/api/pos/catalog/products/food/", async route => {
    payloads.push(route.request().postDataJSON());
    await new Promise<void>(resolve => { release = resolve; });
    catalog = products.map(item => item.id === "food" ? { ...item, name: "Porção revisada" } : item);
    await route.fulfill({ json: catalog[1] });
  });
  await page.goto("/manage/products");
  await page.getByRole("button", { name: "Editar produto e ícone" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Buscar produto").fill("porcao");
  await dialog.getByRole("button", { name: /Porções/ }).click();
  await dialog.getByRole("button", { name: "Editar Porção do catálogo" }).click();
  await dialog.getByLabel("Nome do produto").fill("Porção revisada");
  await page.clock.runFor(5100);
  await expect(dialog.getByLabel("Nome do produto")).toHaveValue("Porção revisada");
  await dialog.getByRole("button", { name: "Salvar nome" }).click();
  await expect(dialog.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
  await expect.poll(() => payloads.length).toBe(1);
  release?.();
  await expect(dialog.getByRole("heading", { name: "Editar Porção revisada" })).toBeVisible();
  expect(payloads).toEqual([{ name: "Porção revisada" }]);
});

for (const capabilities of [["catalog.icon.manage", "catalog.product.create"], ["catalog.icon.manage", "catalog.create.kitchen"]]) test(`single catalog creation routes authorized station ${capabilities.at(-1)}`, async ({ page }) => {
  await setup(page, capabilities);
  await page.route("**/api/pos/catalog/suggestions/**", route => route.fulfill({ json: { results: [] } }));
  const payloads: { fulfillment_station: string }[] = [];
  await page.route("**/api/pos/catalog/resolve-or-create/", route => {
    const body = route.request().postDataJSON(); payloads.push(body);
    return route.fulfill({ json: { product: { ...products[1], ...body, id: "created" }, created: true } });
  });
  await page.goto("/manage/products");
  await page.getByRole("button", { name: "Adicionar produto" }).click();
  const station = page.getByLabel("Preparar em");
  await expect(station.locator("option")).toHaveCount(capabilities.includes("catalog.product.create") ? 2 : 1);
  await station.selectOption("KITCHEN");
  await page.getByRole("combobox", { name: "Nome do produto" }).fill("Produto novo");
  await page.getByRole("option", { name: "Criar “Produto novo”" }).click();
  await page.getByLabel("Preço (R$)").fill("12,50");
  await page.getByRole("button", { name: "Criar item", exact: true }).click();
  await expect.poll(() => payloads.length).toBe(1);
  expect(payloads[0]).toMatchObject({ fulfillment_station: "KITCHEN", price_cents: 1250 });
});

test("catalog picker font 200 percent, search empty and load retry", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 932 });
  await setup(page);
  let failed = true;
  await page.route("**/api/pos/catalog/products/", route => route.fulfill(failed ? { status: 500, json: { message: "Não foi possível carregar." } } : { json: { results: products } }));
  await page.goto("/manage/products");
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  await page.getByRole("button", { name: "Editar produto e ícone" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("alert")).toBeVisible();
  failed = false;
  await dialog.getByRole("button", { name: "Tentar novamente" }).click();
  await dialog.getByLabel("Buscar produto").fill("inexistente");
  await expect(dialog.getByText("Nenhum produto encontrado.")).toBeVisible();
  await dialog.getByLabel("Buscar produto").fill("");
  await dialog.getByRole("button", { name: /Todos/ }).click();
  await layoutAndA11y(page);
});

test("catalog edit permissions and revoked read do not leave an editor open", async ({ page }) => {
  await setup(page, ["catalog.icon.manage"]);
  let revoked = false;
  await page.route("**/api/pos/catalog/products/", route => route.fulfill(revoked ? { status: 403, json: { message: "Acesso encerrado." } } : { json: { results: products } }));
  await page.goto("/manage/products");
  await expect(page.getByRole("button", { name: "Adicionar produto" })).toHaveCount(0);
  await page.getByRole("button", { name: "Editar produto e ícone" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  revoked = true;
  await page.clock.runFor(5100);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Editar produto e ícone" })).toHaveCount(0);
});

test("icon upload preserves selected target and reports server rejection", async ({ page }) => {
  await setup(page);
  const payloads: { action: string; mime?: string }[] = [];
  await page.route("**/api/pos/catalog/products/drink/icon/", route => {
    payloads.push(route.request().postDataJSON());
    return route.fulfill({ status: 400, json: { code: "INVALID_ICON_IMAGE", message: "Imagem não aceita pelo servidor." } });
  });
  await page.goto("/manage/products");
  await page.getByRole("button", { name: "Editar produto e ícone" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: /Bebidas/ }).click();
  await dialog.getByRole("button", { name: "Editar Bebida do catálogo" }).click();
  await dialog.locator('input[type="file"]').setInputFiles({ name: "oversized.png", mimeType: "image/png", buffer: Buffer.alloc(5 * 1024 * 1024 + 1) });
  await expect(dialog.getByText("Use uma imagem até 5 MB.")).toBeVisible();
  expect(payloads).toHaveLength(0);
  await dialog.locator('input[type="file"]').setInputFiles({ name: "invalid.png", mimeType: "image/png", buffer: Buffer.from("invalid image") });
  await expect(dialog.getByText("Imagem não aceita pelo servidor.")).toBeVisible();
  expect(payloads).toHaveLength(1);
  expect(payloads[0]).toMatchObject({ action: "upload", mime: "image/png" });
  await expect(dialog.getByRole("heading", { name: "Editar Bebida do catálogo" })).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Voltar", exact: true })).toBeEnabled();
});

for (const width of [360, 1280]) test(`large catalog grid preserves tile contents ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await setup(page);
  const catalog = Array.from({ length: 50 }, (_, index) => ({ ...products[0], id: `item-${index}`, name: `Produto de nome longo para conferir o catálogo ${index}` }));
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: catalog } }));
  await page.goto("/manage/products");
  await page.getByRole("button", { name: "Editar produto e ícone" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: /Todos/ }).click();
  const first = dialog.getByRole("button", { name: /^Editar Produto/ }).first();
  const card = (await first.boundingBox())!;
  const name = (await first.locator("strong").boundingBox())!;
  expect(name.y + name.height).toBeLessThanOrEqual(card.y + card.height);
  const last = dialog.getByRole("button", { name: "Editar Produto de nome longo para conferir o catálogo 49", exact: true });
  await last.scrollIntoViewIfNeeded();
  await last.click();
  await expect(dialog.getByLabel("Nome do produto")).toHaveValue(catalog[49].name);
  await layoutAndA11y(page);
});
