import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`report historical and current totals ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/management/reports/**", route => route.fulfill({ json: {
    start: "2026-10-08", end: "2026-10-08", generated_at: "2026-10-08T21:00:00Z", timezone: "America/Sao_Paulo", cutoff_hour: 4,
    totals: { gross_cents: 10000, net_sales_cents: 8000, paid_cents: 7000, refunds_cents: 500, net_received_cents: 6500, current_open_exposure_cents: 1200, current_open_tabs: 2, additional_metric: 3 },
    daily: [], products: [], payment_methods: [], orders: [], cash_shifts: [],
  } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/reports");
  await expect(page.getByText("Exposição em aberto agora", { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S3N_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-report-summary/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const summary = page.getByRole("region", { name: "Resumo financeiro", exact: true });
  const historical = summary.getByRole("group", { name: "No período", exact: true });
  const current = summary.getByRole("group", { name: "Estado atual", exact: true });
  await expect(historical.locator(".operationalMetric strong")).toHaveText([/100,00/, /80,00/, /70,00/, /5,00/, /65,00/, "3"]);
  await expect(current.locator(".operationalMetric strong")).toHaveText([/12,00/, "2"]);
  await expect(historical.getByText("additional_metric", { exact: true })).toBeVisible();
  await expect(summary.locator(".operationalMetric")).toHaveCount(8);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#report-summary { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-report-summary/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});
