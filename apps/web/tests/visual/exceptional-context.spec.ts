import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
const itemId = "00000000-0000-4000-8000-000000000123", correctionId = "00000000-0000-4000-8000-000000000234";
const tabId = "00000000-0000-4000-8000-000000000345", paymentId = "00000000-0000-4000-8000-000000000456";
const item = { id: itemId, product_name: "Item original", state: "CANCELLED", quantity: 0, original_quantity: 2, original_line_total_cents: 2400 };
const tab = { id: tabId, display_label: "Comanda histórica", state: "CLOSED", orders: [{ items: [{ ...item, id: "another-item", product_name: "Outro item" }, item] }],
  payments: [{ id: paymentId, method: "PIX", status: "REFUNDED", amount_cents: 2400, refunded_cents: 2400 }], refund_required_corrections: [] };
const target = { tab_id: tabId, order_item_id: itemId, correction_id: correctionId, payment_id: paymentId, correction_status: "APPLIED" };

test("estornos liga a correção selecionada ao pagamento original", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/pos/tabs/tab-test/", route => route.fulfill({ json: { ...tab, id: "tab-test", state: "OPEN",
    payments: [{ ...tab.payments[0], status: "CONFIRMED", refunded_cents: 0, refunds: [] }],
    refund_required_corrections: [{ id: correctionId, order_item_id: itemId, item_name: "Item original", reason_code: "WRONG_ITEM_ENTERED", refund_required_cents: 2400 }],
  } }));
  await page.goto("/refunds"); await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test");
  await expect(page.getByRole("link", { name: "Conferir correção original →" })).toHaveAttribute("href", `/manage/corrections/${correctionId}?payment=${paymentId}&from=${encodeURIComponent("/refunds")}`);
});
for (const kind of ["items", "corrections"]) for (const width of [360, 390, 430]) test(`${kind} contexto original histórico sem mutation ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 }); await fixture(page, "normal", true);
  await page.addInitScript(() => sessionStorage.setItem("rodada.intent.refund.v1", "preserved-envelope"));
  let posts = 0; page.on("request", request => { if (request.method() === "POST") posts++; });
  const id = kind === "items" ? itemId : correctionId;
  await page.route("**/api/pos/**/recovery-context/**", route => route.fulfill({ json: kind === "items" ? { tab_id: tabId, order_item_id: itemId } : target }));
  await page.route(`**/api/pos/tabs/${tabId}/`, route => route.fulfill({ json: tab }));
  await page.goto(`/manage/${kind}/${id}?payment=${paymentId}&from=${encodeURIComponent("/refunds")}`);
  await expect(page.getByRole("heading", { name: "Item original", exact: true })).toBeVisible();
  await expect(page.getByText("Comanda histórica · Encerrada")).toBeVisible();
  await expect(page.getByText("Cancelado", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Registro original" })).toBeFocused();
  await expect(page.getByText("Outro item", { exact: true })).toHaveCount(0);
  if (kind === "corrections") { await expect(page.getByText("Correção: Aplicada", { exact: true })).toBeVisible(); await expect(page.getByText("Pix · Estornado", { exact: true })).toBeVisible(); }
  await expect(page.getByRole("link", { name: "Voltar à revisão de origem →" })).toHaveAttribute("href", "/refunds");
  await expect(page.getByRole("button", { name: /Aprovar|Estornar|Cancelar/ })).toHaveCount(0);
  expect(posts).toBe(0); await layoutAndA11y(page);
  expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.refund.v1"))).toBe("preserved-envelope");
  await page.screenshot({ path: `../../visual-artifacts/spec026/t12b3-${kind}-${width}.png`, fullPage: true });
});
for (const failure of ["invalid", "missing-payment", "forbidden", "missing", "wrong-target", "wrong-tab", "missing-item", "missing-linked-payment", "session"]) test(`correção não publica alvo após ${failure}`, async ({ page }) => {
  await fixture(page, "normal", true); let authReads = 0, posts = 0;
  page.on("request", request => { if (request.method() === "POST") posts++; });
  await page.route("**/api/auth/me", route => ++authReads > 1 && failure === "session" ? route.fulfill({ json: { staff: { id: "operator-test" }, venue: { id: "venue-test" }, session: { id: "changed" } } }) : route.fallback());
  await page.route("**/api/pos/**/recovery-context/**", route => failure === "forbidden" || failure === "missing"
    ? route.fulfill({ status: failure === "forbidden" ? 403 : 404, json: { code: "UNAVAILABLE", message: "Contexto indisponível." } })
    : route.fulfill({ json: { ...target, correction_id: failure === "wrong-target" ? itemId : correctionId } }));
  await page.route(`**/api/pos/tabs/${tabId}/`, route => route.fulfill({ json: { ...tab, id: failure === "wrong-tab" ? itemId : tabId,
    orders: failure === "missing-item" ? [] : tab.orders, payments: failure === "missing-linked-payment" ? [] : tab.payments } }));
  await page.goto(`/manage/corrections/${failure === "invalid" ? "invalid" : correctionId}?payment=${failure === "missing-payment" ? "" : paymentId}&from=${encodeURIComponent("https://outside.example")}`);
  await expect(page.locator(".notice[role=alert]")).toBeVisible();
  await expect(page.getByText("Comanda histórica · Encerrada")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Voltar à revisão de origem →" })).toHaveAttribute("href", "/manage"); expect(posts).toBe(0);
});
