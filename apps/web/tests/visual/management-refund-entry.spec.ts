import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`refund entry ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/refunds");
  await expect(page.getByRole("heading", { name: "Estornos", exact: true })).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "Carregando estornos" })).toHaveCount(0);
  await stable(page);
  const phase = process.env.RODADA_S3G_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-refund-entry/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const back = page.getByRole("link", { name: "Voltar ao Financeiro", exact: true });
  await expect(back).toHaveAttribute("href", "/manage#financeiro");
  expect((await back.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await expect(page.getByRole("group", { name: "Confirmar identidade", exact: true })).toBeVisible();
  await expect(page.getByLabel("PIN do gerente", { exact: true })).toHaveAttribute("type", "password");
  await expect(page.getByRole("region", { name: "Selecionar comanda", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#refund-manager, #refund-tab { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-refund-entry/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});
