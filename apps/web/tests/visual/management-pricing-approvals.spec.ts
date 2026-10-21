import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`pricing approval requests ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/pricing/policy/", route => route.fulfill({ json: { version: 1, service_enabled: true, service_basis_points: 1000, service_max_basis_points: 1500, service_opt_out: true, service_removal_requires_manager: true, service_refundable: true, staff_discount_basis_points: 0, cashier_discount_basis_points: 500, maximum_discount_basis_points: 1000, allow_post_payment: false, service_treatment: "PASS_THROUGH" } }));
  await page.route("**/api/pos/pricing/approvals/", route => route.fulfill({ json: { results: [
    { id: "request-test", label: "Comanda de teste com identificação extensa", requester: "Operador de teste", command: { kind: "TAB_DISCOUNT", reason_code: "Motivo de teste com descrição extensa" }, preview: { before_payable_cents: 11000, after_payable_cents: 9900 } },
    { id: "request-other", label: "", requester: "Operador de teste", command: { kind: "TAB_DISCOUNT", reason_code: "Motivo de teste" }, preview: { before_payable_cents: 5000, after_payable_cents: 4500 } },
  ] } }));
  await page.goto("/manage/pricing");
  await expect(page.getByRole("button", { name: "Aprovar com PIN", exact: true })).toHaveCount(2);
  await stable(page);
  const phase = process.env.RODADA_S3L_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-pricing-approvals/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const request = page.getByRole("article", { name: "Comanda de teste com identificação extensa", exact: true });
  await expect(page.getByRole("article", { name: "Comanda", exact: true })).toBeVisible();
  await expect(request.getByRole("group", { name: "Valores da solicitação", exact: true }).locator("strong")).toHaveText(["R$ 110.00", "R$ 99.00"]);
  await expect(request.getByRole("button")).toBeDisabled();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#pricing-approvals { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-pricing-approvals/after-${width}-zoom200.png`, fullPage: true });
  const commands: unknown[] = [];
  await page.route("**/api/pos/pricing/approvals/request-test/approve/", route => { commands.push(route.request().postDataJSON()); return route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Sem permissão para aprovar." } }); });
  await page.getByLabel("PIN da gerência", { exact: true }).fill("2468");
  await request.getByRole("button").focus(); await page.keyboard.press("Enter");
  await expect(page.getByRole("main").getByRole("status")).toContainText("Sem permissão");
  expect(commands).toEqual([{}]);
  await expect(page.getByLabel("PIN da gerência", { exact: true })).toHaveValue("");
});
