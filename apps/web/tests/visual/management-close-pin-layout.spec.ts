import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`daily close PIN recovery ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  const commands: unknown[] = [];
  await page.route("**/api/pos/management/daily-closes/**", route => {
    if (route.request().method() === "GET") return route.fulfill({ json: { results: [] } });
    commands.push(route.request().postDataJSON());
    return route.fulfill({ status: 403, json: { code: "REAUTH_REQUIRED", message: "Confirme o PIN." } });
  });
  await page.route("**/api/pos/management/correction-requests/**", route => route.fulfill({ json: { results: [] } }));
  await page.goto("/manage/daily-close");
  await page.getByRole("button", { name: "Gerar revisão do dia", exact: true }).click();
  await expect(page.getByLabel("Seu PIN", { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S3F_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-close-pin/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const region = page.getByRole("region", { name: "Confirmar PIN do gerente", exact: true });
  await expect(region.getByRole("group", { name: "Confirmar identidade", exact: true })).toBeVisible();
  await expect(region.getByRole("button", { name: "Confirmar e continuar" })).toBeDisabled();
  await expect(page.getByLabel("Seu PIN")).toHaveAttribute("type", "password");
  await expect(page.getByRole("button", { name: "Gerar revisão do dia", exact: true })).toBeDisabled();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#daily-close-reauth { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-close-pin/after-${width}-zoom200.png`, fullPage: true });
  const cancel = region.getByRole("button", { name: "Cancelar", exact: true });
  expect((await cancel.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await cancel.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Seu PIN")).toHaveCount(0);
  expect(commands).toHaveLength(1);
  expect(commands[0]).toMatchObject({ business_date: "2026-10-08", idempotency_key: expect.any(String) });
  await expect(page.getByRole("button", { name: "Gerar revisão do dia", exact: true })).toBeEnabled();
});
