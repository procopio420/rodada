import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`revoked management session offers staff login ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await fixture(page);
  await page.route("**/api/realtime/snapshot/", route => route.fulfill({ status: 401, json: { code: "SESSION_REVOKED" } }));
  await page.goto("/manage");
  const link = page.getByRole("alert").getByRole("link", { name: "Entrar novamente", exact: true });
  await expect(link).toHaveAttribute("href", "/staff");
  expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(56);
  await expect(link).toHaveCSS("text-decoration-line", "none");
  await expect(page.getByRole("heading", { name: "Sessão encerrada", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-session-login-${width}.png`, fullPage: true });
  await link.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/staff$/);
});

test("ordinary read error does not claim session ended", async ({ page }) => {
  await fixture(page);
  await page.route("**/api/pos/cash/points/", route => route.fulfill({ status: 500, json: { message: "Não foi possível consultar caixas." } }));
  await page.goto("/manage");
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(page.getByRole("link", { name: "Entrar novamente", exact: true })).toHaveCount(0);
});
