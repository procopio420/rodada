import { expect, test } from "@playwright/test";

for (const width of [360, 390, 430]) test(`Staff order committed without response recovers after reload once ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await page.getByRole("button", { name: "Contas", exact: true }).click();
  const label = `Order recovery ${width}`;
  await page.getByLabel("Apelido da comanda (opcional)").fill(label);
  await page.getByRole("button", { name: "Abrir", exact: true }).click();
  await expect(page.getByRole("heading", { name: label, exact: true })).toBeVisible();
  await page.getByLabel("Buscar item no cardápio").fill("Kitchen E2E item");
  await page.getByRole("button", { name: /^Kitchen E2E item/ }).click();
  await page.getByRole("button", { name: "Aumentar quantidade de Kitchen E2E item", exact: true }).click();
  const attempts: string[] = []; let orderId = "", tabId = "";
  await page.route(/\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/, async route => {
    attempts.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(attempts.length === 1 ? 201 : 200);
    const body = await response.json();
    if (!orderId) { orderId = body.id; tabId = body.tab_id; } else expect(body.id).toBe(orderId);
    if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  await page.reload();
  if (width === 390) await page.goto("/pos");
  const verify = page.getByRole("button", { name: "Verificar mesmo pedido" }); await expect(verify).toBeEnabled();
  expect(attempts).toHaveLength(1);
  await verify.dblclick(); await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(attempts).toHaveLength(2); expect(attempts[1]).toBe(attempts[0]);
  const detail = await page.evaluate(async id => (await fetch(`/api/pos/tabs/${id}/`)).json(), tabId);
  expect(detail.orders).toHaveLength(1); expect(detail.orders[0].id).toBe(orderId);
  expect(detail.orders[0].items[0].quantity).toBe(2); expect(detail.exposure_cents).toBe(2000); expect(detail.payments).toHaveLength(0);
  expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.staff-order.v1"))).toBeNull();
});
