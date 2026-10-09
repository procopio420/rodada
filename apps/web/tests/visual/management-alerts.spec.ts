import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
const id = "80606137-578d-40f6-94c4-c11f7931a004";
const sourceId = "72543d61-4a0a-466c-a1a2-c34482e8ba00";
const base = { id, rule_key: "FULFILLMENT_SLA", rule_version: 1, status: "ACTIVE", severity: "DANGER",
  source: { target: "FULFILLMENT_ITEM", id: sourceId, station: "KITCHEN", state: "READY", age_seconds: 1260, source: "CANONICAL_TIMESTAMP" } };
test("manager canonical alert at mobile width: acknowledgement preserves condition", async ({ page }) => {
  await fixture(page);
  let status = "ACTIVE";
  await page.route("**/api/pos/management/alerts/", route => route.fulfill({ json: { results: [{ ...base, status }] } }));
  await page.route(`**/api/pos/management/alerts/${id}/`, route => { status = "ACKNOWLEDGED"; return route.fulfill({ json: { ...base, status } }); });
  await page.goto("/manage");
  await expect(page.getByText("Produção acima do SLA")).toBeVisible();
  await expect(page.getByText("Crítico · Cozinha · 21 min nesta etapa")).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir contexto →" })).toHaveAttribute("href", `/manage/alerts/${id}`);
  await page.getByRole("button", { name: "Registrar ciência" }).click();
  await expect(page.getByText("Ciência registrada · condição continua ativa")).toBeVisible();
  await layoutAndA11y(page);
});
test("resolved alert keeps exact source reference and provenance history", async ({ page }) => {
  await fixture(page);
  await page.route(`**/api/pos/management/alerts/${id}/`, route => route.fulfill({ json: { ...base, status: "RESOLVED", history: [
    { kind: "ACTIVATED", occurred_at: "2026-10-09T20:00:00Z", metadata: {} },
    { kind: "RESOLVED", occurred_at: "2026-10-09T20:10:00Z", metadata: { reason: "CANONICAL_CONDITION_CLEARED" } },
  ] } }));
  await page.goto(`/manage/alerts/${id}`);
  await expect(page.getByText("Resolvido pela condição canônica. Este alerta permanece no histórico.")).toBeVisible();
  await expect(page.getByText(`Contexto: Item do pedido · ${sourceId}`)).toBeVisible();
  await expect(page.getByText("A condição original deixou de exigir ação.", { exact: true })).toBeVisible();
  await layoutAndA11y(page);
});

test("typed alert settings do not activate a failed or conflicted save", async ({ page }) => {
  await fixture(page);
  let version = 1;
  const policy = () => ({ version, fulfillment_warning_seconds: 600, fulfillment_danger_seconds: 1200, payment_pending_seconds: 300 });
  await page.route("**/api/pos/management/alert-policy/", route => {
    if (route.request().method() === "PATCH") { version = 2; return route.fulfill({ status: 409, json: { code: "STALE_VERSION", current: policy() } }); }
    return route.fulfill({ json: policy() });
  });
  await page.route("**/api/auth/reauthenticate", route => route.fulfill({ json: { status: "OK" } }));
  await page.goto("/manage/alerts/settings");
  await expect(page.getByLabel("Produção: atenção após (segundos)")).toHaveValue("600");
  await page.getByLabel("Produção: atenção após (segundos)").fill("300");
  await page.getByLabel("Confirme seu PIN").fill("1234");
  await page.getByRole("button", { name: "Salvar política" }).click();
  await expect(page.getByText("Outra pessoa alterou a política. Estado atual carregado; revise antes de salvar novamente.")).toBeVisible();
  await expect(page.getByLabel("Produção: atenção após (segundos)")).toHaveValue("600");
  await expect(page.getByLabel("Confirme seu PIN")).toHaveValue("");
  await layoutAndA11y(page);
});
