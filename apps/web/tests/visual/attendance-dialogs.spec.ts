import { chooseCatalogItem } from "./category-actions";
import { openOtherTabs } from "./attendance-actions";
import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const width of [360, 390, 430]) test(`Attendance table dialogs at ${width}`, async ({ page }) => {
 await page.setViewportSize({ width, height: 844 });
 await fixture(page, "normal", true);
 let releases = 0;
 await page.route("**/api/attendance/hospitality/tables/table-test/release/", route => { releases++; return route.fulfill({ status: 409, json: { code: "CONFLICT", message: "Atualize a mesa antes de continuar." } }); });
 await page.goto("/attendance");
 await page.getByRole("button", { name: "Mesas e comandas", exact: true }).click();
 await expect(page.getByLabel("Localização da mesa 24")).toHaveCount(0);
 await page.getByRole("button", { name: /Mesa 24 Ocupada/ }).click();
 await page.getByRole("button", { name: "Organizar mesa 24" }).click();
 await expect(page.getByRole("dialog", { name: "Organizar mesa 24" })).toBeVisible();
 await layoutAndA11y(page);
 await page.keyboard.press("Escape");
 await expect(page.getByRole("button", { name: "Organizar mesa 24" })).toBeFocused();
 await page.getByRole("button", { name: "Liberar mesa 24", exact: true }).click();
 expect(releases).toBe(0);
 const dialog = page.getByRole("dialog", { name: "Liberar mesa 24?" });
 await expect(dialog).toContainText("As comandas permanecem abertas");
 await dialog.getByRole("button", { name: "Confirmar liberação" }).click();
 await expect(dialog.getByRole("alert")).toContainText("Atualize a mesa");
 expect(releases).toBe(1);
 await layoutAndA11y(page);
});

test("Attendance close dialog requires explicit confirmation", async ({ page }) => {
 await fixture(page, "normal", true);
 let writes = 0;
 await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ json: { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 0, payable_cents: 0, orders: [] } }));
 await page.route("**/api/attendance/tabs/tab-test/close/", route => { writes++; return route.fulfill({ status: 409, json: { code: "CONFLICT", message: "Confira o estado atualizado." } }); });
 await page.goto("/attendance");
 await openOtherTabs(page);
 await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
 await page.locator(".attendanceOrderDialog").getByRole("button", { name: "Conta", exact: true }).click();
 await page.getByRole("button", { name: "Fechar comanda", exact: true }).click();
 expect(writes).toBe(0);
 const dialog = page.getByRole("dialog", { name: "Fechar comanda?" });
 await layoutAndA11y(page);
 await dialog.getByRole("button", { name: "Confirmar fechamento" }).click();
 await expect(dialog.getByRole("alert")).toContainText("Confira o estado atualizado");
 expect(writes).toBe(1);
});


test("Escape dismisses only the top catalog layer and restores focus", async ({ page }) => {
 await fixture(page, "normal", true);
 await page.goto("/attendance"); await openOtherTabs(page);
 await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
 const workspace = page.locator(".attendanceOrderDialog");
 const item = await chooseCatalogItem(page, "Fritas");
 const category = page.locator(".attendanceCategoryDialog");
 await page.keyboard.press("Escape");
 await expect(item).not.toBeVisible(); await expect(category).toBeVisible(); await expect(workspace).toBeVisible();
 await expect(category.getByRole("button", { name: "Escolher Fritas", exact: true })).toBeFocused();
 await page.keyboard.press("Escape");
 await expect(category).not.toBeVisible(); await expect(workspace).toBeVisible();
 await page.keyboard.press("Escape"); await expect(workspace).not.toBeVisible();
 await expect(page.getByRole("button", { name: /Comanda de teste ·/ })).toBeFocused();
});
