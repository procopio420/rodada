import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";

test("E2E-05: Guest cart rejected after operational availability changes", async ({ page, browser }) => {
  const fixture = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill(fixture.venue_slug);
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();

  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch("/api/pos/" + path, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(path + ": " + response.status);
    return response.json();
  }, { path, body });

  const product = (await api("catalog/resolve-or-create/", {
    name: "E2E05 Guest " + Date.now(), price_cents: 400, fulfillment_station: "BAR",
  })).product;
  const table = await api("hospitality/tables/", { label: "E2E05 " + Date.now(), guest_ordering_mode: "DIRECT" });
  const context = await browser.newContext({ baseURL: "http://127.0.0.1:3110" });
  const stationContext = await browser.newContext({ baseURL: "http://127.0.0.1:3110", storageState: await page.context().storageState() });
  try {
    const station = await stationContext.newPage();
    await station.goto("/bar");
    const guest = await context.newPage();
    await guest.goto("/guest/" + table.public_token);
    await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    await guest.getByRole("button", { name: new RegExp("^" + product.name) }).click();
    await expect(guest.getByRole("region", { name: "Pedido atual" })).toContainText(product.name);
    await guest.route("**/api/guest/orders/confirm/", async route => {
      await station.getByRole("button", { name: "Indisponibilizar " + product.name, exact: true }).click();
      await expect.poll(async () => {
        const catalog = await api("catalog/products/");
        return catalog.results.find((entry: { id: string }) => entry.id === product.id)?.availability;
      }).toBe("UNAVAILABLE");
      await route.continue();
    });
    const responsePromise = guest.waitForResponse(response =>
      response.url().includes("/api/guest/orders/confirm/") && response.request().method() === "POST");
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    const response = await responsePromise;
    expect(response.status()).toBe(409);
    expect((await response.json()).code).toBe("PRODUCTS_NOT_CONFIRMABLE");
    await expect(guest.getByRole("region", { name: "Pedido atual" })).toContainText(product.name);
    const record = (await api("hospitality/tables/")).results.find((value: { id: string }) => value.id === table.id);
    const tabId = record.active_occupancy.tabs[0].id;
    const tab = await api("tabs/" + tabId + "/");
    expect(tab.orders).toHaveLength(0);
    expect(tab.exposure_cents).toBe(0);
    await writeFile("../../artifacts/unavailable-cart-browser.json", JSON.stringify({
      sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
      database_instance_id: fixture.database_instance_id, venue_id: fixture.venue_id,
      product_id: product.id, tab_id: tabId,
      denial: { status: response.status(), code: "PRODUCTS_NOT_CONFIRMABLE" },
      status: "PASS", scope: "Guest real UI and Bar real availability UI; Android/staff stale carts still pending",
    }, null, 2));
  } finally { await context.close(); await stationContext.close(); }
});
