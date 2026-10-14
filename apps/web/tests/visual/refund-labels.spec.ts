import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const width of [360, 390, 430]) test(`estornos traduzem estados canônicos e preservam histórico em ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await fixture(page, "normal", true);
  const methods = ["CASH", "PIX", "CARD", "TAP_TO_PAY", "EXTERNAL_TERMINAL", "CARD_ONLINE", "OTHER", "FUTURE_METHOD"];
  const states = ["CREATED", "PENDING", "PROCESSING", "AUTHORIZED", "CONFIRMATION_PENDING", "CONFIRMED", "EXPIRED", "FAILED", "CANCELLED", "PARTIALLY_REFUNDED", "REFUNDED", "FUTURE_STATE"];
  let posts = 0;
  await page.route("**/api/pos/tabs/tab-test/", route => {
    if (route.request().method() !== "GET") posts++;
    return route.fulfill({ json: { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 0,
      payments: states.map((status, index) => ({ id: `payment-${index}`, method: methods[index % methods.length], status, amount_cents: 1200, refunded_cents: 500,
        refunds: [{ id: `refund-${index}`, amount_cents: 500, status: "CONFIRMED", reason: "Motivo preservado" }] })), refund_required_corrections: [] } });
  });
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test");
  const options = page.getByLabel("Pagamento elegível").locator("option");
  const labels = await options.allTextContents();
  expect(labels).toHaveLength(states.length);
  expect(labels[0]).toContain("Dinheiro · Criado");
  expect(labels[4]).toContain("Maquininha externa · Confirmação pendente");
  expect(labels[5]).toContain("Cartão online · Confirmado");
  expect(labels[7]).toContain("Método não reconhecido · Falhou");
  expect(labels[9]).toContain("Estornado parcialmente");
  expect(labels[10]).toContain("Estornado");
  expect(labels[11]).toContain("Estado não reconhecido");
  expect(labels.some(label => /CONFIRMED|REFUNDED|FUTURE_|CASH/.test(label))).toBe(false);
  await expect(page.getByText(/Confirmado · Motivo preservado/)).toBeVisible();
  await expect(page.getByText("R$ 7,00", { exact: true })).toBeVisible();
  expect(posts).toBe(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/t12a-refund-labels-${width}.png`, fullPage: true });
});
