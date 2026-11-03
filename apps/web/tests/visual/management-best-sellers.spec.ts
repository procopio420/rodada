import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`best sellers ranking ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page, "warnings");
  let quantity = 8;
  let day = "2026-10-08";
  let fail = false;
  const writes: string[] = [];
  page.on("request", r => { if (r.url().includes("/api/") && !["GET", "HEAD"].includes(r.method())) writes.push(r.url()); });
  await page.route("**/api/pos/management/calendar/", route => route.fulfill({ json: { business_date: day, timezone: "America/Sao_Paulo", cutoff_hour: 4 } }));
  await page.route("**/api/pos/management/reports/**", route => {
    expect(new URL(route.request().url()).searchParams.get("start")).toBe(day);
    return route.fulfill(fail ? { status: 403, json: { message: "Consulta não autorizada.", code: "CAPABILITY_REQUIRED" } } : { json: { products: quantity ? [
      { order_item__product_id: "beer", order_item__product_name_snapshot: "Cerveja", quantity },
      { order_item__product_id: "beer", order_item__product_name_snapshot: "Cerveja antiga", quantity: 2 },
      { order_item__product_id: "fries", order_item__product_name_snapshot: "Fritas com nome longo para verificar quebra de linha", quantity: 3 },
    ] : [] } });
  });
  await page.goto("/manage");
  const choice = page.getByRole("button", { name: "Mais vendidos", exact: true });
  await choice.click();
  const list = page.getByRole("list", { name: "Produtos mais vendidos" });
  await expect(list.getByRole("listitem")).toHaveCount(2);
  await expect(list.getByRole("listitem").first()).toContainText("10");
  await expect(list.getByRole("listitem").first()).toContainText("Cerveja");
  await expect(choice).toHaveAttribute("aria-pressed", "true");
  expect((await choice.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await stable(page);
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/best-sellers/${width}.png`, fullPage: true });
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  await layoutAndA11y(page);
  await page.getByRole("button", { name: "Resumo", exact: true }).focus();
  await page.keyboard.press("Tab");
  await expect(choice).toBeFocused();
  quantity = 12;
  await expect(list.getByRole("listitem").first()).toContainText("14", { timeout: 22000 });
  day = "2026-10-09"; quantity = 0;
  await page.getByRole("button", { name: "Atualizar ranking", exact: true }).click();
  await expect(page.getByText("Nenhuma venda nesta noite.")).toBeVisible();
  await expect(page.getByText(/Noite de 09\/10\/2026/)).toBeVisible();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "html { font-size: 100%; }" });
  await page.locator("#now-best-sellers").evaluate(element => element.scrollIntoView({ block: "start" }));
  await page.locator("#now-best-sellers").screenshot({ path: `../../visual-artifacts/best-sellers/empty-refined-${width}.png` });
  await page.getByText("Como é calculado", { exact: true }).click();
  await expect(page.getByText(/Cancelamentos e ajustes não são deduzidos/)).toBeVisible();
  await page.getByText("Como é calculado", { exact: true }).click();
  fail = true;
  await page.getByRole("button", { name: "Atualizar ranking", exact: true }).click();
  await expect(page.getByText("Consulta não autorizada.")).toBeVisible();
  await expect(page.getByText("Nenhuma venda nesta noite.")).toHaveCount(0);
  fail = false;
  await page.getByRole("button", { name: "Atualizar ranking", exact: true }).click();
  await expect(page.getByText("Nenhuma venda nesta noite.")).toBeVisible();
  expect(writes).toEqual([]);
});

test("best sellers limits ten products and orders ties consistently", async ({ page }) => {
  await fixture(page, "warnings");
  const products = Array.from({ length: 12 }, (_, index) => ({
    order_item__product_id: `product-${index}`,
    order_item__product_name_snapshot: `Produto ${String(index).padStart(2, "0")}`,
    quantity: 5,
  })).reverse();
  await page.route("**/api/pos/management/reports/**", route => route.fulfill({ json: {
    products: [...products,
      { order_item__product_id: "product-0", order_item__product_name_snapshot: "Nome anterior", quantity: 3 },
      { order_item__product_id: null, order_item__product_name_snapshot: null, quantity: null },
    ],
  } }));
  await page.goto("/manage");
  await page.getByRole("button", { name: "Mais vendidos", exact: true }).click();
  const rows = page.getByRole("list", { name: "Produtos mais vendidos" }).getByRole("listitem");
  await expect(rows).toHaveCount(10);
  await expect(rows.first()).toContainText("Produto 00");
  await expect(rows.first()).toContainText("8");
  for (let index = 1; index < 10; index++) {
    await expect(rows.nth(index)).toContainText(`Produto ${String(index).padStart(2, "0")}`);
  }
  await expect(page.getByText("Produto 10", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Produto 11", { exact: true })).toHaveCount(0);
});
