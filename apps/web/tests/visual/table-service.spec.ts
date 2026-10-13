import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const width of [360, 390, 430]) test(`table service start/open recovery and contextual selection at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "operator-test", display_name: "Ana" }, venue: { id: "venue-test", name: "Bar" }, session: { id: "session-test" }, capabilities: ["table.manage", "tab.open"] } }));
  let occupied = false;
  let opened = false;
  const starts: unknown[] = [], opens: unknown[] = [];
  const occupancy = () => ({ id: "occupancy-test", generation: 1, responsibility_version: 1, responsible_staff_id: "operator-test", responsible_staff: { id: "operator-test", display_name: "Ana" }, unassigned_service_attention: "NONE", tabs: opened ? [{ id: "tab-test", display_label: "João", display_reference: "Comanda 001", state: "OPEN" }] : [] });
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { results: [{ id: "table-test", label: "12", status: occupied ? "OCCUPIED" : "AVAILABLE", active_occupancy: occupied ? occupancy() : null }] } }));
  await page.route("**/api/attendance/hospitality/tables/table-test/service/start/", route => {
    starts.push(route.request().postDataJSON()); occupied = true;
    if (starts.length === 1) return route.abort();
    return route.fulfill({ json: { table_id: "table-test", active_occupancy: occupancy(), replayed: true } });
  });
  await page.route("**/api/attendance/hospitality/occupancies/occupancy-test/tabs/open/", route => {
    opens.push(route.request().postDataJSON()); opened = true;
    if (opens.length === 1) return route.abort();
    return route.fulfill({ json: { tab_id: "tab-test", table_label: "12", replayed: true } });
  });
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: "Iniciar atendimento · Mesa 12", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesma intenção" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Verificar mesma intenção" })).toBeVisible();
  await page.getByRole("button", { name: "Verificar mesma intenção" }).click();
  await expect(page.getByText("Atendimento: você", { exact: true })).toBeVisible();
  expect(starts).toHaveLength(2); expect(starts[0]).toEqual(starts[1]);
  await page.getByRole("button", { name: "Nova comanda nesta mesa" }).click();
  await page.getByLabel("Nome ou apelido (opcional)").fill("João");
  await page.getByRole("button", { name: "Abrir e pedir" }).click();
  await expect(page.getByRole("button", { name: "Verificar mesma intenção" })).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Verificar mesma intenção" }).click();
  await expect(page.getByText("Mesa 12 · Comanda de teste", { exact: true })).toBeVisible();
  expect(opens).toHaveLength(2); expect(opens[0]).toEqual(opens[1]);
  expect(opens[0]).toMatchObject({ expected_generation: 1, display_label: "João" });
  await layoutAndA11y(page);
});

test("one QR attention per occupancy and explicit claim removes warning", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "operator-test", display_name: "Ana" }, venue: { id: "venue-test", name: "Bar" }, session: { id: "session-test" }, capabilities: ["table.manage", "tab.open"] } }));
  let claimed = false;
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { results: [{ id: "table-test", label: "12", status: "OCCUPIED", active_occupancy: { id: "occupancy-test", generation: 1, tabs: [], responsibility_version: claimed ? 1 : 0, responsible_staff_id: claimed ? "operator-test" : null, responsible_staff: claimed ? { id: "operator-test", display_name: "Ana" } : null, unassigned_service_attention: claimed ? "NONE" : "UNASSIGNED_READY", unassigned_guest_order_count: 2, oldest_unassigned_guest_order_at: "2026-10-08T20:00:00Z" } }] } }));
  await page.route("**/api/attendance/hospitality/occupancies/occupancy-test/responsibility/claim/", route => {
    expect(route.request().postDataJSON()).toMatchObject({ expected_responsibility_version: 0, mode: "CLAIM_UNASSIGNED" });
    claimed = true; return route.fulfill({ json: { replayed: false } });
  });
  await page.goto("/attendance");
  await expect(page.getByText("Pedido via QR · Sem responsável", { exact: true })).toHaveCount(1);
  await expect(page.getByText(/Pedido pronto ·/)).toBeVisible();
  await page.getByRole("button", { name: "Assumir atendimento", exact: true }).click();
  await expect(page.getByText("Pedido via QR · Sem responsável", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await expect(page.getByText("Atendimento: você", { exact: true })).toBeVisible();
  await layoutAndA11y(page);
});
