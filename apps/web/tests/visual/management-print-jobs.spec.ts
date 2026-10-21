import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
import type { Page } from "@playwright/test";

const jobs = [
  { id: "job-uncertain", state: "DELIVERY_UNCERTAIN", last_error: "Envio interrompido; confira o papel antes de outra ação.", reason: "", reprint_of: null, document_id: "document-test", attempts: [{ number: 1, outcome: "DELIVERY_UNCERTAIN", detail: "Conferir fila e papel no computador de impressão." }] },
  { id: "job-failed", state: "FAILED_RETRYABLE", last_error: "Conexão indisponível.", reason: "", reprint_of: null, document_id: "document-test", attempts: [] },
  { id: "job-printed", state: "PRINTED", last_error: "", reason: "Cópia de teste", reprint_of: "job-original", document_id: "document-test", attempts: [] },
];
async function prepare(page: Page) {
  await fixture(page, "normal", true);
  await page.route("**/api/pos/printing/agents/v1/", route => route.fulfill({ json: { enabled: false, results: [] } }));
  await page.route("**/api/pos/printing/agents/v1/routes/", route => route.fulfill({ json: { printers: [], routes: [] } }));
  await page.route("**/api/pos/printing/endpoints/", route => route.fulfill({ json: { results: [] } }));
  await page.route("**/api/pos/printing/jobs/**", route => route.fulfill({ json: { results: jobs, next_offset: null } }));
}

for (const width of [360, 390, 430, 1280]) test(`print job hierarchy ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await prepare(page);
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/printing");
  await expect(page.getByText("job-uncertain", { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S1F_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-print-jobs/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const uncertain = page.getByRole("article", { name: "job-uncertain", exact: true });
  await expect(uncertain.getByRole("heading", { level: 3 })).toHaveText("Pode ter impresso · confira o papel");
  await expect(uncertain).toContainText(jobs[0].last_error);
  await expect(uncertain).toContainText("Tentativa 1");
  await expect(uncertain.getByRole("link", { name: "Ver documento" })).toHaveAttribute("href", "/printing/jobs/job-uncertain");
  await expect(uncertain.getByRole("button", { name: "Tentar agora" })).toHaveCount(0);
  await expect(uncertain.getByRole("button", { name: "Confirmar que vi o papel" })).toBeVisible();
  const printed = page.getByRole("article", { name: "job-printed", exact: true });
  await expect(printed.getByRole("button", { name: "Cancelar trabalho" })).toHaveCount(0);
  await expect(printed).toContainText("REIMPRESSÃO de job-original · Cópia de teste");
  await expect(printed.getByRole("button", { name: "Reimprimir cópia" })).toBeDisabled();
  await page.getByLabel("Motivo para reimpressão").fill("Conferência de teste");
  await expect(printed.getByRole("button", { name: "Reimprimir cópia" })).toBeEnabled();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-print-jobs/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

for (const action of ["retry", "confirm", "cancel", "reprint"]) test(`job action preserves ${action} command`, async ({ page }) => {
  await prepare(page);
  const target = action === "retry" ? "job-failed" : "job-uncertain";
  let sent: Record<string, unknown> | undefined;
  await page.route(`**/api/pos/printing/jobs/${target}/`, route => {
    sent = route.request().postDataJSON();
    return route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Ação não permitida." } });
  });
  await page.goto("/manage/printing");
  await page.getByLabel("Motivo para reimpressão").fill("Conferência de teste");
  const article = page.getByRole("article", { name: target, exact: true });
  const labels: Record<string, string> = { retry: "Tentar agora", confirm: "Confirmar que vi o papel", cancel: "Cancelar trabalho", reprint: "Reimprimir cópia" };
  await article.getByRole("button", { name: labels[action], exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toHaveText("Ação não permitida.");
  if (action === "reprint") {
    expect(sent).toEqual({ action, reason: "Conferência de teste", idempotency_key: expect.stringMatching(/^[0-9a-f-]{36}$/) });
  } else expect(sent).toEqual({ action });
  await expect(article.getByRole("button", { name: labels[action], exact: true })).toBeEnabled();
});
