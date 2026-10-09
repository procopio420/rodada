import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) {
  test(`Atendimento browser operations without payments at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await fixture(page, "normal", true);
    await page.goto("/attendance");
    await expect(page.getByRole("heading", { name: "Entregas prontas" })).toBeVisible();
    await expect(page.getByText("Teste sem pagamentos.", { exact: false })).toBeVisible();
    await stable(page); await layoutAndA11y(page);
    await page.getByRole("button", { name: "Contas", exact: true }).click();
    await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
    await expect(page.getByRole("button", { name: /Fritas/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "Receber em dinheiro" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /Estornos|Abrir caixa/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Fechar comanda", exact: true })).toBeDisabled();
    await layoutAndA11y(page);
    await page.getByRole("button", { name: "Mesas", exact: true }).click();
    await expect(page.getByRole("button", { name: "Liberar mesa 24" })).toBeVisible();
    await layoutAndA11y(page);
  });
}
test("Atendimento manifest and financial gateway exclusion", async ({ request }) => {
  const manifest = await request.get("/attendance/manifest.webmanifest");
  expect(await manifest.json()).toMatchObject({ name: "Rodada Atendimento", start_url: "/attendance", display: "standalone" });
  for (const route of ["tabs/test/payments", "tabs/test/payments/integrated", "payments/capabilities", "refunds", "cash/points"]) {
    const result = await request.post(`/api/attendance/${route}/`, { data: {} });
    expect(result.status()).toBe(403);
    expect((await result.json()).code).toBe("ATTENDANCE_OPERATION_DISABLED");
  }
});

test("ambiguous order retry preserves payload after catalog changes", async ({ page }) => {
  await fixture(page, "normal", true);
  const attempts: unknown[] = [];
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", async route => {
    attempts.push(route.request().postDataJSON());
    await route.fulfill({ status: attempts.length === 1 ? 503 : 200, json: attempts.length === 1 ? { code: "TEMPORARY", message: "Resultado ainda não confirmado." } : { id: "same-order" } });
  });
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Contas", exact: true }).click();
  await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
  await page.getByRole("button", { name: /Fritas/ }).click();
  await page.getByLabel("Quantidade de Fritas").fill("2");
  await layoutAndA11y(page);
  await page.getByRole("button", { name: /Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeVisible();
  await expect(page.getByLabel("Quantidade de Fritas")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Abrir", exact: true })).toBeDisabled();
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [] } }));
  await page.clock.runFor(15000);
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
});

test("Atendimento hostname selects the dedicated browser entry", async ({ request }) => {
  const response = await request.get("/", { headers: { host: "atendimento.rodada.ai" } });
  expect(response.ok()).toBeTruthy();
  expect(await response.text()).toContain("Rodada Atendimento");
  const manifest = await request.get("/manifest.webmanifest", { headers: { host: "atendimento.rodada.ai" } });
  expect(await manifest.json()).toMatchObject({ name: "Rodada Atendimento", start_url: "/attendance" });
});
