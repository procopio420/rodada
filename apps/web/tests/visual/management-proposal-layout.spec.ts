import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`correction proposals readable ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/management/daily-closes/**", route => route.fulfill({ json: { results: [] } }));
  await page.route("**/api/pos/management/correction-requests/**", route => route.fulfill({ json: { results: ["PENDING", "PENDING", "APPROVED", "REJECTED"].map((status, i) => ({
    id: `proposal-${i}`, cash_point_label: `Caixa de teste ${i} com identificação extensa`, amount_cents: i ? 200 : -100, status,
    reason: "Justificativa de teste com descrição extensa para conferir leitura e quebra de linha", requested_at: "2026-10-09T08:00:00Z",
    requested_by: i === 1 ? "operator-test" : "other-operator", decision_reason: status === "REJECTED" ? "Rejeição de teste" : "Conferência de teste", movement_id: status === "APPROVED" ? "movement-test" : null,
  })) } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/manage/daily-close");
  await expect(page.getByText("Pendentes (2)", { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S3E_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-proposals/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  await expect(page.getByRole("article")).toHaveCount(4);
  const first = page.getByRole("article", { name: "Caixa de teste 0 com identificação extensa", exact: true });
  const own = page.getByRole("article", { name: "Caixa de teste 1 com identificação extensa", exact: true });
  await expect(first.getByRole("button", { name: "Aprovar", exact: true })).toBeDisabled();
  await expect(own.getByRole("button")).toHaveCount(0);
  for (const i of [2, 3]) await expect(page.getByRole("article", { name: `Caixa de teste ${i} com identificação extensa`, exact: true }).getByRole("button")).toHaveCount(0);
  await first.getByLabel("Motivo da decisão").fill("Conferência de teste");
  for (const name of ["Aprovar", "Rejeitar"]) expect((await first.getByRole("button", { name, exact: true }).boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "[data-correction-proposals] { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-proposals/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});
