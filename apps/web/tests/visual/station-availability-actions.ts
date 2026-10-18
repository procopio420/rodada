import { expect, type Page } from "@playwright/test";

export async function chooseBarAvailability(page: Page, name: string, reactivate = false) {
  await page.getByRole("button", { name: reactivate ? "Reativar item" : "Indisponibilizar item", exact: true }).click();
  await page.getByRole("navigation", { name: "Categorias da disponibilidade" }).getByRole("button", { name: /^Todos/ }).click();
  await page.getByRole("button", { name: `${reactivate ? "Reativar" : "Indisponibilizar"} ${name}`, exact: true }).click();
  return page.getByRole("dialog");
}

export async function closeBarAvailability(page: Page) {
  for (let i = 0; i < 3 && await page.getByRole("dialog").isVisible(); i++) {
    await page.getByRole("dialog").getByRole("button", { name: "Voltar", exact: true }).click();
  }
  await expect(page.getByRole("dialog")).not.toBeVisible();
}

export async function expectBarAvailabilityBlocked(page: Page, name: string) {
  await page.getByRole("button", { name: "Indisponibilizar item", exact: true }).click();
  await page.getByRole("navigation", { name: "Categorias da disponibilidade" }).getByRole("button", { name: /^Todos/ }).click();
  await expect(page.getByRole("button", { name: `Indisponibilizar ${name}`, exact: true })).toBeDisabled();
  await closeBarAvailability(page);
}
