import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`refund payment summary ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/tabs/tab-test/", route => route.fulfill({ json: {
    id: "tab-test", state: "OPEN", payments: [
      { id: "partial", method: "CASH", status: "PARTIALLY_REFUNDED", amount_cents: 1200, refunded_cents: 500, refunds: [{ id: "refund-test", amount_cents: 500, status: "CONFIRMED", reason: "Justificativa de teste com identificação extensa para conferir quebra de linha" }] },
      { id: "complete", method: "PIX", status: "REFUNDED", amount_cents: 1000, refunded_cents: 1000, refunds: [] },
    ], refund_required_corrections: [],
  } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test");
  await expect(page.getByText("Restante reembolsável", { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S3H_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-refund-payment/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const group = page.getByRole("group", { name: "Saldo do pagamento", exact: true });
  await expect(group.locator("strong")).toHaveText([/12,00/, /5,00/, /7,00/]);
  await expect(page.getByRole("list", { name: "Histórico de estornos", exact: true }).getByRole("listitem")).toHaveCount(1);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#refund-payment-summary, #refund-history { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-refund-payment/after-${width}-zoom200.png`, fullPage: true });
  await page.getByLabel("Pagamento elegível", { exact: true }).selectOption("complete");
  await expect(group.locator("strong")).toHaveText([/10,00/, /10,00/, /0,00/]);
  await expect(page.getByRole("button", { name: "Confirmar estorno", exact: true })).toBeDisabled();
  expect(writes).toEqual([]);
});
