import { expect, test } from "@playwright/test";
import { fixture } from "./fixtures";

for (const station of ["BAR", "KITCHEN"]) test(`station clock starts with snapshot and ticks ${station}`, async ({ page }) => {
  await fixture(page, "normal", true);
  const writes: string[] = [];
  page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/pos/")) writes.push(request.url()); });
  await page.route(`**/api/pos/production/${station}/`, route => route.fulfill({ json: { results: [
    { id: "clock-item", product_id: "fries", order_id: "clock-order", state: "PREPARING", quantity: 1, product_name: "Item com horário", tab_label: "Comanda de teste", created_at: "2026-10-08T20:55:00Z" },
    { id: "unknown-item", product_id: "fries", order_id: "unknown-order", state: "PREPARING", quantity: 1, product_name: "Item sem horário", tab_label: "Comanda de teste", created_at: "invalid" },
  ] } }));
  await page.goto(station === "BAR" ? "/bar" : "/kitchen");
  const times = page.getByLabel("Tempo desde o pedido");
  await expect(times).toHaveCount(2);
  await expect(times.filter({ hasText: "5:00" })).toHaveCount(1);
  await expect(times.filter({ hasText: "Tempo não informado" })).toHaveCount(1);
  await page.clock.setFixedTime(new Date("2026-10-08T21:00:15Z"));
  await page.clock.runFor(15000);
  await expect(times.filter({ hasText: "5:15" })).toHaveCount(1);
  await expect(times.filter({ hasText: "Tempo não informado" })).toHaveCount(1);
  expect(writes).toEqual([]);
});
