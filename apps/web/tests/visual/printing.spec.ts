import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 1280]) {
  test(`printing management readable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
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
