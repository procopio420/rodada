import { expect, test, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";

type NativeProof = {
  database: string;
  venue_id: string;
  venue_slug: string;
  result: string;
  original_order_id: string;
  original_tab_id: string;
  orders: number;
  order_items: number;
  charges: number;
  payments: number;
  original_key_preserved: boolean;
};

type TabDetail = {
  id: string;
  exposure_cents: number;
  payments_cents: number;
  orders: Array<{
    id: string;
    items: Array<{ id: string; state: string; product_id: string; quantity: number }>;
  }>;
};

async function readCanonicalTab(page: Page, id: string): Promise<TabDetail> {
  const result = await page.evaluate(async tabId => {
    const response = await fetch(`/api/pos/tabs/${tabId}/`);
    return { status: response.status, body: await response.json() };
  }, id);
  expect(result.status, JSON.stringify(result.body)).toBe(200);
  return result.body as TabDetail;
}

test("native Android committed POST, offline replay, then real Web Bar production on the identical Tab", async ({ page }) => {
  // Produced exclusively by the real Android instrumentation + PostgreSQL SQL verifier.
  // This suite MUST NOT generate a mock receipt or a browser-originated order.
  const receiptPath = process.env.RODADA_ANDROID_PROOF;
  expect(receiptPath, "Run scripts/android-live-post-drop.sh before this browser gate").toBeTruthy();
  const receipt = JSON.parse(await readFile(path.resolve(receiptPath!), "utf8")) as NativeProof;
  expect(receipt).toMatchObject({
    result: "PASS",
    orders: 1,
    order_items: 1,
    charges: 1,
    payments: 0,
    original_key_preserved: true,
  });
  expect(receipt.original_order_id).toBeTruthy();
  expect(receipt.original_tab_id).toBeTruthy();
  expect(receipt.database).toBe("rodada_android_post_drop");
  expect(receipt.venue_slug).toBe("android-post-drop-ci");
  expect(receipt.venue_id).toBeTruthy();

  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("android-post-drop-ci");
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468"); // Ephemeral CI-only fixture.
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();

  const before = await readCanonicalTab(page, receipt.original_tab_id);
  expect(before.orders).toHaveLength(1);
  expect(before.orders[0].id).toBe(receipt.original_order_id);
  expect(before.orders[0].items).toHaveLength(1);
  const nativeItem = before.orders[0].items[0];
  expect(nativeItem.quantity).toBe(1);
  expect(nativeItem.state).toBe("NEW"); // No silent auto-prepare.
  expect(before.exposure_cents).toBe(700);
  expect(before.payments_cents).toBe(0); // No fabricated settlement.

  // Exercise the actual Web station UI against the same persisted Android order.
  await page.goto("/bar");
  await expect(page.getByText("Android Post Drop Test Soda", { exact: true }).first()).toBeVisible();
  const start = page.getByRole("button", { name: /^Iniciar preparo:.*Android TCP reset acceptance$/ }).first();
  await expect(start).toBeVisible();
  await start.click();

  await expect.poll(async () => {
    const detail = await readCanonicalTab(page, receipt.original_tab_id);
    return detail.orders[0].items[0].state;
  }).toBe("PREPARING");

  const ready = page.getByRole("button", { name: /^Pronto:.*Android TCP reset acceptance$/ }).first();
  await expect(ready).toBeVisible();
  await ready.click();
  await expect.poll(async () => {
    const detail = await readCanonicalTab(page, receipt.original_tab_id);
    return detail.orders[0].items[0].state;
  }).toBe("READY");

  const after = await readCanonicalTab(page, receipt.original_tab_id);
  expect(after.orders).toHaveLength(1);
  expect(after.orders[0].id).toBe(receipt.original_order_id);
  expect(after.orders[0].items).toHaveLength(1);
  expect(after.orders[0].items[0].id).toBe(nativeItem.id);
  expect(after.exposure_cents).toBe(700);
  expect(after.payments_cents).toBe(0);
});
