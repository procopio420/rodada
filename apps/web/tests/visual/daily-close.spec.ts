import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const closeId = "00000000-0000-4000-8000-000000000123";
const requestId = "00000000-0000-4000-8000-000000000456";
const shiftId = "00000000-0000-4000-8000-000000000789";
const snapshot = {
  schema_version: 1, business_date: "2026-10-08",
  calendar: { timezone: "America/Sao_Paulo", lower: "2026-10-08T04:00:00-03:00", upper: "2026-10-09T04:00:00-03:00" },
  financial: { gross_cents: 6000, adjustments_cents: -1000, net_sales_cents: 5000 },
  receipts: { paid_cents: 5000, refunds_cents: 500, net_received_cents: 4500,
    methods: [{ method: "CASH", paid_cents: 5000, refunds_cents: 500, net_received_cents: 4500 }] },
  cash_shifts: [{ id: shiftId, label: "Caixa principal", status: "CLOSED", review_status: "REVIEWED",
    counted_amount_cents: 4900, expected_at_close_cents: 5000, discrepancy_cents: -100 }],
  blockers: [],
  facts: { movement_ids: [], payment_ids: [], refund_ids: [] },
};
const closed = {
  id: closeId, version: 1, business_date: "2026-10-08", status: "REVIEWED", generated_at: "2026-10-09T07:01:00Z",
  fingerprint: "a".repeat(64), original: snapshot,
  review: { reviewed_at: "2026-10-09T07:02:00Z", reviewed_by: "operator-test", reason: "Conferência verificada" },
  corrected_cash_delta_cents: 0, post_close_adjustments: [],
};
const correction = {
  id: requestId, shift_id: shiftId, cash_point_label: "Caixa principal", amount_cents: -100,
  reason: "Sangria omitida", status: "PENDING", version: 1,
  requested_by: "other-operator", requested_at: "2026-10-09T08:00:00Z",
  decided_by: null, decision_reason: "", movement_id: null,
};

test("gerência mostra snapshot imutável e só confirma correção após PIN e aprovação", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await fixture(page);
  let approvals = 0;
  let reauthenticated = false;
  await page.route("**/api/pos/management/daily-closes/**", route => route.fulfill({ json: { results: [closed] } }));
  await page.route("**/api/pos/management/correction-requests/**", route => route.fulfill({ json: { results: [correction] } }));
  await page.route("**/api/pos/cash/correction-requests/*/decision/**", route => {
    approvals++;
    if (!reauthenticated) return route.fulfill({ status: 403, json: { code: "REAUTH_REQUIRED", message: "Confirme seu PIN." } });
    return route.fulfill({ json: { ...correction, status: "APPROVED", version: 2, movement_id: "movement-test" } });
  });
  await page.route("**/api/auth/reauthenticate", route => {
    reauthenticated = true;
    return route.fulfill({ json: { status: "OK" } });
  });
  await page.goto("/manage/daily-close");
  await expect(page.getByRole("heading", { name: "Fechamento diário" })).toBeVisible();
  await expect(page.getByText("Conferência verificada")).toBeVisible();
  await expect(page.getByText("Sangria omitida")).toBeVisible();
  await expect(page.getByText("R$ 45,00").first()).toBeVisible();
  await expect(page.getByText("R$ 49,00")).toBeVisible();
  await page.getByLabel("Motivo da decisão").fill("Comprovante validado");
  await page.getByRole("button", { name: "Aprovar", exact: true }).click();
  await expect(page.getByLabel("Seu PIN")).toBeVisible();
  expect(approvals).toBe(1);
  await page.getByLabel("Seu PIN").fill("2468");
  await page.getByRole("button", { name: "Confirmar e continuar" }).click();
  await expect(page.getByText(/Correção aprovada: novo movimento auditado/)).toBeVisible();
  expect(approvals).toBe(2);
  await layoutAndA11y(page);
});
