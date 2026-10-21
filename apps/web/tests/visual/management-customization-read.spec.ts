import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const failure of ["network", "server"] as const) test(`customization initial read ${failure}`, async ({ page }) => {
  await fixture(page);
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.route("**/api/pos/catalog/products/?include_inactive=true", route => failure === "network" ? route.abort("failed") : route.fulfill({ status: 500, json: { code: "CATALOG_UNAVAILABLE", message: "Consulta do catálogo indisponível." } }));
  await page.goto("/manage/catalog");
  await expect(page.getByRole("main").getByRole("alert")).toHaveText(failure === "network" ? "Não foi possível carregar o catálogo. Confira a conexão e atualize a página." : "Consulta do catálogo indisponível.");
  await expect(page.getByLabel("Produto", { exact: true }).locator("option")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Salvar configuração", exact: true })).toHaveCount(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-catalog-read/after-${failure}.png`, fullPage: true });
  expect(errors).toEqual([]);
  expect(writes).toEqual([]);
});
