import { test, expect } from "@playwright/test";
import { fixture } from "./fixtures";
const job = (id: string) => ({ id, state: "FAILED_RETRYABLE", last_error: "Conexão indisponível.", reason: "", reprint_of: null, document_id: "document-test", attempts: [] });
test.beforeEach(async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/pos/printing/agents/v1/", r => r.fulfill({ json: { enabled: false, results: [] } }));
  await page.route("**/api/pos/printing/agents/v1/routes/", r => r.fulfill({ json: { printers: [], routes: [] } }));
});
test("printing ignores response from a previous filter", async ({ page }) => {
  await page.route("**/api/pos/printing/endpoints/", r => r.fulfill({ json: { results: [] } }));
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let oldStarted = false;
  await page.route("**/api/pos/printing/jobs/**", async route => {
    const old = new URL(route.request().url()).searchParams.get("failed_only") === "false";
    if (old) { oldStarted = true; await gate; }
    await route.fulfill({ json: { results: [job(old ? "job-old-query" : "job-filtered-query")], next_offset: null } });
  });
  await page.goto("/manage/printing");
  await expect.poll(() => oldStarted).toBe(true);
  await page.getByRole("button", { name: "Somente falhas", exact: true }).click();
  await expect(page.getByRole("article", { name: "job-filtered-query", exact: true })).toBeVisible();
  const late = page.waitForResponse(r => r.url().includes("/printing/jobs/") && r.url().includes("failed_only=false"));
  release();
  await (await late).finished();
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(page.getByRole("article", { name: "job-filtered-query", exact: true })).toBeVisible();
  await expect(page.getByRole("article", { name: "job-old-query", exact: true })).toHaveCount(0);
});
test("printing polling handles transport failure and stops after leaving", async ({ page }) => {
  await page.clock.install();
  await page.route("**/api/pos/printing/endpoints/", r => r.fulfill({ json: { results: [] } }));
  let reads = 0;
  await page.route("**/api/pos/printing/jobs/**", route => ++reads === 1 ? route.fulfill({ json: { results: [job("job-poll-test")], next_offset: null } }) : route.abort("failed"));
  await page.goto("/manage/printing");
  await expect(page.getByRole("article", { name: "job-poll-test", exact: true })).toBeVisible();
  await page.clock.runFor(5000);
  await expect(page.getByRole("main").getByRole("alert")).toHaveText("Não foi possível atualizar os trabalhos.");
  await page.goto("/manage#gestao");
  const before = reads;
  await page.clock.runFor(10000);
  expect(reads).toBe(before);
});
test("printing initial transport failure keeps existing message", async ({ page }) => {
  await page.route("**/api/pos/printing/endpoints/", r => r.fulfill({ json: { results: [] } }));
  await page.route("**/api/pos/printing/jobs/**", route => route.abort("failed"));
  await page.goto("/manage/printing");
  await expect(page.getByRole("main").getByRole("alert")).toHaveText("Impressão indisponível. Confira a conexão.");
});
