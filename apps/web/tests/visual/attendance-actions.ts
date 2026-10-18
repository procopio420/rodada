import { expect, type Page } from "@playwright/test";

export async function openOtherTabs(page: Page) {
  const details = page.getByRole("region", { name: "Outras comandas" }).locator("details");
  await expect(details).toBeVisible();
  if (await details.getAttribute("open") === null) await details.locator("summary").click();
}

export async function openAttendanceTab(page: Page, id = "tab-test") {
  await openOtherTabs(page);
  await page.locator(`button[data-tab-id="${id}"]`).click();
  await expect(page.locator(".attendanceOrderDialog")).toBeVisible();
}

export async function closeAttendanceTab(page: Page) {
  const workspace = page.locator(".attendanceOrderDialog");
  if (await workspace.isVisible()) {
    await workspace.locator(":scope > button").last().click();
    await expect(workspace).not.toBeVisible();
  }
}

export async function selectAttendanceTab(page: Page, name: RegExp) {
  await closeAttendanceTab(page);
  await openOtherTabs(page);
  await page.getByRole("button", { name }).click();
  await expect(page.locator(".attendanceOrderDialog")).toBeVisible();
}

export async function attendanceDraft(page: Page) {
  await page.locator(".attendanceOrderDialog").getByRole("button", { name: /^Pedido atual/ }).click();
  return page.getByRole("region", { name: "Pedido atual" });
}
