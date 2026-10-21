import { chooseCatalogItem } from "./category-actions";
import { openAttendanceTab } from "./attendance-actions";
import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const width of [360, 390, 430]) test(`Attendance table dialogs at ${width}`, async ({ page }) => {
 await page.setViewportSize({ width, height: 844 });
 await fixture(page, "normal", true);
 let releases = 0;
 await page.route("**/api/attendance/hospitality/tables/table-test/release/", route => { releases++; return route.fulfill({ status: 409, json: { code: "CONFLICT", message: "Atualize a mesa antes de continuar." } }); });
 await page.goto("/attendance");
 await page.getByRole("button", { name: "Mesas", exact: true }).click();
 await expect(page.getByLabel("Localização da mesa 24")).toHaveCount(0);
 await page.getByRole("button", { name: /Mesa 24 Ocupada/ }).click();
 await page.getByText("Opções da mesa", { exact: true }).click();
 await page.getByRole("button", { name: "Organizar mesa 24" }).click();
 await expect(page.getByRole("dialog", { name: "Organizar mesa 24" })).toBeVisible();
 await layoutAndA11y(page);
 await page.keyboard.press("Escape");
 await expect(page.getByRole("button", { name: "Organizar mesa 24" })).toBeFocused();
 await page.getByRole("button", { name: "Grupo saiu · Liberar mesa", exact: true }).click();
 expect(releases).toBe(0);
 const dialog = page.getByRole("dialog", { name: "Liberar mesa 24?" });
 await expect(dialog).toContainText("A mesa passará para Aguardando limpeza");
 await dialog.getByRole("button", { name: "Confirmar liberação" }).click();
 await expect(dialog.getByRole("alert")).toContainText("Atualize a mesa");
 expect(releases).toBe(1);
 await layoutAndA11y(page);
});

test("Zero balance closes directly and surfaces canonical conflict", async ({ page }) => {
 await fixture(page, "normal", true);
 let writes = 0;
 await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ json: { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 0, payable_cents: 0, orders: [] } }));
 await page.route("**/api/attendance/tabs/tab-test/close/", route => { writes++; return route.fulfill({ status: 409, json: { code: "CONFLICT", message: "Confira o estado atualizado." } }); });
 await page.goto("/attendance"); await openAttendanceTab(page);
 await page.getByRole("button", { name: "Conferir / fechar conta", exact: true }).click();
 await page.getByRole("button", { name: "Encerrar comanda", exact: true }).click();
 await expect(page.getByRole("dialog", { name: "Fechar comanda?", exact: true })).toHaveCount(0);
 await expect(page.getByRole("region", { name: "Comanda selecionada", exact: true }).getByRole("alert")).toContainText("Confira o estado atualizado");
 expect(writes).toBe(1);
 await layoutAndA11y(page);
});


test("Escape dismisses personalization and restores its trigger", async ({ page }) => {
 await fixture(page, "normal", true);
 await page.goto("/attendance"); await openAttendanceTab(page);
 const item = await chooseCatalogItem(page, "Fritas");
 await page.keyboard.press("Escape");
 await expect(item).not.toBeVisible();
 const workspace = page.getByRole("region", { name: "Comanda selecionada", exact: true });
 await expect(workspace).toBeVisible();
 await expect(workspace.getByRole("button", { name: "Personalizar Fritas", exact: true })).toBeFocused();
 await workspace.getByRole("button", { name: "Voltar", exact: true }).click();
 await expect(workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true })).toBeVisible();
});

test("each personalization entry restores its own catalog or draft trigger", async ({ page }) => {
 await fixture(page, "normal", true);
 await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: ["A", "B"].map(id => ({
  id, name: `Produto ${id}`, price_cents: 100, active: true, availability: "AVAILABLE",
  variants: [{ id: `variant-${id}`, name: "Padrão", price_cents: 100, active: true, availability: "AVAILABLE", is_default: true, version: 1 }],
 })) } }));
 await page.goto("/attendance"); await openAttendanceTab(page);
 const workspace = page.getByRole("region", { name: "Comanda selecionada", exact: true });
 await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
 await workspace.getByRole("button", { name: "Personalizar Produto A", exact: true }).click();
 await page.keyboard.press("Escape");
 await expect(workspace.getByRole("button", { name: "Personalizar Produto A", exact: true })).toBeFocused();
 const plus = workspace.getByRole("button", { name: "Adicionar Produto B", exact: true });
 await plus.click();
 const dialog = page.getByRole("dialog", { name: "Personalizar Produto B", exact: true });
 await expect(dialog).toBeVisible(); await page.keyboard.press("Escape");
 await expect(plus).toBeFocused();
 await plus.click(); await dialog.getByRole("button", { name: /^Adicionar ·/ }).click();
 await workspace.getByRole("button", { name: "Ver resumo", exact: true }).click();
 const edit = workspace.getByRole("button", { name: "Editar", exact: true });
 await edit.click(); await expect(dialog).toBeVisible(); await page.keyboard.press("Escape");
 await expect(edit).toBeFocused();
 await expect(workspace.getByText("1× Produto B", { exact: true })).toBeVisible();
});
