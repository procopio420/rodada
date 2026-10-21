import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`now summary and shortcuts ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page, "warnings");
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/manage");
  const pulse = page.getByRole("heading", { name: "Agora", exact: true });
  await expect(pulse).toBeVisible();
  const exception = page.getByRole("heading", { name: "Divergências de caixa pendentes" });
  expect((await exception.boundingBox())!.y).toBeLessThan((await pulse.boundingBox())!.y);
  await stable(page);
  const phase = process.env.RODADA_S2A_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-now/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const metrics = page.getByRole("region", { name: "Agora", exact: true }).locator(".operationalMetric");
  const first = (await metrics.filter({ hasText: "Exposição em aberto" }).boundingBox())!;
  const second = (await metrics.filter({ hasText: "Comandas abertas" }).boundingBox())!;
  if (width < 768) expect(second.y).toBeGreaterThanOrEqual(first.y + first.height);
  else expect(second.y).toBe(first.y);
  const shortcuts = page.getByRole("navigation", { name: "Acessos rápidos" });
  for (const link of await shortcuts.getByRole("link").all()) {
    expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await expect(link).toHaveAttribute("href", /\/(attendance|cash)$/);
  }
  await shortcuts.getByRole("link").first().focus();
  await page.keyboard.press("Tab");
  await expect(shortcuts.getByRole("link").nth(1)).toBeFocused();
  const details = page.locator("details").filter({ has: page.getByText("Ver mais do resumo", { exact: true }) });
  await details.locator("summary").focus();
  await page.keyboard.press("Enter");
  await expect(details.getByText("Itens indisponíveis", { exact: true })).toBeVisible();
  await expect(details.getByRole("link")).toHaveAttribute("href", "/manage#operacao");
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-now/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});
