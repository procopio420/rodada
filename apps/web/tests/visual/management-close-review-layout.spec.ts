import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const close = {
  id: "close-test", business_date: "2026-10-08", version: 1, status: "INCOMPLETE", fingerprint: "a".repeat(64),
  generated_at: "2026-10-09T07:00:00Z", review: null, corrected_cash_delta_cents: 0, post_close_adjustments: [],
  original: {
    financial: { net_sales_cents: 5000 },
    receipts: { paid_cents: 5000, refunds_cents: 500, net_received_cents: 4500, methods: [{ method: "CASH", net_received_cents: 4500 }] },
    cash_shifts: [{ id: "shift-test", label: "Caixa de teste com identificação extensa para conferir leitura", status: "CLOSED", review_status: "PENDING", counted_amount_cents: 4900, discrepancy_cents: -100 }],
    blockers: [{ kind: "CASH_SHIFT", id: "shift-test" }, { kind: "UNRESOLVED_PAYMENT", id: "payment-test" }],
  },
};

for (const width of [360, 390, 430, 1280]) test(`close review values and blockers ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/management/daily-closes/**", route => route.fulfill({ json: { results: [close] } }));
  await page.route("**/api/pos/management/correction-requests/**", route => route.fulfill({ json: { results: [] } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/manage/daily-close");
  await expect(page.getByText("Caixa aberto ou sem revisão", { exact: false })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S3C_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-close-review/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  await page.route("**/api/pos/management/daily-closes/**", route => route.fulfill({ json: { results: [{ ...close, original: { ...close.original, financial: { net_sales_cents: 6000 } } }] } }));
  await page.reload();
  const review = page.getByRole("region", { name: "Revisões imutáveis", exact: true });
  await expect(review.getByRole("group", { name: "Resumo financeiro", exact: true })).toBeVisible();
  await expect(review.getByRole("group", { name: "Resumo financeiro", exact: true }).locator("strong")).toHaveText([/60,00/, /50,00/, /5,00/, /45,00/]);
  await expect(review.getByRole("list", { name: "Bloqueios da revisão", exact: true }).getByRole("listitem")).toHaveCount(2);
  const link = review.getByRole("link", { name: "Revisar este turno →", exact: true });
  await expect(link).toHaveAttribute("href", `/cash?shift=shift-test&from=${encodeURIComponent("/manage/daily-close")}`);
  expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await expect(review.getByRole("button", { name: "Confirmar revisão com PIN" })).toHaveCount(0);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#daily-close-revisions { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-close-review/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});
