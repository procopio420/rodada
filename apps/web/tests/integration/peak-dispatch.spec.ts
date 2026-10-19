import { test, expect } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { writeFile } from "node:fs/promises";

function snapshot() {
  return JSON.parse(execFileSync(process.env.RODADA_TEST_PYTHON!, [resolve("tests/integration/peak-dispatch-fixture.py")],
    { env: process.env, encoding: "utf8", timeout: 60_000 }));
}
for (const width of [360, 390, 430, 1280]) test(`50 persisted READY and 50 calls retain navigation and fallback at ${width}`, async ({ page }) => {
  test.setTimeout(90_000);
  const before = snapshot();
  expect(before.tasks).toHaveLength(100); expect(before.items).toHaveLength(50);
  expect(before.payments).toEqual([]); expect(before.charges.every((row: { amount_cents: number }) => row.amount_cents === 0)).toBe(true);
  let failing = false;
  const reads = { delivery: 0, requests: 0 };
  await page.route(/\/api\/attendance\/dispatch\/(delivery|requests)\/$/, route => {
    reads[route.request().url().includes("/delivery/") ? "delivery" : "requests"]++;
    return failing ? route.fulfill({ status: 503, json: { code: "DISPATCH_UNAVAILABLE", message: "Injected Dispatch outage" } }) : route.continue();
  });
  await page.setViewportSize({ width, height: 844 }); await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Atendimentos 50", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Entregas 50", exact: true })).toBeVisible();
  const queues = await page.evaluate(async () => {
    const read = async (path: string) => (await (await fetch(`/api/attendance/${path}`)).json()).results;
    return { service: await read("dispatch/requests/"), delivery: await read("dispatch/delivery/"), tables: await read("hospitality/tables/") };
  });
  expect(queues.service).toHaveLength(50); expect(queues.delivery).toHaveLength(50);
  expect(new Set(queues.delivery.map((row: { zone_id: string }) => row.zone_id)).size).toBe(5);
  expect(new Set(queues.service.map((row: { zone_id: string }) => row.zone_id)).size).toBe(5);
  const writes: string[] = [], taskReads: string[] = [];
  page.on("request", request => {
    if (request.method() !== "GET") writes.push(request.url());
    if (request.method() === "GET" && request.url().includes("/dispatch/tasks/")) taskReads.push(new URL(request.url()).pathname);
  });
  const service = queues.service.at(-1); const table = queues.tables.find((row: { id: string }) => row.id === service.target.table_id);
  await expect(page.locator(".ux2ServiceQueue .ux2QueueItem")).toHaveCount(50);
  await page.locator(".ux2ServiceQueue .ux2QueueItem").filter({ hasText: service.destination_label }).getByRole("button").first().click();
  await expect(page.locator(".ux2TablePage").getByRole("heading", { name: `Mesa ${table.label}`, exact: true })).toBeVisible();
  await page.locator(".ux2TablePage").getByRole("button", { name: "Voltar", exact: true }).click();
  await page.getByRole("button", { name: "Agora", exact: true }).click();
  await page.getByRole("button", { name: "Entregas 50", exact: true }).click();
  const delivery = queues.delivery.at(-1);
  await expect(page.locator(".ux2QueueItem:visible")).toHaveCount(50);
  await page.locator(".ux2QueueItem:visible").filter({ hasText: delivery.tab_label }).getByRole("button", { name: "Ver entrega ›", exact: true }).click();
  const detail = page.getByRole("region", { name: "Levar pedido.", exact: true });
  await expect(detail.getByText(`${delivery.quantity}× ${delivery.product_name}`, { exact: true })).toBeVisible();
  await expect(detail).toContainText(delivery.tab_display_reference);
  await detail.getByRole("button", { name: "Voltar sem concluir", exact: true }).click();
  failing = true;
  await expect(page.getByRole("button", { name: "Entregas —", exact: true })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("button", { name: "Atendimentos —", exact: true })).toBeVisible({ timeout: 20_000 });
  await expect(page.locator(".ux2QueueItem:visible")).toHaveCount(50);
  await page.screenshot({ path: test.info().outputPath("peak-stale.png"), fullPage: true });
  failing = false;
  await page.getByRole("button", { name: "Atualizar entregas", exact: true }).click();
  await expect(page.getByRole("button", { name: "Entregas 50", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Atendimentos —", exact: true }).click();
  await page.getByRole("button", { name: "Atualizar chamadas", exact: true }).click();
  await expect(page.getByRole("button", { name: "Atendimentos 50", exact: true })).toBeVisible();
  await expect(page.locator(".ux2ServiceQueue .ux2QueueItem")).toHaveCount(50);
  await page.screenshot({ path: test.info().outputPath("peak-reconnected.png"), fullPage: true });
  expect(reads.delivery).toBeGreaterThan(2); expect(reads.requests).toBeGreaterThan(2);
  expect(writes).toEqual([]);
  expect(taskReads).toContain(`/api/attendance/dispatch/tasks/${service.id}/`);
  expect(taskReads).toContain(`/api/attendance/dispatch/tasks/${delivery.id}/`);
  const after = snapshot(); expect(after).toEqual(before);
  await writeFile(test.info().outputPath("canonical-proof.json"), JSON.stringify({ width, service, delivery,
    zones: [...new Set(queues.delivery.map((row: { zone_id: string }) => row.zone_id))], reads, taskReads, writes, before, after }, null, 2));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
