import { expect, test } from "@playwright/test";
import { fixture } from "./fixtures";

test("pricing initial read restores exact pending command and preserves lost-response retry", async ({ page }) => {
  await fixture(page);
  const command = { kind: "TAB_DISCOUNT", expected_version: 1, idempotency_key: "pricing-recovery-test", reason_code: "TEST_CORRECTION", value: 125, calculation_type: "FIXED" };
  const preview = { before_payable_cents: 1000, after_payable_cents: 875, after_remaining_cents: 875, approval_required: true };
  await page.addInitScript(({ command, preview }) => sessionStorage.setItem("rodada-pricing:venue-test:operator-test:recovery-tab", JSON.stringify({ command, preview })), { command, preview });
  const bill = { id: "recovery-tab", version: 1, display_label: "Comanda de teste", state: "OPEN", exposure_cents: 1000, charges_cents: 1000, payments_cents: 0, orders: [], payments: [] };
  await page.route("**/api/pos/tabs/", route => route.fulfill({ json: { results: [bill] } }));
  await page.route("**/api/pos/tabs/recovery-tab/", route => route.fulfill({ json: bill }));
  await page.route("**/api/pos/tabs/recovery-tab/pricing/", route => route.fulfill({ json: { version: 1, policy: { service_basis_points: 1000 }, history: [], charges: [] } }));
  const attempts: string[] = [];
  await page.route("**/api/pos/tabs/recovery-tab/pricing/approval-request/", route => {
    attempts.push(route.request().postData()!);
    return attempts.length === 1 ? route.abort() : route.fulfill({ json: { status: "REQUESTED" } });
  });
  await page.goto("/pos");
  await page.getByRole("button", { name: /Comanda de teste/ }).click();
  await expect(page.getByText("Há um ajuste aguardando confirmação. Verifique esta mesma operação.")).toBeVisible();
  await expect(page.getByLabel("Ação", { exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Solicitar aprovação", exact: true }).click();
  await expect(page.getByText("Resposta não confirmada. Tente novamente para verificar o mesmo ajuste.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Solicitar aprovação", exact: true }).click();
  await expect(page.getByText("Solicitação enviada à gerência.")).toBeVisible();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toBe(attempts[0]);
  expect(JSON.parse(attempts[0])).toEqual(command);
  expect(await page.evaluate(() => sessionStorage.getItem("rodada-pricing:venue-test:operator-test:recovery-tab"))).toBeNull();
});

test("pricing initial transport failure is explicit and blocks preview", async ({ page }) => {
  await fixture(page);
  const bill = { id: "failed-tab", version: 1, display_label: "Comanda sem leitura", state: "OPEN", exposure_cents: 1000, orders: [], payments: [] };
  await page.route("**/api/pos/tabs/", route => route.fulfill({ json: { results: [bill] } }));
  await page.route("**/api/pos/tabs/failed-tab/", route => route.fulfill({ json: bill }));
  await page.route("**/api/pos/tabs/failed-tab/pricing/", route => route.abort());
  await page.goto("/pos");
  await page.getByRole("button", { name: /Comanda sem leitura/ }).click();
  await expect(page.getByText("Não foi possível consultar os ajustes. Tente novamente.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Conferir antes de aplicar" })).toBeDisabled();
});
