import { expect, type Page } from "@playwright/test";
import { attendanceWorkspace } from "./attendance-actions";

export async function openProductCategory(page: Page, name: string) {
  const workspace = attendanceWorkspace(page);
  if (await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).isVisible())
    await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  else if (await workspace.getByRole("button", { name: "← Continuar escolhendo itens", exact: true }).isVisible())
    await workspace.getByRole("button", { name: "← Continuar escolhendo itens", exact: true }).click();
  await workspace.getByLabel("Buscar produto", { exact: true }).fill(name);
  await workspace.getByRole("group", { name: "Categorias", exact: true }).locator('button[data-category=""]').click();
  return workspace;
}
export async function chooseCatalogItem(page: Page, name: string) {
  const catalog = await openProductCategory(page, name);
  await catalog.getByRole("button", { name: `Personalizar ${name}`, exact: true }).click();
  const item = page.getByRole("dialog", { name: `Personalizar ${name}`, exact: true });
  await expect(item).toBeVisible();
  return item;
}
export async function addCatalogItem(page: Page, name: string, quantity = 1) {
  const catalog = attendanceWorkspace(page);
  if (!await catalog.getByRole("button", { name: `Adicionar ${name}`, exact: true }).isVisible())
    await openProductCategory(page, name);
  for (let count = 0; count < quantity; count++)
    await catalog.getByRole("button", { name: `Adicionar ${name}`, exact: true }).click();
}
export async function expectCatalogQuantity(page: Page, name: string, quantity: number) {
  const catalog = await openProductCategory(page, name);
  await expect(catalog.getByRole("status", { name: `Quantidade de ${name}`, exact: true })).toHaveText(String(quantity));
}
