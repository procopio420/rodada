import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const width of [360, 390, 430]) test(`Attendance history is separate and read-only at ${width}`, async ({ page }) => {
 await fixture(page, "normal", true);
 await page.setViewportSize({ width, height: 900 });
 const closed = { id: "closed-tab", display_label: "Comanda encerrada", state: "CLOSED", exposure_cents: 0, payable_cents: 1200, original_subtotal_cents: 1200, payments_cents: 1200, orders: [] };
 await page.route("**/api/attendance/tabs/", route => route.fulfill({ json: { results: [closed] } }));
 await page.route("**/api/attendance/tabs/closed-tab/", route => route.fulfill({ json: closed }));
 const task = { id: "history-origin-task", task_type: "SERVICE_REQUEST", state: "OPEN", destination_label: "Mesa 24", claimed_by_id: null,
  target_version: 1, target: { kind: "TABLE", tab_id: null, table_id: "table-test", occupancy_id: "occupancy-test", generation: 1 } };
 await page.route("**/api/attendance/dispatch/requests/", route => route.fulfill({ json: { results: [task] } }));
 await page.route("**/api/attendance/dispatch/tasks/history-origin-task/", route => route.fulfill({ json: task }));
 await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { results: [{ id: "table-test", label: "24", status: "OCCUPIED", active_occupancy: { id: "occupancy-test", generation: 1, tabs: [] } }] } }));
 const writes: string[] = [];
 page.on("request", request => { if (request.method() !== "GET") writes.push(request.url()); });
 await page.goto("/attendance");
 // Establish Agora as the previous contextual origin, then enter history from Mesas.
 await page.getByRole("button", { name: /Mesa 24.*Escolher comanda/ }).click();
 await expect(page.locator(".ux2TablePage")).toBeVisible();
 await page.locator(".ux2TablePage").getByRole("button", { name: "Voltar", exact: true }).click();
 await page.getByRole("button", { name: "Mesas", exact: true }).click();
 await expect(page.getByRole("button", { name: /Ver histórico de comandas/ })).toHaveCount(0);
 await expect(page.getByRole("button", { name: /Comanda encerrada ·/ })).toHaveCount(0);
 const trigger = page.getByRole("button", { name: "Histórico", exact: true });
 await expect(page.getByRole("heading", { name: "Mesas", exact: true })).toBeVisible();
 await expect(trigger).toHaveText("");

 const target = await trigger.boundingBox();
 expect(target!.width).toBeGreaterThanOrEqual(44);
 expect(target!.height).toBeGreaterThanOrEqual(44);
 await trigger.click();
 const dialog = page.getByRole("dialog", { name: "Histórico de comandas" });
 await expect(dialog).toBeVisible();
 await dialog.getByRole("button", { name: "Comanda encerrada · Comanda CLOSED-T · Encerrada", exact: true }).click();
 await expect(dialog.getByRole("region", { name: "Detalhes da comanda encerrada" })).toBeVisible();
 await expect(dialog.getByRole("button", { name: "Fechar comanda", exact: true })).toHaveCount(0);
 await expect(page.locator(".attendanceSelectedTab")).toHaveCount(0);
 await layoutAndA11y(page);
 await page.screenshot({ path: test.info().outputPath("history-open.png"), fullPage: true });
 await expect(dialog.getByRole("button", { name: "Voltar", exact: true })).toHaveClass(/buttonSecondary dialogReturn/);
 await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
 await expect(dialog).toHaveCount(0);
 await expect(trigger).toBeFocused();
 await expect(page.getByRole("heading", { name: "Mesas", exact: true })).toBeVisible();
 expect(writes).toEqual([]);
 await page.screenshot({ path: test.info().outputPath("history-return.png"), fullPage: true });
});
