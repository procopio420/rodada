import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const destinations = [
  ["Caixa e turnos", "/cash"], ["Fechamento diário e aprovações", "/manage/daily-close"],
  ["Correções e estornos", "/refunds"], ["Serviço, descontos e aprovações", "/manage/pricing"],
  ["Relatórios de vendas e recebimentos", "/reports"],
];
for (const width of [360, 390, 430, 1280]) test(`finance entry readable ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/cash/points/", route => route.fulfill({ json: { results: [
    { id: "cash-open", label: "Caixa de teste com identificação extensa", active_shift: { status: "OPEN", expected_cents: 123456 } },
    { id: "cash-counting", label: "Caixa em conferência de teste", active_shift: { status: "COUNTING", expected_cents: 0 } },
    { id: "cash-no-total", label: "Caixa sem total informado", active_shift: { status: "OPEN" } },
  ] } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/manage#financeiro");
  const finance = page.locator("#financeiro");
  await expect(finance.getByText("Caixa de teste com identificação extensa · Aberto", { exact: true })).toBeVisible();
  await expect(finance.getByText("Caixa em conferência de teste · Em contagem", { exact: true })).toBeVisible();
  await expect(finance.getByText("Ver caixa", { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S3A_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-finance/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  for (const [name, href] of destinations) {
    const link = finance.getByRole("link", { name, exact: true });
    await expect(link).toHaveAttribute("href", href);
    await expect(link).toHaveAccessibleDescription(/\S+/);
    expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  }
  await finance.getByRole("link").first().focus();
  await page.keyboard.press("Tab");
  await expect(finance.getByRole("link").nth(1)).toBeFocused();
  await expect(finance.getByRole("region", { name: "Caixa e fechamento", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#financeiro { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-finance/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

test("finance confirmed empty and rejected initial read", async ({ page }) => {
  await fixture(page, "empty");
  await page.goto("/manage#financeiro");
  await expect(page.getByText("Nenhum caixa com turno ativo.", { exact: true })).toBeVisible();
  await page.route("**/api/pos/cash/points/", route => route.fulfill({ status: 403, json: { message: "Sem permissão para consultar caixas." } }));
  await page.reload();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Último estado confirmado");
  await expect(page.locator("#financeiro")).toBeVisible();
  await page.evaluate(() => sessionStorage.clear());
  await page.reload();
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(page.locator("#financeiro")).toHaveCount(0);
});
