import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`report result lists ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/management/reports/**", route => route.fulfill({ json: {
    start: "2026-10-07", end: "2026-10-08", generated_at: "2026-10-08T21:00:00Z", totals: {},
    daily: [{ date: "2026-10-07", net_sales_cents: 10000, net_received_cents: 8500, adjustments_cents: -500, refunds_cents: 1500 }, { date: "2026-10-08", net_sales_cents: 0, net_received_cents: 0, adjustments_cents: 0, refunds_cents: 0 }],
    products: [{ order_item__product_name_snapshot: "Produto de teste com identificação extensa para conferir leitura e quebra de linha", quantity: 12, gross_cents: 10000 }],
    payment_methods: [{ method: "CASH", count: 2, amount_cents: 5000 }, { method: "PIX", count: 1, amount_cents: 3500 }],
    orders: [{ source: "GUEST", status: "CONFIRMED", count: 3 }, { source: "CASHIER", status: "CANCELLED", count: 1 }], cash_shifts: [],
  } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "2026-10-07", exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S3O_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-report-results/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const day = page.getByRole("article", { name: "2026-10-07", exact: true });
  await expect(day.locator("strong")).toHaveText([/100,00/, /85,00/, /-.*5,00.*15,00/]);
  await expect(page.getByRole("article", { name: "2026-10-08", exact: true }).locator("strong")).toHaveText([/0,00/, /0,00/, /0,00.*0,00/]);
  for (const [name, count] of [["Produtos vendidos", 1], ["Métodos de pagamento", 2], ["Origem e estado dos pedidos", 2]] as const) await expect(page.getByRole("list", { name, exact: true }).getByRole("listitem")).toHaveCount(count);
  await expect(page.getByText("Cliente · Confirmado", { exact: true })).toBeVisible();
  await expect(page.getByText("Caixa · Cancelado", { exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "[data-report-results] { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-report-results/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});
