import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
const destinations = [
  { id: "products", path: "/manage/products", label: "Cardápio e nomes dos produtos" },
  { id: "customizations", path: "/manage/catalog", label: "Variações e adicionais" },
];
for (const width of [360, 390, 430, 1280]) for (const destination of destinations) test(`menu return focus ${destination.id} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  const writes: string[] = [];
  page.on("request", r => { if (r.url().includes("/api/") && !["GET", "HEAD"].includes(r.method())) writes.push(r.url()); });
  await page.goto("/manage#cardapio");
  const origin = page.getByRole("link", { name: destination.label, exact: true });
  await origin.click();
  await expect(page).toHaveURL(new RegExp(`${destination.path}$`));
  await page.getByRole("link", { name: "Voltar ao Cardápio", exact: true }).click();
  await expect(page).toHaveURL(/\/manage#cardapio$/);
  await stable(page);
  const phase = process.env.RODADA_S5_FOCUS_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-menu-return/${phase}-${destination.id}-${width}.png`, fullPage: true });
  await expect(origin).toBeFocused();
  await layoutAndA11y(page);
  const bounds = await origin.boundingBox();
  const nav = await page.getByRole("navigation").boundingBox();
  expect(bounds!.y).toBeGreaterThanOrEqual(0);
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(nav!.y);
  expect(writes).toEqual([]);
});
for (const destination of destinations) test(`menu direct return ${destination.id}`, async ({ page }) => {
  await fixture(page);
  await page.goto(destination.path);
  await page.getByRole("link", { name: "Voltar ao Cardápio", exact: true }).click();
  await expect(page.getByRole("link", { name: destination.label, exact: true })).toBeFocused();
});
test("menu return remains available without storage", async ({ page }) => {
  await fixture(page);
  await page.addInitScript(() => { Object.defineProperty(window, "sessionStorage", { get() { throw new Error("Storage unavailable"); } }); });
  await page.goto("/manage/products");
  await page.getByRole("link", { name: "Voltar ao Cardápio", exact: true }).click();
  await expect(page).toHaveURL(/\/manage#cardapio$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Cardápio");
});
