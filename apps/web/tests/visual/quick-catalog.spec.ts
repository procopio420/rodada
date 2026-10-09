import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const width of [360, 390, 430]) {
  test(`Quick Catalog accessible mobile flow ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.route("**/api/**", route => {
      const path = new URL(route.request().url()).pathname;
      if (path === "/api/auth/me") return route.fulfill({ json: { capabilities: ["catalog.create.bar"] } });
      return route.fulfill({ json: { results: [] } });
    });
    await page.goto("/bar");
    await page.getByRole("button", { name: "+ Item", exact: true }).click();
    await page.getByRole("combobox").fill("Cerveja artesanal");
    await page.getByRole("option", { name: "Criar “Cerveja artesanal”" }).click();
    await expect(page.getByLabel("Preço (R$)")).toBeFocused();
    expect(await page.locator("body").evaluate(el => el.scrollWidth <= innerWidth)).toBe(true);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(results.violations).toEqual([]);
    await page.screenshot({ path: `test-results/quick-catalog-${width}.png`, fullPage: true });
  });
}
