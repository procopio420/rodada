import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const id = "00000000-0000-4000-8000-000000000789";
const origin = "/manage/alerts/00000000-0000-4000-8000-000000000123";
const original = { id, cash_point_id: "cash-test", business_date: "2026-10-07", status: "CLOSED", review_status: "PENDING", version: 3,
  expected_at_close_cents: 5000, counted_amount_cents: 4900, discrepancy_cents: -100, movements: [] };

for (const width of [360, 390, 430]) test(`contexto seleciona turno histórico fora da primeira página com retorno em ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 }); await fixture(page, "normal", true);
  let posts = 0;
  page.on("request", request => { if (request.method() === "POST") posts++; });
  await page.route(`**/api/pos/cash/shifts/${id}/`, route => route.fulfill({ json: original }));
  await page.route("**/api/pos/cash/shifts/history/**", route => route.fulfill({ json: { results: [], next_offset: 100 } }));
  await page.goto(`/cash?shift=${id}&from=${encodeURIComponent(origin)}`);
  await expect(page.getByText("Turno original carregado. Confira o histórico antes de decidir.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Turno da exceção" })).toBeFocused();
  await expect(page.getByLabel("Selecionar turno atual ou fechamento antigo")).toHaveValue(id);
  await expect(page.getByLabel("Ponto de caixa")).toHaveValue("cash-test");
  await expect(page.getByRole("link", { name: "Voltar à revisão de origem →" })).toHaveAttribute("href", origin);
  expect(posts).toBe(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/t12b1-cash-${width}.png`, fullPage: true });
});

for (const failure of ["invalid", "forbidden", "missing", "wrong-id", "wrong-point", "unlisted-point"]) test(`contexto de caixa não seleciona alternativa após ${failure}`, async ({ page }) => {
  await fixture(page, "normal", true);
  let reads = 0, posts = 0;
  page.on("request", request => { if (request.method() === "POST") posts++; });
  await page.route(`**/api/pos/cash/shifts/${id}/`, route => {
    reads++;
    if (failure === "forbidden" || failure === "missing") return route.fulfill({ status: failure === "forbidden" ? 403 : 404, json: { code: "CONTEXT_UNAVAILABLE", message: "Contexto indisponível." } });
    return route.fulfill({ json: { ...original, ...(failure === "wrong-id" ? { id: "different-id" } : {}),
      ...(failure === "unlisted-point" || failure === "wrong-point" && reads > 1 ? { cash_point_id: "other-point" } : {}) } });
  });
  await page.goto(`/cash?shift=${failure === "invalid" ? "invalid" : id}&from=${encodeURIComponent("https://outside.example")}`);
  await expect(page.getByRole("alert").filter({ hasText: "CASH_CONTEXT_" })).toBeVisible();
  if (failure === "wrong-point") await expect(page.getByLabel("Selecionar turno atual ou fechamento antigo")).toHaveValue("");
  else await expect(page.getByLabel("Selecionar turno atual ou fechamento antigo")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Voltar à revisão de origem →" })).toHaveAttribute("href", "/manage");
  await expect(page.getByText("Turno original carregado. Confira o histórico antes de decidir.")).toHaveCount(0);
  expect(posts).toBe(0);
  if (failure === "invalid") expect(reads).toBe(0);
});
