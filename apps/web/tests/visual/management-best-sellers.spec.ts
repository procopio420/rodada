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
  await page.route("**/api/pos/catalog/products/**", route => route.fulfill({ json: { results: [
    { id: "beer", name: "Cerveja", category: "Cervejas" },
    { id: "fries", name: "Fritas", category: "Porções" },
  ] } }));
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
  await expect(page.getByText("Atualiza a cada 15 s", { exact: true })).toBeVisible();
  expect(await list.locator("li > [aria-hidden] > span").evaluateAll(bars => bars.map(bar => (bar as HTMLElement).style.height))).toEqual(["100%", "30%"]);
  const categories = page.getByRole("list", { name: "Unidades por categoria" });
  await expect(categories.getByRole("listitem").first()).toContainText("Cervejas");
  await expect(categories.getByRole("listitem").first()).toContainText("10 un.");
  await expect(categories.getByRole("listitem").last()).toContainText("Porções");
  const bars = list.locator("li > [aria-hidden] > span");
  const swatches = categories.locator("li > [aria-hidden]");
  const colors = await bars.evaluateAll(elements => elements.map(element => getComputedStyle(element).backgroundColor));
  expect(colors).toEqual(await swatches.evaluateAll(elements => elements.map(element => getComputedStyle(element).backgroundColor)));
  expect(new Set(colors).size).toBe(2);
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
  await expect(categories.getByRole("listitem").first()).toContainText("14 un.");
  day = "2026-10-09"; quantity = 0;
  await page.getByRole("button", { name: "Atualizar ranking", exact: true }).click();
  await expect(page.getByText("Nenhuma venda nesta noite.")).toBeVisible();
  await expect(page.getByText(/Noite de 09\/10\/2026/)).toBeVisible();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "html { font-size: 100%; }" });
  await page.locator("#now-best-sellers").evaluate(element => element.scrollIntoView({ block: "start" }));
  await page.locator("#now-best-sellers").screenshot({ path: `../../visual-artifacts/best-sellers/empty-refined-${width}.png` });
  await expect(page.getByText(/Noite de 09\/10\/2026 · Atualizado às/)).toBeVisible();
  await expect(page.getByText("Como é calculado", { exact: true })).toHaveCount(0);
  fail = true;
  await page.getByRole("button", { name: "Atualizar ranking", exact: true }).click();
  await expect(page.getByText("Consulta não autorizada.")).toBeVisible();
  await expect(page.getByText("Nenhuma venda nesta noite.")).toHaveCount(0);
  fail = false;
  await page.getByRole("button", { name: "Atualizar ranking", exact: true }).click();
  await expect(page.getByText("Nenhuma venda nesta noite.")).toBeVisible();
  expect(writes).toEqual([]);
});

test("best sellers refreshes on a live event before polling", async ({ page }) => {
  await fixture(page, "warnings");
  let rankingRead = false;
  let quantity = 3;
  await page.route("**/api/pos/management/reports/**", route => {
    rankingRead = true;
    return route.fulfill({ json: { products: [{ order_item__product_id: "beer", order_item__product_name_snapshot: "Cerveja", quantity }] } });
  });
  await page.route("**/api/realtime/stream/**", route => {
    if (!rankingRead) return route.fulfill({ contentType: "text/event-stream", body: ": sem evento\n\n" });
    quantity = 12;
    const event = { id: "visual-test:1", schema_version: 1, type: "order.confirmed", aggregate_type: "order", aggregate_id: "test-order", version: 1, venue_id: "venue-test", payload: {} };
    return route.fulfill({ contentType: "text/event-stream", body: `event: change\nid: visual-test:1\ndata: ${JSON.stringify(event)}\n\n` });
  });
  await page.goto("/manage");
  await page.getByRole("button", { name: "Mais vendidos", exact: true }).click();
  await expect(page.getByRole("list", { name: "Produtos mais vendidos" })).toContainText("12", { timeout: 5000 });
});

test("best sellers limits ten products and orders ties consistently", async ({ page }) => {
  await fixture(page, "warnings");
  const products = Array.from({ length: 12 }, (_, index) => ({
    order_item__product_id: `product-${index}`,
    order_item__product_name_snapshot: `Produto ${String(index).padStart(2, "0")}`,
    quantity: 5,
  })).reverse();
  await page.route("**/api/pos/catalog/products/**", route => route.fulfill({ json: { results: [
    { id: "product-10", name: "Produto 10", category: "Cervejas" },
    { id: "product-11", name: "Produto 11", category: "Todos" },
  ] } }));
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
  const categories = page.getByRole("list", { name: "Unidades por categoria" });
  await expect(categories.getByRole("listitem").filter({ hasText: "Cervejas" })).toContainText("5 un.");
  await expect(categories.getByRole("listitem").filter({ hasText: "Outros" })).toContainText("53 un.");
  await expect(categories.getByText("Todos", { exact: true })).toHaveCount(0);
});
