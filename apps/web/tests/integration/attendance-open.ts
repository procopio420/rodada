import { expect, type Page } from "./fixtures";

/** Create only disposable web-e2e fixture tables; never touch a shared venue. */
export async function createAttendanceTable(page: Page, label: string) {
  const result = await page.evaluate(async label => {
    const response = await fetch("/api/pos/hospitality/tables/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label }),
    });
    return { status: response.status, body: await response.text() };
  }, label);
  expect(result.status, result.body).toBe(201);
  // Prove the table reached the real Attendance view before using the opening dialog.
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await expect(page.getByRole("button", { name: new RegExp(`Mesa ${label} Disponível`) })).toBeVisible();
}

/** Real attendance flow: named Tab, table-choice dialog, canonical selection. */
export async function openAttendanceTab(page: Page, name: string, tableLabel: string) {
  await page.getByLabel("Nome da Comanda").fill(name);
  await page.getByRole("button", { name: "Abrir comanda", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Qual mesa o cliente está?" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: new RegExp(`^Mesa ${tableLabel}(?: · Em uso)?$`) }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.locator(".attendanceSelectedTab")).toContainText(name);
}
