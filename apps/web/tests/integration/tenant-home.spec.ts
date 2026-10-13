import { expect, test } from "@playwright/test";

// Integration test: Next SSR resolves the real Django VenueDomain seeded in start_api.py.
// No mocked tenant context or browser-only substitution.
test("Spec 025: tenant hub is branded, navigable and 2/3/4-column responsive", async ({ page }) => {
  await page.setExtraHTTPHeaders({ Host: "e2ea.rodada.bar" });
  const nav = page.getByRole("navigation", { name: "Módulos operacionais" });

  for (const [width, columns] of [[360, 2], [390, 2], [430, 2], [768, 3], [1024, 3], [1280, 4], [1440, 4]] as const) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await expect(page.getByRole("img", { name: "Rodada" })).toBeVisible();
    await expect(page.getByText("Web E2E — test only", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Onde vamos trabalhar?" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Entrar ou trocar operador" })).toHaveAttribute("href", "/staff");

    const destinations = [
      ["Atendimento", "/atendimento"],
      ["Cozinha", "/cozinha"],
      ["Bar", "/bar"],
      ["Caixa", "/caixa"],
      ["Gerência", "/gerencia"],
    ] as const;
    await expect(nav.getByRole("link")).toHaveCount(destinations.length);
    for (const [label, href] of destinations) {
      const link = nav.getByRole("link", { name: new RegExp("^" + label) });
      await expect(link).toHaveAttribute("href", href);
      expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    }
    const actualColumns = await nav.evaluate(element =>
      getComputedStyle(element).gridTemplateColumns.trim().split(/\\s+/).length,
    );
    expect(actualColumns, `grid columns at ${width}px`).toBe(columns);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
});

test("Spec 025: venue hub heading comes from the verified host, not a hardcoded pilot name", async ({ page }) => {
  await page.setExtraHTTPHeaders({ Host: "e2eb.rodada.bar" });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/");
  await expect(page.getByText("Other E2E — test only", { exact: true })).toBeVisible();
  await expect(page.getByText("Web E2E — test only")).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Módulos operacionais" }).getByRole("link")).toHaveCount(5);
});
