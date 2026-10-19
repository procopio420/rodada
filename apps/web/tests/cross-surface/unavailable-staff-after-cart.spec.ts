import { chooseBarAvailability } from "../visual/station-availability-actions";
import { addCatalogItem } from "../visual/category-actions";
import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";

test("E2E-05: Attendance Web stale cart rejects actual Bar availability flip", async ({ page, browser }) => {
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
    name: "E2E05 Web " + Date.now(), price_cents: 500, fulfillment_station: "BAR",
  })).product;
  const table = await api("hospitality/tables/", { label: "E2E05 Web " + Date.now(), guest_ordering_mode: "DIRECT" });
  // Set up an occupied table before testing the staff ordering UI; AVAILABLE tables cannot open a second Tab directly.
  await api("hospitality/tables/" + table.id + "/occupy/", {});
  const stationContext = await browser.newContext({ baseURL: "http://127.0.0.1:3110", storageState: await page.context().storageState() });
  try {
    const station = await stationContext.newPage();
    await station.goto("/bar");
    await page.goto("/attendance");
    await page.getByRole("button", { name: new RegExp("^Mesa " + table.label) }).click();
    await page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
    await page.getByRole("dialog").getByRole("textbox").fill("E2E05 staff");
    await page.getByRole("dialog").getByRole("button", { name: /Abrir/ }).click();
    const dialog = page.locator(".attendanceOrderDialog");
    await addCatalogItem(page, product.name);
    await dialog.getByRole("button", { name: /Pedido atual/ }).click();
    await expect(dialog.getByRole("button", { name: /^Confirmar pedido/ })).toBeEnabled();

    await page.route(/\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/, async route => {
      await chooseBarAvailability(station, product.name);
      await station.getByRole("button", { name: "Sim, indisponibilizar", exact: true }).click();
      await expect.poll(async () => {
        const catalog = await api("catalog/products/");
        return catalog.results.find((entry: { id: string }) => entry.id === product.id)?.availability;
      }).toBe("UNAVAILABLE");
      await route.continue();
    });
    const responsePromise = page.waitForResponse(response =>
      /\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/.test(response.url()) && response.request().method() === "POST");
    await dialog.getByRole("button", { name: /^Confirmar pedido/ }).click();
    const response = await responsePromise;
    expect(response.status()).toBe(409);
    expect((await response.json()).code).toBe("PRODUCTS_NOT_CONFIRMABLE");
    await expect(page.getByRole("alert").filter({ hasText: /não podem mais ser confirmados/ })).toBeVisible();
    await expect(dialog.getByText(product.name).first()).toBeVisible();

    const tableRow = (await api("hospitality/tables/")).results.find((entry: { id: string }) => entry.id === table.id);
    const tabId = tableRow.active_occupancy.tabs[0].id;
    const detail = await api("tabs/" + tabId + "/");
    expect(detail.orders).toHaveLength(0);
    expect(detail.exposure_cents).toBe(0);
    await writeFile("../../artifacts/unavailable-staff-browser.json", JSON.stringify({
      sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
      database_instance_id: fixture.database_instance_id, venue_id: fixture.venue_id,
      tab_id: tabId, product_id: product.id, denial: { status: 409, code: "PRODUCTS_NOT_CONFIRMABLE" },
      status: "PASS", scope: "Attendance Web and Bar real UIs; Android stale cart remains unproven",
    }, null, 2));
  } finally { await stationContext.close(); }
});
