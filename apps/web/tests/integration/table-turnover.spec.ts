import { expect, test } from "./fixtures";

test("Table turnover real PostgreSQL report shows canonical coverage at mobile and desktop widths", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();

  const call = (path: string, method = "GET", body?: unknown) => page.evaluate(async ({ path, method, body }) => {
    const r = await fetch(`/api/pos/${path}`, {
      method, headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
    return r.json();
  }, { path, method, body });
  const table = await call("hospitality/tables/", "POST", {
    label: "Giro E2E", guest_ordering_mode: "DIRECT",
  });
  await call(`hospitality/tables/${table.id}/occupy/`, "POST", {});
  await call(`hospitality/tables/${table.id}/release/`, "POST", {});
  await call(`hospitality/tables/${table.id}/cleaning/start/`, "POST", {});
  await call(`hospitality/tables/${table.id}/cleaning/complete/`, "POST", {});
  const calendar = await call("management/calendar/");
  const report = await call(`management/table-turnover/?start=${calendar.business_date}&end=${calendar.business_date}`);
  expect(report.summary.released).toBe(1);
  expect(report.summary.ready).toBe(1);
  expect(report.summary.timings.occupancy.observed).toBe(1);
  expect(report.summary.timings.cleaning.observed).toBe(1);
  expect(report.summary.orders.denominator).toBe(0);
  expect(report.summary.orders.guest_percent).toBeNull();
  expect(report.tables.find((row: { table_id: string }) => row.table_id === table.id).released).toBe(1);

  await page.goto("/manage/table-turnover");
  await expect(page.getByRole("heading", { name: "Giro e limpeza das mesas" })).toBeVisible();
  const total = page.locator(".operationalMetric").filter({ hasText: "Mesas liberadas (giros)" });
  await expect(total.locator("strong")).toHaveText("1");
  await expect(page.getByText("Giro E2E")).toBeVisible();
  await expect(page.getByText("Sem dados", { exact: true })).toBeVisible();
  for (const width of [360, 390, 430, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `test-results/turnover-${width}.png`, fullPage: true });
  }
});
