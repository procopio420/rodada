import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const policy = { version: 3, service_enabled: true, service_basis_points: 1000, service_max_basis_points: 1500, service_opt_out: true, service_removal_requires_manager: true, service_refundable: true, staff_discount_basis_points: 500, cashier_discount_basis_points: 1000, maximum_discount_basis_points: 2000, allow_post_payment: false, service_treatment: "PASS_THROUGH" };
for (const width of [360, 390, 430, 1280]) test(`pricing policy fields ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  const commands: unknown[] = [];
  await page.route("**/api/pos/pricing/policy/", route => {
    if (route.request().method() === "GET") return route.fulfill({ json: policy });
    commands.push(route.request().postDataJSON());
    return route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Sem permissão para alterar política." } });
  });
  await page.route("**/api/pos/pricing/approvals/", route => route.fulfill({ json: { results: [] } }));
  await page.goto("/manage/pricing");
  await expect(page.getByLabel("Serviço padrão (%)", { exact: true })).toHaveValue("10");
  await stable(page);
  const phase = process.env.RODADA_S3K_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-pricing-policy/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  await expect(page.getByRole("group", { name: "Regras de cobrança", exact: true })).toBeVisible();
  await expect(page.getByRole("group", { name: "Confirmar alteração", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Voltar ao Financeiro", exact: true })).toHaveAttribute("href", "/manage#financeiro");
  await expect(page.getByRole("button", { name: "Salvar política" })).toBeDisabled();
  await page.getByLabel("Serviço padrão (%)", { exact: true }).fill("12.5");
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#pricing-policy { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-pricing-policy/after-${width}-zoom200.png`, fullPage: true });
  await page.getByLabel("PIN da gerência", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Salvar política" }).click();
  await expect(page.getByRole("main").getByRole("status")).toContainText("Sem permissão");
  expect(commands).toHaveLength(1);
  expect(commands[0]).toEqual({ ...policy, version: undefined, expected_version: 3, service_basis_points: 1250 });
});
