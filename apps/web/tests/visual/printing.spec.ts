import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 1280]) {
  test(`printing management readable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    await page.route("**/api/pos/printing/agents/v1/", route => route.fulfill({ json: { enabled: false, results: [] } }));
    await page.route("**/api/pos/printing/agents/v1/routes/", route => route.fulfill({ json: { printers: [], routes: [] } }));
    await page.route("**/api/pos/printing/endpoints/", route => route.fulfill({ json: { results: [{ id: "printer-1", label: "Cozinha / computador local", adapter: "SPOOL", width_mm: 80, connection_ref: "kitchen-local", cut_supported: false, stations: ["KITCHEN"], enabled: true, health: "UNKNOWN", health_at: null, bridge_status: "OFFLINE" }] } }));
    await page.route("**/api/pos/printing/jobs/**", route => route.fulfill({ json: { results: [{ id: "11111111-1111-4111-8111-111111111111", state: "DELIVERY_UNCERTAIN", last_error: "Envio interrompido; pode haver impressão parcial.", reason: "", reprint_of: null, document_id: "document-1", attempts: [{ number: 1, outcome: "DELIVERY_UNCERTAIN", detail: "Conferir papel e fila local." }] }] } }));
    await page.goto("/manage/printing");
    await expect(page.getByText("Bridge: OFFLINE")).toBeVisible();
    await stable(page);
    await layoutAndA11y(page);
  });
  test(`cashier canonical receipt preview readable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    await page.route("**/api/auth/me", route => route.fulfill({ json: { capabilities: ["print.customer"] } }));
    await page.route("**/api/pos/printing/endpoints/", route => route.fulfill({ json: { results: [{ id: "printer-1", label: "Navegador do caixa", adapter: "BROWSER", enabled: true, width_mm: 58, stations: [] }] } }));
    await page.route("**/api/pos/printing/documents/", route => route.fulfill({ json: { id: "document-1", kind: "CUSTOMER_CHECK", text: "CONTA\nDOCUMENTO NÃO FISCAL\n1 x Porção\nSaldo: R$ 72,00", html: '<!doctype html><html lang="pt-BR"><title>Conta não fiscal</title><body><pre>CONTA\nDOCUMENTO NÃO FISCAL\n1 x Porção\nSaldo: R$ 72,00</pre></body></html>' } }));
    await page.goto("/pos");
    await page.getByRole("button", { name: /Comanda de teste/ }).click();
    await page.getByRole("button", { name: "Ver conta / recibos" }).click();
    await expect(page.frameLocator("iframe").locator("pre")).toContainText("NÃO FISCAL");
    await stable(page);
    await layoutAndA11y(page, true);
  });
}

// Public receipt and historical job had no dedicated visual wrapper coverage.
for (const width of [360, 390, 768]) {
  test(`shared receipt preserves document and heading semantics at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    const text = "RECIBO DE TESTE\nDOCUMENTO NÃO FISCAL\nSaldo: R$ 72,00";
    await page.route("**/api/receipt/visual-only", route => route.fulfill({ json: { text } }));
    await page.goto("/receipt/visual-only");
    await expect(page.getByRole("heading", { level: 1, name: "Recibo não fiscal", exact: true })).toBeVisible();
    await expect(page.locator("pre")).toHaveText(text);
    await expect(page.locator("h1 svg")).toHaveAttribute("aria-hidden", "true");
    await stable(page); await layoutAndA11y(page);
    await page.screenshot({ path: `../../visual-artifacts/spec023-all-web/receipt-${width}.png`, fullPage: true });
    await page.route("**/api/receipt/visual-only", route => route.fulfill({ status: 410, json: { code: "EXPIRED" } }));
    await page.reload();
    await expect(page.getByRole("main").getByRole("alert")).toContainText("expirou");
    await expect(page.locator("pre")).toHaveCount(0);
  });
  test(`historical print wrapper preserves immutable output at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    const text = "DOCUMENTO NÃO FISCAL\n1 x Produto de teste\nSaldo: R$ 72,00";
    await page.route("**/api/pos/printing/jobs/visual-only/", route => route.fulfill({ json: { state: "OUTPUT_READY", output: { text, html: `<html lang="pt-BR"><title>Documento de teste</title><body><pre>${text}</pre></body></html>` } } }));
    await page.goto("/printing/jobs/visual-only");
    await expect(page.getByRole("heading", { level: 1, name: "Documento não fiscal", exact: true })).toBeVisible();
    await expect(page.getByText("Documento disponível · papel não confirmado", { exact: true })).toBeVisible();
    await expect(page.frameLocator("iframe").locator("pre")).toHaveText(text);
    await expect(page.getByRole("link", { name: "Baixar texto" })).toHaveAttribute("href", `data:text/plain;charset=utf-8,${encodeURIComponent(text)}`);
    await stable(page); await layoutAndA11y(page, true);
    await page.screenshot({ path: `../../visual-artifacts/spec023-all-web/document-${width}.png`, fullPage: true });
  });
}

for (const width of [360, 390, 430, 1280]) {
  test(`explicit printer profile and renewed attestation at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await fixture(page);
    await page.route("**/api/pos/printing/agents/v1/", route => route.fulfill({ json: { enabled: true, results: [] } }));
    await page.route("**/api/pos/printing/agents/v1/routes/", route => route.fulfill({ json: {
      printers: [{ id: "queue1", agent_id: "pc1", label: "Bematech candidata", queue_name: "Fila Windows de teste", transport: "WINDOWS_DRIVER", driver_name: "Driver instalado", health: "UNKNOWN", config_fingerprint: "test" }], routes: [],
    } }));
    await page.route("**/api/pos/printing/endpoints/", route => route.fulfill({ json: { results: [{ id: "printer1", label: "Bar", adapter: "AGENT", width_mm: 80, stations: ["BAR"], enabled: true, health: "UNKNOWN" }] } }));
    await page.route("**/api/pos/printing/jobs/**", route => route.fulfill({ json: { results: [] } }));
    await page.goto("/manage/printing");
    const panel = page.getByRole("region", { name: "Rotas dos computadores" });
    await panel.getByLabel("Destino lógico").selectOption("printer1");
    await panel.getByLabel("Fila descoberta").selectOption("queue1");
    await panel.getByLabel("Usar ESC/POS RAW em vez do driver Windows").check();
    const confirmation = panel.getByLabel(/Confirmei em teste físico/);
    await confirmation.check();
    await panel.getByLabel("Perfil ESC/POS").selectOption("escpos-pc860-cut-v1");
    await expect(confirmation).not.toBeChecked();
    await expect(panel.getByRole("button", { name: "Salvar rota", exact: true })).toBeDisabled();
    await expect(page.getByRole("link", { name: /Instalador para Windows/ })).toHaveAttribute("href", "https://rodada.bar/downloads");
    await stable(page);
    await layoutAndA11y(page);
    await panel.screenshot({ path: `../../visual-artifacts/print-profile-${width}.png` });
  });
}

test("test-print keeps the same key after confirmed POST and failed readback", async ({ page }) => {
  await fixture(page);
  const keys: string[] = [];
  let failed = false;
  await page.route("**/api/pos/printing/agents/v1/", route => route.fulfill({ json: { enabled: false, results: [] } }));
  await page.route("**/api/pos/printing/agents/v1/routes/", route => route.fulfill({ json: { printers: [], routes: [] } }));
  await page.route("**/api/pos/printing/endpoints/", route => route.fulfill(failed ? { status: 503, json: { message: "Synthetic unavailable" } } : { json: { results: [{ id: "printer1", label: "Bar", adapter: "AGENT", width_mm: 80, stations: ["BAR"], enabled: true, health: "UNKNOWN" }] } }));
  await page.route("**/api/pos/printing/jobs/**", route => route.fulfill({ json: { results: [] } }));
  await page.route("**/api/pos/printing/endpoints/printer1/test/", route => {
    keys.push(route.request().postDataJSON().idempotency_key);
    failed = true;
    return route.fulfill({ status: 201, json: { id: "same-diagnostic-job", state: "QUEUED" } });
  });
  await page.goto("/manage/printing");
  const button = page.getByRole("button", { name: "Testar Bar", exact: true });
  await button.click();
  await expect(page.getByRole("alert")).toContainText("mesma tentativa será preservada");
  await button.click();
  await expect(button).toBeEnabled();
  expect(keys).toHaveLength(2);
  expect(keys[1]).toBe(keys[0]);
});
