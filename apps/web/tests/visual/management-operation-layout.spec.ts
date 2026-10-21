import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`operation production and delivery ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/dispatch/delivery/", route => route.fulfill({ json: { results: Array.from({ length: 8 }, (_, i) => ({ id: `delivery-${i}`, product_name: "Produto de teste com descrição extensa para conferir quebra de linha", destination_label: i ? "Destino de teste com identificação extensa" : "", age_seconds: i ? 180 : 30 })) } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/manage#operacao");
  const panel = page.locator("#operacao");
  const summary = panel.locator("summary");
  await expect(summary).toHaveText("Ver mais das entregas (8)");
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(panel.getByText("Sem destino", { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S2B_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-operation/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  await expect(page.getByRole("region", { name: "Produção e entrega", exact: true })).toBeVisible();
  await expect(panel.getByRole("list", { name: "Entregas prontas" }).getByRole("listitem")).toHaveCount(8);
  await expect(panel.getByText("agora", { exact: true })).toBeVisible();
  for (const name of ["Abrir Bar", "Abrir Cozinha"]) {
    const link = panel.getByRole("link", { name, exact: true });
    expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await expect(link).toHaveAttribute("href", name === "Abrir Bar" ? "/bar" : "/kitchen");
  }
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#operacao { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-operation/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

test("operation empty and failed initial read", async ({ page }) => {
  await fixture(page, "empty");
  await page.goto("/manage#operacao");
  const panel = page.locator("#operacao");
  await expect(panel.getByText("Prontos para entrega", { exact: true })).toBeVisible();
  await panel.locator("summary").click();
  await expect(panel.getByText("Nenhuma entrega no último estado consultado.")).toBeVisible();
  await layoutAndA11y(page);
  await page.route("**/api/pos/dispatch/delivery/", route => route.fulfill({ status: 403, json: { message: "Sem permissão para consultar entregas." } }));
  await page.reload();
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(panel).toBeVisible();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Último estado confirmado; atualize para conferir a operação.");
  // Remove only the isolated browser fixture cache to exercise a first read.
  await page.evaluate(() => sessionStorage.clear());
  await page.reload();
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(panel).toHaveCount(0);
});
