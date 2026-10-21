import { test, expect } from "@playwright/test";
import { fixture } from "./fixtures";
test.beforeEach(async ({ page }) => { await fixture(page); });
test("refund initial read remains loading until resources resolve", async ({ page }) => {
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/pos/tabs/", async route => { await gate; await route.fulfill({ json: { results: [] } }); });
  const writes: string[] = [];
  page.on("request", r => { if (r.url().includes("/api/") && !["GET", "HEAD"].includes(r.method())) writes.push(r.url()); });
  await page.goto("/refunds");
  await expect(page.getByText("Carregando estornos…", { exact: true })).toBeVisible();
  release();
  await expect(page.getByText("Carregando estornos…", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Comanda", { exact: true }).locator("option")).toHaveCount(1);
  expect(writes).toEqual([]);
});
for (const failure of ["network", "server"] as const) test(`refund read failure ${failure}`, async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.route("**/api/pos/tabs/", route => failure === "network" ? route.abort("failed") : route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Consulta de comandas indisponível." } }));
  await page.goto("/refunds");
  await expect(page.getByRole("main").getByRole("alert")).toHaveText(failure === "network" ? "Não foi possível atualizar os estornos. Confira a conexão." : "Consulta de comandas indisponível.");
  await expect(page.getByText("Carregando estornos…", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Comanda", { exact: true }).locator("option")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Confirmar estorno", exact: true })).toHaveCount(0);
  expect(errors).toEqual([]);
});
test("refund initial read only offers cash points with open shifts", async ({ page }) => {
  await page.route("**/api/pos/cash/points/", route => route.fulfill({ json: { results: [
    { id: "cash-closed", label: "Caixa fechado de teste", active_shift: null },
    { id: "cash-open", label: "Caixa aberto de teste", active_shift: { id: "shift-test" } },
  ] } }));
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test");
  const cash = page.getByLabel("Caixa que devolverá o dinheiro", { exact: true });
  await expect(cash).toHaveValue("cash-open");
  await expect(cash.locator("option")).toHaveCount(2);
  await expect(cash.locator('option[value="cash-closed"]')).toHaveCount(0);
});
