import { expect, test, type Page } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

function database(code: string) {
  return execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os,json
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.catalog.models import Product
from modules.ordering.models import OrderItem
from modules.ledger.models import Charge,Payment
from modules.venue.models import Venue
v=Venue.objects.get(slug='web-e2e')
${code}`], { cwd: resolve("../api"), env: process.env }).toString().trim();
}
async function api(page: Page, path: string, body?: unknown) {
  return page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const result = await response.json(); if (!response.ok) throw new Error(JSON.stringify(result)); return result;
  }, { path, body });
}
for (const width of [360, 390, 430]) test(`Real POS repeated round current price new intent and lost-response replay at ${width}`, async ({ page }) => {
  test.setTimeout(90000);
  database("Product.objects.filter(venue=v,name='Kitchen E2E item').update(price_cents=1000)");
  await page.setViewportSize({ width, height: 900 }); await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468"); await page.getByRole("button", { name: "Entrar", exact: true }).click();

  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible(); await page.goto("/pos"); const catalog = (await api(page, "catalog/products/")).results;
  const product = catalog.find((p: { name: string }) => p.name === "Kitchen E2E item");
  const tab = await api(page, "tabs/", { display_label: `POS Repeat ${width}` });
  const other = await api(page, "tabs/", { display_label: `POS Other ${width}` });
  const original = await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: `historical-${width}`, lines: [{ product_id: product.id, quantity: 1, special_instructions: "Sem sal" }] });
  database("Product.objects.filter(venue=v,name='Kitchen E2E item').update(price_cents=1200)");
  await page.reload();
  await page.getByRole("button", { name: new RegExp(`^POS Other ${width} ·`) }).click();
   await page.getByRole("button", { name: /^Bar E2E item/ }).click();
  await page.getByRole("button", { name: new RegExp(`^POS Repeat ${width} ·`) }).click();
   await page.getByRole("button", { name: /^Bar E2E item/ }).click();
  const draft = page.getByRole("region", { name: "Pedido atual" });
  const repeat = page.getByRole("button", { name: "Repetir rodada 1", exact: true }); await repeat.click();
  const dialog = page.getByRole("dialog", { name: "Conferir rodada" });
  await expect(dialog.getByText(/^Anterior:/)).toContainText("10,00"); await expect(dialog.getByText(/^Atual:/)).toContainText("12,00");
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click(); await expect(draft.locator(".dataRow")).toHaveCount(1);
  await repeat.click();
  const add = dialog.getByRole("button", { name: "Adicionar ao carrinho" });
  await dialog.getByRole("checkbox").uncheck(); await expect(add).toBeDisabled();
  await dialog.getByRole("checkbox").check();
  await dialog.getByRole("spinbutton", { name: "Quantidade de Kitchen E2E item" }).fill("1");
  await add.dblclick();
  await expect(draft.locator(".dataRow")).toHaveCount(2);
  const beforeSend = await api(page, `tabs/${tab.id}/`); expect(beforeSend.orders).toHaveLength(1); expect(beforeSend.exposure_cents).toBe(1000);
  const attempts: string[] = []; let newOrderId = "";
  const endpoint = `**/api/pos/tabs/${tab.id}/orders/confirm/`;
  await page.route(endpoint, async route => {
    attempts.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(attempts.length === 1 ? 201 : 200);
    const body = await response.json(); if (!newOrderId) newOrderId = body.id; else expect(body.id).toBe(newOrderId);
    if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await draft.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled(); await expect(repeat).toBeDisabled();
  expect(JSON.parse(attempts[0]).idempotency_key).not.toBe(`historical-${width}`);
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).dblclick();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(attempts).toHaveLength(2); expect(attempts[1]).toBe(attempts[0]); expect(newOrderId).not.toBe(original.id);
  const after = await api(page, `tabs/${tab.id}/`); expect(after.orders).toHaveLength(2); expect(after.exposure_cents).toBe(2700);
  expect(after.payments).toEqual(beforeSend.payments);
  expect(after.orders.find((o: { id: string }) => o.id === original.id)).toEqual(beforeSend.orders[0]);
  expect(database(`print(Charge.objects.filter(tab_id='${tab.id}').count())`)).toBe("3");
  const snapshot = JSON.parse(database(`item=OrderItem.objects.get(pk='${original.items[0].id}'); print(json.dumps({'cents':item.unit_price_cents,'snapshot':item.customization_snapshot}))`));
  expect(snapshot.cents).toBe(1000); expect(snapshot.snapshot).toEqual(original.items[0].customization_snapshot);
  await page.getByRole("button", { name: new RegExp(`^POS Other ${width} ·`) }).click();
  await expect(draft.getByText("1× Bar E2E item", { exact: true })).toBeVisible();
  const untouched = await api(page, `tabs/${other.id}/`); expect(untouched.orders).toHaveLength(0); expect(untouched.exposure_cents).toBe(0);
  await page.screenshot({ path: `test-results/pos-repeat-order-real-${width}.png`, fullPage: true });
  await page.unroute(endpoint);
});
