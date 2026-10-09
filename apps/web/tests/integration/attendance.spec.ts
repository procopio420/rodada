import { expect, test } from "@playwright/test";

test("real Atendimento login, order, production, table lifecycle and logout without payments", async ({ page }) => {
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Entregas prontas" })).toBeVisible();
  await page.getByRole("button", { name: "Contas", exact: true }).click();
  await page.getByLabel("Apelido da comanda (opcional)").fill("Atendimento browser test");
  await page.getByRole("button", { name: "Abrir", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Atendimento browser test", exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Kitchen E2E item/ }).click();
  await page.getByLabel("Quantidade de Kitchen E2E item").fill("2");
  await page.getByRole("button", { name: /Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: /Confirmar pedido/ })).toBeDisabled();
  await expect(page.getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();
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
  await page.getByRole("button", { name: "Agora", exact: true }).click();
  await expect(page.getByRole("button", { name: "Concluir entrega" })).toBeVisible();
  await page.getByRole("button", { name: "Concluir entrega" }).click();
  await expect(page.getByRole("button", { name: "Concluir entrega" })).toHaveCount(0);
  const tableResult = await browserRequest.post("/api/pos/hospitality/tables/", { data: { label: "Attendance test", guest_ordering_mode: "DIRECT" } });
  expect(tableResult.ok()).toBeTruthy();
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: "Ocupar mesa Attendance test" }).click();
  await page.getByLabel("Associar comanda à mesa Attendance test").selectOption(tab.id);
  await expect(page.getByText("Atendimento browser test", { exact: true }).last()).toBeVisible();
  await page.getByRole("button", { name: "Liberar mesa Attendance test" }).click();
  await page.getByRole("button", { name: "Iniciar limpeza" }).click();
  await page.getByRole("button", { name: "Concluir limpeza" }).click();
  await expect(page.getByRole("button", { name: "Ocupar mesa Attendance test" })).toBeVisible();
  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page.getByRole("button", { name: "Entrar", exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});
