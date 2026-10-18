import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
import { openAttendanceTab } from "./attendance-actions";
import { addCatalogItem, openProductCategory } from "./category-actions";
for (const width of [360, 390, 430]) test(`Attendance categories and compact bill at ${width}`, async ({ page }) => {
  await fixture(page, "normal", true);
  await page.setViewportSize({ width, height: 900 });
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [
    { id: "beer", name: "Amstel Long Neck", category: "Cervejas", price_cents: 1000, active: true, availability: "AVAILABLE" },
    { id: "cola", name: "Coca-Cola Lata", category: "Bebidas", price_cents: 600, active: true, availability: "AVAILABLE" },
    { id: "cold", name: "Tábua de Frios", category: "Pratos", price_cents: 4000, active: true, availability: "UNAVAILABLE" },
    { id: "hidden", name: "Retirado", category: "Cervejas", price_cents: 1, active: false, availability: "AVAILABLE" },
    { id: "other", name: "Item sem categoria", price_cents: 300, active: true, availability: "AVAILABLE" },
    { id: "brahma", name: "Brahma 600 ml", price_cents: 1200, active: true, availability: "AVAILABLE" },
  ] } }));
  await page.goto("/attendance");
  await openAttendanceTab(page);
  const workspace = page.locator(".attendanceOrderDialog");
  await workspace.getByRole("button", { name: "Conta", exact: true }).click();
  const bill = workspace.getByRole("region", { name: "Valores da comanda" });
  await expect(bill.getByText("Subtotal", { exact: true })).toBeVisible();
  await expect(bill.getByText("Subtotal original")).not.toBeVisible();
  await expect(bill.getByText("Descontos")).not.toBeVisible();
  await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 84,00", { exact: true })).toBeVisible();
  await bill.getByText("Mais detalhes", { exact: true }).click();
  await expect(bill.getByText("Descontos")).toBeVisible();
  await expect(bill.getByText("Subtotal original")).toBeVisible();
  await expect(bill.getByText("R$ 72,00", { exact: true })).toBeVisible();
  await workspace.getByRole("button", { name: "Cardápio", exact: true }).click();
  await expect(workspace.getByRole("navigation", { name: "Categorias do cardápio" })).toBeVisible();
  await expect(workspace.getByRole("button", { name: "Escolher Amstel Long Neck", exact: true })).toHaveCount(0);
  await addCatalogItem(page, "Amstel Long Neck");
  const category = await openProductCategory(page, "brahma");
  await expect(category.getByRole("button", { name: "Escolher Brahma 600 ml", exact: true })).toBeVisible();
  await expect(category.getByRole("button", { name: /Coca-Cola Lata/ })).toHaveCount(0);
  await category.locator(":scope > button").last().click();
  await page.getByLabel("Buscar item no cardápio", { exact: true }).fill("tabua");
  await page.getByRole("navigation", { name: "Categorias do cardápio" }).getByRole("button").first().click();
  await expect(category.getByRole("button", { name: "Escolher Tábua de Frios", exact: true })).toBeDisabled();
  await category.locator(":scope > button").last().click();
  await page.getByLabel("Buscar item no cardápio", { exact: true }).fill("inexistente");
  await expect(workspace.getByText("Nenhum item encontrado.")).toBeVisible();
  await page.getByLabel("Buscar item no cardápio", { exact: true }).fill("");
  await page.getByRole("navigation", { name: "Categorias do cardápio" }).getByRole("button", { name: /^Todos/ }).click();
  await expect(category.getByRole("button", { name: /^Escolher / })).toHaveCount(5);
  await expect(category.getByRole("button", { name: /Retirado/ })).toHaveCount(0);
  await expect(category.getByRole("button", { name: "Escolher Tábua de Frios", exact: true })).toBeDisabled();
  await expect(category.getByRole("button", { name: "Escolher Item sem categoria", exact: true })).toBeVisible();
  for (const [index, name] of ["Amstel Long Neck", "Brahma 600 ml", "Coca-Cola Lata", "Tábua de Frios", "Item sem categoria"].entries()) {
    await expect(category.getByRole("button", { name: /^Escolher / }).nth(index)).toContainText(name);
  }
  await layoutAndA11y(page);
  await category.getByRole("button", { name: "Ver pedido atual · 1 itens", exact: true }).click();
  await expect(workspace.getByText("1× Amstel Long Neck", { exact: true })).toBeVisible();
  await expect(workspace.getByRole("button", { name: /Confirmar pedido/ })).toBeEnabled();
  await layoutAndA11y(page);
});


test("virtual Todos remains separate from a real Todos category and respects search", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [
    { id: "real", name: "Item da categoria Todos", category: "Todos", price_cents: 500, active: true, availability: "AVAILABLE" },
    { id: "other", name: "Item de bebidas", category: "Bebidas", price_cents: 700, active: true, availability: "UNAVAILABLE" },
    { id: "inactive", name: "Item inativo", category: "Todos", price_cents: 1, active: false, availability: "AVAILABLE" },
  ] } }));
  await page.goto("/attendance"); await openAttendanceTab(page);
  const nav = page.getByRole("navigation", { name: "Categorias do cardápio" });
  await expect(nav.getByRole("button").first()).toHaveText("Todos2 itens");
  await nav.getByRole("button").filter({ hasText: /^Todos1 itens$/ }).click();
  const category = page.locator(".attendanceCategoryDialog");
  await expect(category.getByRole("button", { name: /^Escolher / })).toHaveCount(1);
  await category.locator(":scope > button").last().click();
  await nav.getByRole("button").first().click();
  await expect(category.getByRole("button", { name: /^Escolher / })).toHaveCount(2);
  await expect(category.getByRole("button", { name: "Escolher Item de bebidas", exact: true })).toBeDisabled();
  await category.locator(":scope > button").last().click();
  await page.getByLabel("Buscar item no cardápio", { exact: true }).fill("bebidas");
  await expect(nav.getByRole("button").first()).toHaveText("Todos1 itens");
  await nav.getByRole("button").first().click();
  await expect(category.getByRole("button", { name: /^Escolher / })).toHaveCount(1);
});
