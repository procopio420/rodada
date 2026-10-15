import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";

for (const origin of ["guest", "attendance"] as const) test(`${origin} rejects product unavailable after cart without ledger effects`, async ({ page, browser }) => {
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill(f.venue_slug);
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const r = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(`${path}: ${r.status}`); return r.json();
  }, { path, body });
  const label = `Catalog-${origin}-${Date.now()}`;
  const table = await api("hospitality/tables/", { label, guest_ordering_mode: "DIRECT" });
  const context = await browser.newContext({ baseURL: "http://127.0.0.1:3110", ...(origin === "attendance" ? { storageState: await page.context().storageState() } : {}) });
  try {
    const client = await context.newPage();
    if (origin === "guest") {
      await client.goto(`/guest/${table.public_token}`);
      await client.getByRole("button", { name: "Abrir minha comanda" }).click();
      await client.getByRole("button", { name: /^Android Compose Test Meal/ }).click();
    } else {
      await client.goto("/attendance");
      await client.getByRole("button", { name: new RegExp(`^Mesa ${label}`) }).click();
      await client.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
      await client.getByRole("dialog").getByRole("textbox").fill(label);
      await client.getByRole("dialog").getByRole("button", { name: /Abrir/ }).click();
      await client.locator(".attendanceOrderDialog").getByRole("button", { name: /^Android Compose Test Meal/ }).click();
      await client.locator(".attendanceOrderDialog").getByRole("button", { name: /Pedido atual/ }).click();
    }
    let rejected = 0;
    const routePattern = origin === "guest" ? "**/api/guest/orders/confirm/" : /\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/;
    await client.route(routePattern, async route => {
      // Change REAL server state at the boundary after UI captured its cart.
      await api(`catalog/products/${f.kitchen_product_id}/availability/`, { state: "UNAVAILABLE" });
      const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
      rejected = response.status(); expect(rejected).toBe(409);
      expect((await response.json()).code).toBe("PRODUCTS_NOT_CONFIRMABLE");
      await route.fulfill({ response });
    });
    await client.getByRole("button", { name: origin === "guest" ? /^Enviar ·/ : /^Confirmar pedido/ }).click();
    await expect.poll(() => rejected).toBe(409);
    await expect(client.getByText(origin === "guest" ? "Um item do carrinho acabou de ficar indisponível. Atualize o pedido." : "Um ou mais itens não podem mais ser confirmados.", { exact: true })).toBeVisible();
    const current = (await api("hospitality/tables/")).results.find((t: { id: string }) => t.id === table.id);
    const tab = await api(`tabs/${current.active_occupancy.tabs[0].id}/`);
    expect(tab.orders).toHaveLength(0); expect(tab.exposure_cents).toBe(0); expect(tab.payments).toHaveLength(0);
    await writeFile(`../../artifacts/catalog-${origin}-browser.json`, JSON.stringify({ sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(), database_instance_id: f.database_instance_id, venue_id: f.venue_id, tab_id: tab.id, status: "PASS", rejected_status: rejected, origin, product_id: f.kitchen_product_id }, null, 2));
  } finally {
    await api(`catalog/products/${f.kitchen_product_id}/availability/`, { state: "AVAILABLE" });
    await context.close();
  }
});
