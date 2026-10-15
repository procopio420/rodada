import { expect, type Page } from "@playwright/test";

export async function openProductCategory(page: Page, name: string) {
  const category = page.locator(".attendanceCategoryDialog");
  if (await category.isVisible()) await category.locator(":scope > button").last().click();
  await page.getByLabel("Buscar item no cardápio", { exact: true }).fill(name);
  await page.getByRole("navigation", { name: "Categorias do cardápio" }).getByRole("button").first().click();
  return category;
}
export async function chooseCatalogItem(page: Page, name: string) {
  const category = await openProductCategory(page, name);
  await category.getByRole("button", { name: `Escolher ${name}`, exact: true }).click();
  const item = page.getByRole("dialog", { name: `Adicionar ${name}`, exact: true });
  await expect(item).toBeVisible();
  return item;
}
export async function addCatalogItem(page: Page, name: string, quantity = 1) {
  const item = await chooseCatalogItem(page, name);
  for (let count = 1; count < quantity; count++) await item.getByRole("button", { name: "Aumentar quantidade escolhida", exact: true }).click();
  await item.getByRole("button", { name: /^Adicionar ·/ }).click();
  await expect(item).not.toBeVisible();
  await page.locator(".attendanceCategoryDialog").locator(":scope > button").last().click();
  await expect(page.locator(".attendanceCategoryDialog")).not.toBeVisible();
  await expect(page.locator(".attendanceOrderDialog").locator(":scope > button").last()).toBeEnabled();
}
export async function expectCatalogQuantity(page: Page, name: string, quantity: number) {
  const category = await openProductCategory(page, name);
  const card = category.getByRole("button", { name: `Escolher ${name}`, exact: true });
  await expect(card).toHaveAttribute("data-selected", quantity ? "true" : "false");
  if (quantity) await expect(card.getByRole("status")).toHaveText(`${quantity} no pedido`);
  await category.locator(":scope > button").last().click();
  await expect(category).not.toBeVisible();
  await expect(page.locator(".attendanceOrderDialog").locator(":scope > button").last()).toBeEnabled();
}
