import { expect, test } from "./fixtures";
import { openNamedAttendanceTab } from "./attendance-helpers";
import { addCatalogItem } from "../visual/category-actions";
import { mkdir } from "node:fs/promises";
import path from "node:path";

test.skip(process.env.RODADA_E2E_MENU !== "1", "Opt-in canonical CSV import into the disposable E2E Venue only");
for (const width of [360, 390, 430]) test(`canonical photographed menu orders reach BAR and KITCHEN at ${width}`, async ({ page }) => {
  test.setTimeout(90_000);
  await page.setViewportSize({ width, height: 844 });
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await page.getByRole("button", { name: "Agora", exact: true }).click();
  await page.getByRole("button", { name: /^Entregas / }).click();
  await expect(page.getByRole("heading", { name: "Prontos para levar" })).toBeVisible();
  const catalog = await page.evaluate(async () => (await (await fetch("/api/attendance/catalog/products/")).json()).results);
  const imported = catalog.filter((p: { name: string }) => !p.name.endsWith("E2E item"));
  expect(imported).toHaveLength(143);
  expect(imported.filter((p: { fulfillment_station: string }) => p.fulfillment_station === "BAR")).toHaveLength(112);
  expect(imported.filter((p: { fulfillment_station: string }) => p.fulfillment_station === "KITCHEN")).toHaveLength(31);
  const label = `CSV acceptance ${width}`;
  await openNamedAttendanceTab(page, label);
  const workspace = page.getByRole("region", { name: "Comanda selecionada", exact: true });
  for (const name of ["Brahma 600 ml", "Coxinha de Queijo com Alho"]) {
    await workspace.getByLabel("Buscar produto", { exact: true }).fill(name);
    await addCatalogItem(page, name);
  }
  await workspace.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await expect(workspace.getByText("1× Brahma 600 ml", { exact: true })).toBeVisible();
  await expect(workspace.getByText("1× Coxinha de Queijo com Alho", { exact: true })).toBeVisible();
  await workspace.getByRole("button", { name: /^Enviar / }).click();
  await expect(workspace.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  await expect(workspace.locator(".ux2ReviewRow")).toHaveCount(0);
  const detail = await page.evaluate(async label => {
    const tabs = (await (await fetch("/api/attendance/tabs/")).json()).results;
    const tab = tabs.find((t: { display_label: string }) => t.display_label === label);
    return (await fetch(`/api/attendance/tabs/${tab.id}/`)).json();
  }, label);
  expect(detail.orders).toHaveLength(1);
  const items = detail.orders[0].items;
  expect(items).toHaveLength(2);
  expect(items.find((i: { product_name: string }) => i.product_name === "Brahma 600 ml").unit_price_cents).toBe(1200);
  expect(items.find((i: { product_name: string }) => i.product_name === "Coxinha de Queijo com Alho").unit_price_cents).toBe(350);
  expect(detail.payments_cents).toBe(0);
  expect(detail.exposure_cents).toBe(1550);
  const out = path.resolve(__dirname, "../../../../visual-artifacts/spec023-024/runtime");
  await mkdir(out, { recursive: true });
  await page.screenshot({ path: path.join(out, `menu-attendance-${width}.png`), fullPage: true });
  for (const [station, name] of [["bar", "Brahma 600 ml"], ["kitchen", "Coxinha de Queijo com Alho"]]) {
    await page.goto(`/${station}`);
    const order = page.getByRole("group", { name: /^Pedido: / }).filter({ hasText: label });
    await expect(order.getByText(`1 ${name}`, { exact: true })).toBeVisible();
    await order.getByRole("button", { name: /^Iniciar preparo:/ }).click();
    await expect(order.getByRole("button", { name: /^Pronto:/ })).toBeEnabled();
    await order.getByRole("button", { name: /^Pronto:/ }).click();
    await expect(order).toHaveCount(0);
    const ready = page.locator(".stationPassRow").filter({ hasText: label });
    await expect(ready.getByText(`1 ${name}`, { exact: true })).toBeVisible();
    await page.screenshot({ path: path.join(out, `menu-${station}-${width}.png`), fullPage: true });
  }
});
