import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const historyTab = {
  id: "history-fixture", display_label: "Conta encerrada", state: "CLOSED", last_table_label: "01",
  exposure_cents: 0, original_subtotal_cents: 1600, charges_cents: 1600, discounts_cents: 0,
  courtesy_cents: 0, corrections_cents: 0, service_charge_cents: 0, payable_cents: 1600,
  payments_cents: 1600, refunds_cents: 0,
  orders: [{ id: "order", items: [{ id: "item", product_name: "Item do catálogo", quantity: 2, line_total_cents: 1600, state: "DELIVERED" }] }],
  payments: [{ id: "payment", method: "CASH", status: "CONFIRMED", amount_cents: 1600 }],
};

test("Management cancelled history preserves items without a paid label", async ({ page }) => {
  await fixture(page, "normal", true);
  const cancelled = { ...historyTab, display_label: "Conta cancelada", state: "CANCELLED", payable_cents: 0,
    payments_cents: 0, payments: [], corrections_cents: -1600,
    orders: [{ id: "order", items: [{ ...historyTab.orders[0].items[0], state: "CANCELLED" }] }],
  };
  await page.route("**/api/pos/tabs/**", route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/history-fixture/")) return route.fulfill({ json: cancelled });
    if (url.searchParams.has("history_day")) return route.fulfill({ json: { results: [cancelled], history_business_date: "2026-10-17", next_offset: null } });
    return route.fallback();
  });
  await page.goto("/manage");
  await page.getByRole("button", { name: "Histórico de comandas", exact: true }).click();
  const dialog = page.getByRole("dialog");
  const row = dialog.getByRole("button", { name: /Conta cancelada/ });
  await expect(row).toContainText("Cancelada");
  await row.click();
  await expect(dialog.getByText(/2× Item do catálogo · Cancelado/)).toBeVisible();
  await expect(dialog.getByText("Sem pagamentos registrados.")).toBeVisible();
  await expect(dialog.getByText("Paga", { exact: true })).toHaveCount(0);
  await layoutAndA11y(page);
});

for (const [width, fontPercent] of [[360, 100], [390, 100], [430, 100], [1280, 100], [360, 200]]) test(`Management history read-only popup ${width} font${fontPercent}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await fixture(page, "normal", true);
  let historyReads = 0; let writes = 0;
  page.on("request", request => { if (request.url().includes("/api/") && request.method() !== "GET") writes++; });
  await page.route("**/api/pos/tabs/**", route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/history-fixture/")) return route.fulfill({ json: historyTab });
    if (!url.searchParams.has("history_day")) return route.fallback();
    historyReads++;
    return route.fulfill({ json: { results: [historyTab], history_business_date: "2026-10-17", next_offset: null } });
  });
  await page.goto("/manage");
  if (fontPercent === 200) await page.addStyleTag({ content: "html { font-size: 200%; }" });
  const trigger = page.getByRole("button", { name: "Histórico de comandas", exact: true });
  await expect(trigger).toBeVisible(); expect(historyReads).toBe(0);
  await trigger.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("button", { name: /Conta encerrada/ })).toBeVisible();
  await expect(dialog.getByLabel("Dia operacional")).toHaveValue("2026-10-17");
  await layoutAndA11y(page);
  await page.screenshot({ path: `test-results/management-history-list-${width}-font${fontPercent}.png` });
  await dialog.getByRole("button", { name: /Conta encerrada/ }).click();
  await expect(dialog.getByRole("heading", { name: "Detalhes da comanda", exact: true })).toBeVisible();
  await expect(dialog.getByText("2× Item do catálogo")).toBeVisible();
  await expect(dialog.getByText("Dinheiro · Confirmado")).toBeVisible();
  await expect(dialog.getByText("Pagamento confirmado.")).toBeVisible();
  await expect(dialog.getByText("Total da conta", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Saldo restante", { exact: true })).toHaveCount(0);
  await expect(dialog.getByText("Total a pagar", { exact: true })).toHaveCount(0);
  await expect(dialog.getByRole("button", { name: /Pagar|Reabrir|Corrigir|Cancelar/ })).toHaveCount(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `test-results/management-history-detail-${width}-font${fontPercent}.png` });
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(dialog.getByRole("heading", { name: "Histórico de comandas", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0); await expect(trigger).toBeFocused();
  expect(writes).toBe(0);
});

test("Management history date search pagination error retry and empty", async ({ page }) => {
  await fixture(page, "normal", true);
  const reads: string[] = []; let fail = true;
  await page.route("**/api/pos/tabs/**", route => {
    const url = new URL(route.request().url());
    if (!url.searchParams.has("history_day")) return route.fallback();
    reads.push(url.search);
    if (fail) { fail = false; return route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Consulta indisponível" } }); }
    const offset = Number(url.searchParams.get("offset"));
    return route.fulfill({ json: { results: offset || url.searchParams.get("q") ? [] : [historyTab], history_business_date: "2026-10-16", next_offset: offset ? null : 200 } });
  });
  await page.goto("/manage"); await page.getByRole("button", { name: "Histórico de comandas", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("alert")).toContainText("Consulta indisponível");
  await dialog.getByRole("button", { name: "Tentar novamente" }).click();
  await dialog.getByRole("button", { name: "Próxima página" }).click();
  await expect(dialog.getByText("Nenhuma comanda encerrada para esta consulta.")).toBeVisible();
  expect(reads.at(-1)).toContain("history_day=2026-10-16"); expect(reads.at(-1)).toContain("offset=200");
  await dialog.getByLabel("Dia operacional").fill("2026-10-15");
  await dialog.getByLabel("Buscar comanda").fill("mesa");
  await dialog.getByRole("button", { name: "Consultar", exact: true }).click();
  await expect.poll(() => reads.at(-1)).toContain("history_day=2026-10-15");
  expect(reads.at(-1)).toContain("q=mesa"); expect(reads.at(-1)).toContain("offset=0");
});

test("Management history invalidates pending read on close and reopen", async ({ page }) => {
  await fixture(page, "normal", true);
  let release: (() => void) | undefined; let reads = 0;
  await page.route("**/api/pos/tabs/**", async route => {
    const url = new URL(route.request().url());
    if (!url.searchParams.has("history_day")) return route.fallback();
    const read = ++reads;
    if (read === 1) await new Promise<void>(resolve => { release = resolve; });
    try { await route.fulfill({ json: { results: read === 1 ? [] : [historyTab], history_business_date: "2026-10-17", next_offset: null } }); } catch { /* Closed popup aborts its old read. */ }
  });
  await page.goto("/manage"); const trigger = page.getByRole("button", { name: "Histórico de comandas", exact: true });
  await trigger.click(); await expect(page.getByRole("status").filter({ hasText: "Carregando histórico…" })).toBeVisible();
  await page.keyboard.press("Escape"); await trigger.click();
  await expect(page.getByRole("dialog").getByRole("button", { name: /Conta encerrada/ })).toBeVisible();
  release?.();
  await expect(page.getByRole("dialog").getByRole("button", { name: /Conta encerrada/ })).toBeVisible();
});

test("Management history shows transferred responsibility", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/pos/tabs/**", route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/history-fixture/")) return route.fulfill({ json: { ...historyTab, payments: [], payments_cents: 0, transfers_cents: -1600 } });
    if (!url.searchParams.has("history_day")) return route.fallback();
    return route.fulfill({ json: { results: [historyTab], history_business_date: "2026-10-17", next_offset: null } });
  });
  await page.goto("/manage"); await page.getByRole("button", { name: "Histórico de comandas", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: /Conta encerrada/ }).click();
  await expect(page.getByRole("dialog").getByText("Responsabilidade transferida").locator("..")).toContainText("-R$ 16,00");
});

test("Management history closes and clears when session is revoked", async ({ page }) => {
  await fixture(page, "normal", true);
  let revoked = false;
  await page.route("**/api/realtime/stream/**", route => revoked
    ? route.fulfill({ status: 401, json: { code: "AUTH_REQUIRED", message: "Sessão encerrada" } }) : route.fallback());
  await page.route("**/api/pos/tabs/**", route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/history-fixture/")) return route.fulfill({ json: historyTab });
    if (!url.searchParams.has("history_day")) return route.fallback();
    return route.fulfill({ json: { results: [historyTab], history_business_date: "2026-10-17", next_offset: null } });
  });
  await page.goto("/manage"); const trigger = page.getByRole("button", { name: "Histórico de comandas", exact: true });
  await trigger.click(); await page.getByRole("dialog").getByRole("button", { name: /Conta encerrada/ }).click();
  await expect(page.getByRole("dialog").getByText("Dinheiro · Confirmado")).toBeVisible();
  revoked = true;
  await page.evaluate(() => window.dispatchEvent(new Event("online")));
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(trigger).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Sessão encerrada", exact: true })).toBeVisible();
  await expect(page.getByRole("alert").getByRole("link", { name: "Entrar novamente", exact: true })).toHaveAttribute("href", "/staff");
});

for (const scenario of ["transfer", "pending", "courtesy", "simulated", "refunded", "stale"] as const) test(`Management statement payment label ${scenario}`, async ({ page }) => {
  await fixture(page, "normal", true);
  const detail = { ...historyTab, payments: historyTab.payments.map(payment => ({ ...payment, simulated: scenario === "simulated" })), transfers_cents: 0, service_assessment_stale: scenario === "stale" };
  if (scenario === "transfer" || scenario === "courtesy") { detail.payments = []; detail.payments_cents = 0; }
  if (scenario === "transfer") detail.transfers_cents = -1600;
  if (scenario === "courtesy") { detail.payable_cents = 0; detail.courtesy_cents = 1600; }
  if (scenario === "pending") { detail.payments[0].status = "PENDING"; detail.payments_cents = 0; }
  if (scenario === "refunded") { detail.payments[0].status = "REFUNDED"; detail.refunds_cents = 1600; }
  await page.route("**/api/pos/tabs/**", route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/history-fixture/")) return route.fulfill({ json: detail });
    if (!url.searchParams.has("history_day")) return route.fallback();
    return route.fulfill({ json: { results: [historyTab], history_business_date: "2026-10-17", next_offset: null } });
  });
  await page.goto("/manage"); await page.getByRole("button", { name: "Histórico de comandas", exact: true }).click();
  const dialog = page.getByRole("dialog"); await dialog.getByRole("button", { name: /Conta encerrada/ }).click();
  await expect(dialog.getByText("Total da conta", { exact: true })).toBeVisible();
  if (scenario === "simulated") await expect(dialog.getByText("Paga · simulação", { exact: true })).toBeVisible();
  else await expect(dialog.locator('.notice[data-state="success"]')).toHaveCount(0);
  if (scenario === "stale") await expect(dialog.getByText("Taxa de serviço desatualizada; confira a conta.")).toBeVisible();
});
