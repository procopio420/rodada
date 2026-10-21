import { expect, type Page } from "@playwright/test";

export const attendanceWorkspace = (page: Page) => page.getByRole("region", { name: "Comanda selecionada", exact: true });

export async function openOtherTabs(page: Page) {
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await expect(page.getByRole("region", { name: "Outras comandas", exact: true })).toBeVisible();
}

export async function openAttendanceTab(page: Page, id = "tab-test") {
  await openOtherTabs(page);
  await page.locator(`button[data-tab-id="${id}"]`).click();
  await expect(attendanceWorkspace(page)).toBeVisible();
}

export async function closeAttendanceTab(page: Page) {
  const workspace = attendanceWorkspace(page);
  for (let step = 0; step < 3 && await workspace.isVisible(); step++)
    await workspace.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(workspace).not.toBeVisible();
}

export async function selectAttendanceTab(page: Page, name: RegExp) {
  await closeAttendanceTab(page);
  await openOtherTabs(page);
  await page.getByRole("region", { name: "Outras comandas", exact: true }).getByRole("button", { name }).click();
  await expect(attendanceWorkspace(page)).toBeVisible();
}

export async function attendanceDraft(page: Page) {
  const workspace = attendanceWorkspace(page);
  await expect(workspace).toBeVisible();
  if (await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).isVisible())
    await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  await workspace.getByRole("button", { name: "Ver resumo", exact: true }).click();
  return workspace;
}

export async function openAttendanceTable(page: Page, id: string) {
  const tables = page.getByRole("button", { name: "Mesas", exact: true });
  await tables.click();
  await page.locator(`#attendance-table-${id} button`).click();
  await expect(page.locator(".ux2TablePage")).toBeVisible();
}
