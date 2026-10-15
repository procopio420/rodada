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
  original_key_preserved?: boolean;
  native_ui?: string;
  tab_label?: string;
  product_ids?: Record<string, string>;
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

for (const source of ["recovery", "compose"] as const) test(`native Android ${source}, then real Web Bar production on the identical Tab`, async ({ page }) => {
  // Produced exclusively by the real Android instrumentation + PostgreSQL SQL verifier.
  // This suite MUST NOT generate a mock receipt or a browser-originated order.
  const receiptPath = source === "recovery" ? process.env.RODADA_ANDROID_PROOF : process.env.RODADA_ANDROID_COMPOSE_PROOF;
  expect(receiptPath, "Run scripts/android-live-post-drop.sh before this browser gate").toBeTruthy();
  const receipt = JSON.parse(await readFile(path.resolve(receiptPath!), "utf8")) as NativeProof;
  expect(receipt).toMatchObject({
    result: "PASS",
    orders: 1,
    order_items: source === "compose" ? 2 : 1,
    charges: source === "compose" ? 2 : 1,
    payments: 0,

  });
  if (source === "recovery") expect(receipt.original_key_preserved).toBe(true);
  else expect(receipt.native_ui).toBe("production MainActivity Compose");
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
  const count = source === "compose" ? 2 : 1;
  const total = source === "compose" ? 1700 : 700;
  expect(before.orders[0].items).toHaveLength(count);
  const nativeItem = before.orders[0].items[0];
  expect(nativeItem.quantity).toBe(1);
  expect(nativeItem.state).toBe("NEW"); // No silent auto-prepare.
  expect(before.exposure_cents).toBe(total);
  expect(before.payments_cents).toBe(0); // No fabricated settlement.

  // Every station transition is an explicit click on the persisted native order.
  const label = receipt.tab_label ?? "Android TCP reset acceptance";
  for (const station of source === "compose" ? ["BAR", "KITCHEN"] : ["BAR"]) {
    const item = before.orders[0].items.find(i => i.product_id === (receipt.product_ids?.[station] ?? before.orders[0].items[0].product_id))!;
    expect(item, `missing ${station} route`).toBeTruthy();
    expect(item.state).toBe("NEW");
    await page.goto(station === "BAR" ? "/bar" : "/kitchen");
    const start = page.getByRole("button", { name: new RegExp(`^Iniciar preparo:.*${label}$`) }).first();
    await expect(start).toBeVisible();
    await start.click();
    await expect.poll(async () => (await readCanonicalTab(page, receipt.original_tab_id)).orders[0].items.find(i => i.id === item.id)?.state).toBe("PREPARING");
    await page.getByRole("button", { name: new RegExp(`^Pronto:.*${label}$`) }).first().click();
    await expect.poll(async () => (await readCanonicalTab(page, receipt.original_tab_id)).orders[0].items.find(i => i.id === item.id)?.state).toBe("READY");
  }

  const after = await readCanonicalTab(page, receipt.original_tab_id);
  expect(after.orders).toHaveLength(1);
  expect(after.orders[0].id).toBe(receipt.original_order_id);
  expect(after.orders[0].items).toHaveLength(count);
  expect(after.orders[0].items[0].id).toBe(nativeItem.id);
  expect(after.exposure_cents).toBe(total);
  expect(after.payments_cents).toBe(0);
});
