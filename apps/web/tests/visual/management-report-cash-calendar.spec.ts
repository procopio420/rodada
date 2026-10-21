import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`report cash and calendar ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/management/reports/**", route => route.fulfill({ json: {
    start: "2026-10-08", end: "2026-10-08", generated_at: "2026-10-08T21:00:00Z", totals: {}, daily: [], products: [], payment_methods: [], orders: [],
    cash_shifts: [{ id: "shift-test", cash_point_label: "Caixa de teste com identificação extensa", business_date: "2026-10-08", status: "CLOSED", review_status: "PENDING", expected_at_close_cents: 10000, corrected_expected_cents: 9500, counted_amount_cents: 9000, discrepancy_cents: -1000 }, { id: "shift-open", cash_point_label: "Caixa em aberto de teste", business_date: "2026-10-08", status: "OPEN", review_status: "NONE" }],
  } }));
  await page.goto("/reports");
  await page.getByText("Configurar dia operacional", { exact: true }).click();
  await expect(page.getByLabel("Fuso horário IANA", { exact: true })).toHaveValue("America/Sao_Paulo");
  await stable(page);
  const phase = process.env.RODADA_S3P_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-report-cash-calendar/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const cash = page.getByRole("article", { name: "Caixa de teste com identificação extensa · 2026-10-08", exact: true });
  await expect(cash.locator(".dataRow strong")).toHaveText([/100,00.*95,00/, /90,00.*-.*10,00/]);
  await expect(cash.getByText("Fechado · Revisão pendente", { exact: true })).toBeVisible();
  await expect(page.getByRole("article", { name: "Caixa em aberto de teste · 2026-10-08", exact: true }).locator(".dataRow strong")).toHaveText(["— / —", "— / —"]);
  for (const link of await cash.getByRole("link").all()) expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await expect(page.getByRole("group", { name: "Calendário do estabelecimento", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#report-cash, #report-calendar { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-report-cash-calendar/after-${width}-zoom200.png`, fullPage: true });
  const commands: unknown[] = [];
  await page.route("**/api/pos/management/calendar/", route => { commands.push(route.request().postDataJSON()); return route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Sem permissão para alterar calendário." } }); });
  await page.getByLabel("Hora de corte (0 a 23)").fill("5");
  await page.getByRole("button", { name: "Salvar calendário", exact: true }).focus(); await page.keyboard.press("Enter");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Sem permissão");
  expect(commands).toEqual([{ timezone: "America/Sao_Paulo", cutoff_hour: 5 }]);
  await expect(page.getByText(/Calendário salvo\./)).toHaveCount(0);
});
