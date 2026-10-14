import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const paymentId = "00000000-0000-4000-8000-000000000123";
const tabId = "00000000-0000-4000-8000-000000000456";
const origin = "/manage/alerts/00000000-0000-4000-8000-000000000789";
const payment = { id: paymentId, method: "PIX", status: "PARTIALLY_REFUNDED", amount_cents: 1200, refunded_cents: 500,
  refunds: [{ id: "refund-test", amount_cents: 500, status: "CONFIRMED", reason: "Motivo original preservado" }] };
const tab = { id: tabId, display_label: "Comanda histórica", state: "CLOSED", payments: [{ ...payment, id: "another-payment", amount_cents: 9999 }, payment] };

for (const width of [360, 390, 430]) test(`pagamento exato em comanda encerrada fora da lista com foco e retorno ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 }); await fixture(page, "normal", true);
  await page.addInitScript(() => sessionStorage.setItem("rodada.intent.refund.v1", "original-envelope-test"));
  let posts = 0, lists = 0;
  page.on("request", request => { if (request.method() === "POST") posts++; if (new URL(request.url()).pathname === "/api/pos/tabs/") lists++; });
  await page.route(`**/api/pos/payments/${paymentId}/recovery-context/`, route => route.fulfill({ json: { tab_id: tabId, payment_id: paymentId } }));
  await page.route(`**/api/pos/tabs/${tabId}/`, route => route.fulfill({ json: tab }));
  await page.goto(`/manage/payments/${paymentId}?from=${encodeURIComponent(origin)}`);
  await expect(page.getByText("Comanda histórica · Encerrada")).toBeVisible();
  await expect(page.getByText("Pix · Estornado parcialmente")).toBeVisible();
  await expect(page.getByText("R$ 7,00", { exact: true })).toBeVisible();
  await expect(page.getByText("Motivo original preservado", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pagamento original" })).toBeFocused();
  await expect(page.getByRole("link", { name: "Voltar à revisão de origem →" })).toHaveAttribute("href", origin);
  await expect(page.getByRole("button", { name: /Estornar|Cobrar|Conciliar/ })).toHaveCount(0);
  await page.getByText("Identificadores para auditoria", { exact: true }).click();
  await expect(page.getByText(`Pagamento: ${paymentId}`, { exact: true })).toBeVisible();
  expect(posts).toBe(0); expect(lists).toBe(0);
  expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.refund.v1"))).toBe("original-envelope-test");
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/t12b2-payment-${width}.png`, fullPage: true });
});

for (const failure of ["invalid", "forbidden", "missing", "wrong-payment", "wrong-tab", "payment-absent", "session-changed"]) test(`conferência não publica contexto após ${failure}`, async ({ page }) => {
  await fixture(page, "normal", true);
  let resolverReads = 0, authReads = 0, posts = 0;
  page.on("request", request => { if (request.method() === "POST") posts++; });
  await page.route("**/api/auth/me", async route => {
    authReads++;
    if (failure !== "session-changed" || authReads === 1) return route.fallback();
    return route.fulfill({ json: { staff: { id: "operator-test" }, venue: { id: "venue-test" }, session: { id: "different-session" } } });
  });
  await page.route(`**/api/pos/payments/${paymentId}/recovery-context/`, route => {
    resolverReads++;
    if (failure === "forbidden" || failure === "missing") return route.fulfill({ status: failure === "forbidden" ? 403 : 404, json: { code: "CONTEXT_UNAVAILABLE", message: "Contexto indisponível." } });
    return route.fulfill({ json: { tab_id: tabId, payment_id: failure === "wrong-payment" ? "other-payment" : paymentId } });
  });
  await page.route(`**/api/pos/tabs/${tabId}/`, route => route.fulfill({ json: { ...tab, id: failure === "wrong-tab" ? "other-tab" : tabId, payments: failure === "payment-absent" ? [] : tab.payments } }));
  await page.goto(`/manage/payments/${failure === "invalid" ? "invalid" : paymentId}?from=${encodeURIComponent("https://outside.example")}`);
  await expect(page.locator(".notice[role=alert]")).toBeVisible();
  await expect(page.getByText("Comanda histórica · Encerrada")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Voltar à revisão de origem →" })).toHaveAttribute("href", "/manage");
  expect(posts).toBe(0); if (failure === "invalid") expect(resolverReads).toBe(0);
});

test("pagamento pendente e atualização negada nunca parecem recebimento confirmado", async ({ page }) => {
  await fixture(page, "normal", true);
  let reads = 0;
  await page.route(`**/api/pos/payments/${paymentId}/recovery-context/`, route => ++reads === 1
    ? route.fulfill({ json: { tab_id: tabId, payment_id: paymentId } })
    : route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Acesso revogado." } }));
  await page.route(`**/api/pos/tabs/${tabId}/`, route => route.fulfill({ json: { ...tab, payments: [{ ...payment, status: "PENDING", refunded_cents: 0, refunds: [] }] } }));
  await page.goto(`/manage/payments/${paymentId}`);
  await expect(page.getByText("Pix · Pendente", { exact: true })).toBeVisible();
  await expect(page.getByText("Não confirmado", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Consultar novamente" }).click();
  await expect(page.getByText("Acesso revogado.", { exact: true })).toBeVisible();
  await expect(page.getByText("Pix · Pendente", { exact: true })).toHaveCount(0);
});
