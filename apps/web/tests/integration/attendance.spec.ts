import { addCatalogItem } from "../visual/category-actions";
import { expect, test } from "./fixtures";
import { openNamedAttendanceTab } from "./attendance-helpers";

test("real Atendimento login, order, production, table lifecycle and logout without payments", async ({ page }) => {
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await page.getByRole("button", { name: "Agora", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Entregas prontas" })).toBeVisible();
  await openNamedAttendanceTab(page, "Atendimento browser test");
  await expect(page.locator(".attendanceOrderDialog")).toContainText("Mesa Fixture Atendimento browser test");
  await addCatalogItem(page, "Kitchen E2E item");
  await page.locator(".attendanceOrderDialog").getByRole("button", { name: /Pedido atual/ }).click();
  await page.getByRole("button", { name: "Aumentar quantidade de Kitchen E2E item", exact: true }).click();
  await page.getByRole("button", { name: /Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: /Confirmar pedido/ })).toBeDisabled();
  await page.locator(".attendanceOrderDialog").getByRole("button", { name: "Conta", exact: true }).click();
  await expect(page.getByRole("region", { name: "Rodada 1", exact: true }).getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();
  const browserRequest = {
    get: (path: string) => call(path),
    post: (path: string, options: { data: unknown }) => call(path, options.data),
  };
  async function call(path: string, data?: unknown) {
    const result = await page.evaluate(async ({ path, data }) => {
      const response = await fetch(path, { method: data === undefined ? "GET" : "POST", headers: { "Content-Type": "application/json" }, body: data === undefined ? undefined : JSON.stringify(data) });
      return { status: response.status, body: await response.json() };
    }, { path, data });
    return { ok: () => result.status < 300, status: () => result.status, json: async () => result.body };
  }
  const tabs = await (await browserRequest.get("/api/attendance/tabs/")).json();
  const tab = tabs.results.find((item: { display_label: string }) => item.display_label === "Atendimento browser test");
  const detail = await (await browserRequest.get(`/api/attendance/tabs/${tab.id}/`)).json();
  expect(detail.orders).toHaveLength(1); expect(detail.orders[0].items[0].quantity).toBe(2);
  expect(detail.exposure_cents).toBe(2000); expect(detail.payments_cents).toBe(0);
  expect((await browserRequest.post(`/api/attendance/tabs/${tab.id}/payments/`, { data: { amount_cents: 2000, method: "CASH" } })).status()).toBe(403);
  expect((await browserRequest.post(`/api/attendance/tabs/${tab.id}/close/`, { data: {} })).status()).toBeGreaterThanOrEqual(400);
  for (const state of ["ACCEPTED", "PREPARING", "READY"]) {
    const r = await browserRequest.post(`/api/pos/order-items/${detail.orders[0].items[0].id}/transition/`, { data: { state } });
    expect(r.ok()).toBeTruthy();
  }
  await page.locator(".attendanceOrderDialog").getByRole("button", { name: "Voltar", exact: true }).click();
  await page.locator(".attendanceTableDialog").getByRole("button", { name: "Voltar", exact: true }).click();
  await page.getByRole("button", { name: "Agora", exact: true }).click();
  await expect(page.getByRole("button", { name: "Concluir entrega" })).toBeVisible();
  await page.getByRole("button", { name: "Concluir entrega" }).click();
  await expect(page.getByRole("button", { name: "Concluir entrega" })).toHaveCount(0);
  const tableResult = await browserRequest.post("/api/pos/hospitality/tables/", { data: { label: "Attendance test", guest_ordering_mode: "DIRECT" } });
  expect(tableResult.ok()).toBeTruthy();
  await browserRequest.post(`/api/pos/hospitality/tables/${tableResult.ok() ? (await tableResult.json()).id : ""}/occupy/`, { data: {} });
  await page.getByRole("button", { name: "Mesas e comandas", exact: true }).click();
  await page.getByRole("button", { name: /^Mesa Attendance test/ }).click();
  await page.getByRole("button", { name: "Organizar mesa Attendance test" }).click();
  await page.getByLabel("Associar comanda à mesa Attendance test").selectOption(tab.id);
  await page.getByRole("dialog", { name: "Mover comanda?" }).getByRole("button", { name: "Confirmar mudança de mesa" }).click();
  await expect(page.getByRole("button", { name: /Atendimento browser test · Comanda/ }).last()).toBeVisible();
  await page.getByRole("button", { name: "Liberar mesa Attendance test" }).click();
  await page.getByRole("button", { name: "Confirmar liberação" }).click();
  await expect(page.locator(".attendanceTableDialog")).not.toBeVisible();
  await page.getByRole("button", { name: /^Mesa Attendance test Aguardando limpeza/ }).click();
  await expect(page.getByRole("button", { name: "Iniciar limpeza" })).toHaveCount(0);
  await page.getByRole("button", { name: "Concluir limpeza" }).click();
  await expect(page.locator(".attendanceTableDialog")).not.toBeVisible();
  await expect(page.getByRole("button", { name: /^Mesa Attendance test Disponível/ })).toBeVisible();
  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page.getByRole("button", { name: "Entrar", exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});
