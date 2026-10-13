import { expect, test } from "@playwright/test";
import { fixture } from "./fixtures";

test("Production region navigation stays available during a pending mutation", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 }); await fixture(page, "normal", true);
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  let attempts = 0;
  await page.route("**/api/pos/catalog/products/fries/availability/", async route => {
    attempts++; await pending; await route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Sem autorização" } });
  });
  await page.goto("/kitchen");
  const nav = page.getByRole("navigation", { name: "Regiões da produção" });
  await nav.getByRole("button", { name: /^Disponibilidade/ }).click();
  await page.getByRole("button", { name: "Indisponibilizar Fritas", exact: true }).click();
  await expect.poll(() => attempts).toBe(1);
  await nav.getByRole("button", { name: /^Prontos/ }).click(); await expect(page.getByRole("region", { name: "Pronto para retirada" })).toBeFocused();
  await nav.getByRole("button", { name: /^Fila/ }).click(); await expect(page.getByRole("region", { name: "Fila de pedidos" })).toBeFocused();
  await expect(page.getByRole("button", { name: /^Pronto:/ })).toBeDisabled();
  await nav.getByRole("button", { name: /^Disponibilidade/ }).click();
  await expect(page.getByRole("button", { name: "Indisponibilizar Omelete", exact: true })).toBeDisabled();
  expect(attempts).toBe(1); release();
  await expect(page.getByRole("alert").filter({ hasText: "CAPABILITY_REQUIRED" })).toBeVisible();
});
