import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

async function setup(page: Page) {
  await fixture(page, "normal", true);
  let failed = false;
  const orders = [{ id: "order-actual-uuid", status: "CONFIRMED", confirmed_at: "2026-10-16T19:00:00Z", items: [
    { id: "historical-bar", product_id: "fries", product_name: "Fritas", quantity: 2, state: "NEW", fulfillment_station_snapshot: "BAR" },
    { id: "historical-kitchen", product_id: "omelette", product_name: "Omelete", quantity: 1, state: "PREPARING", fulfillment_station_snapshot: "KITCHEN" },
  ] }];
  const tab = { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 2400, version: 2, orders, payments: [] };
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { table_service_enabled: true, results: [
    { id: "table-test", label: "08", status: "OCCUPIED", active_occupancy: { id: "visit", generation: 1, tabs: [tab] } },
  ] } }));
  await page.route(/\/api\/attendance\/tabs\/tab-test\/(\?.*)?$/, route => route.fulfill(failed
    ? { status: 503, json: { code: "READ_FAILED", message: "Leitura indisponível" } }
    : { json: tab }));
  const open = async () => {
    await page.getByRole("button", { name: /Mesa 08 Ocupada/ }).click();
    await page.locator('button[data-tab-id="tab-test"]').click();
    await expect(page.locator(".attendanceOrderDialog")).toBeVisible();
  };
  await page.goto("/attendance"); await open();
  return { orders, open, fail: () => { failed = true; }, recover: () => { failed = false; } };
}

for (const width of [360, 390, 430, 1280]) test(`canonical order confirmation persists across reload at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  const { open } = await setup(page);
  const status = page.getByRole("region", { name: "Último pedido confirmado" });
  await expect(status.getByText("Pedido #order-actual-uuid confirmado", { exact: true })).toBeVisible();
  await expect(status.getByText("2× Fritas · 1× Omelete", { exact: true })).toBeVisible();
  await expect(status.getByText("Bar · Na fila", { exact: true })).toBeVisible();
  await expect(status.getByText("Cozinha · Em preparo", { exact: true })).toBeVisible();
  await expect(status.getByText(/Pronto/)).toHaveCount(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `visual-artifacts/033/order-status-${width}.png`, fullPage: true });
  await page.reload(); await open();
  await expect(status).toContainText("#order-actual-uuid");
});

test("canonical refresh updates production, failed read stays explicitly stale", async ({ page }) => {
  const state = await setup(page);
  const status = page.getByRole("region", { name: "Último pedido confirmado" });
  state.orders[0].items[0].state = "READY";
  await page.clock.runFor(15000);
  await expect(status.getByText("Bar · Pronto", { exact: true })).toBeVisible();
  state.fail(); await page.clock.runFor(15000);
  await expect(status.getByText(/Estado desatualizado/)).toBeVisible();
  await expect(status).toContainText("#order-actual-uuid");
  state.recover();
  state.orders[0].items[0].fulfillment_station_snapshot = "";
  state.orders[0].items[0].state = "FUTURE_STATE";
  await page.clock.runFor(15000);
  await expect(status.getByText("Destino não informado · Estado não informado", { exact: true })).toBeVisible();
  await expect(status.getByText(/Estado desatualizado/)).toHaveCount(0);
});

test("unconfirmed read models never show canonical order confirmation", async ({ page }) => {
  const { orders } = await setup(page);
  orders[0].status = "PENDING";
  await page.clock.runFor(15000);
  await expect(page.getByRole("region", { name: "Último pedido confirmado" })).toHaveCount(0);
});
