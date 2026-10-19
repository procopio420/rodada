import { expect, test, type Page } from "./test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";

async function login(page: Page, operator: string) {
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill(operator);
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await page.getByRole("button", { name: "Agora", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Entregas prontas" })).toBeVisible();
}
async function api(page: Page, url: string, body?: unknown) {
  return page.evaluate(async ({ url, body }) => {
    const response = await fetch(`/api/pos/${url}`, { method: body === undefined ? "GET" : "POST",
      headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
    if (!response.ok) throw new Error(`${url}: ${response.status}`);
    return response.json();
  }, { url, body });
}

for (const width of [360, 390, 430]) test(`real service queue conflict, stale and committed response loss at ${width}`, async ({ page, browser }) => {
  await page.setViewportSize({ width, height: 844 });
  let initialReadFailed = true;
  await page.route("**/api/attendance/dispatch/requests/", route => initialReadFailed
    ? route.fulfill({ status: 503, json: { code: "TEST_INITIAL_READ_FAILURE", message: "Leitura indisponível no ensaio." } }) : route.continue());
  await login(page, "test-manager");
  const initialPanel = page.getByRole("region", { name: "Chamadas de atendimento" });
  await expect(initialPanel.getByText(/Chamadas desatualizadas/)).toBeVisible();
  await expect(initialPanel.getByText("Nenhuma chamada aberta.")).toHaveCount(0);
  initialReadFailed = false;
  await page.unroute("**/api/attendance/dispatch/requests/");
  const label = `Acceptance queue ${width} para atendimento com referência operacional longa`;
  const table = await api(page, "hospitality/tables/", { label, guest_ordering_mode: "DIRECT" });
  const originalOccupancy = await api(page, `hospitality/tables/${table.id}/occupy/`, {});
  const task = await api(page, "dispatch/requests/", { request_id: crypto.randomUUID(), task_type: "BILL_REQUEST", table_id: table.id });
  await page.getByRole("button", { name: "Atualizar chamadas" }).click();
  const panel = page.getByRole("region", { name: "Chamadas de atendimento" });
  const row = panel.getByRole("article").filter({ has: page.getByRole("heading", { name: `Pedido de conta · Mesa ${label}`, exact: true }) });
  await expect(row.getByText("Sem responsável", { exact: true })).toBeVisible();
  await expect(row.getByText(/Solicitado há/)).toBeVisible();

  const otherContext = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}` });
  const other = await otherContext.newPage();
  await login(other, "test-staff");
  const otherRow = other.getByRole("article").filter({ has: other.getByRole("heading", { name: `Pedido de conta · Mesa ${label}`, exact: true }) });
  await otherRow.getByRole("button", { name: "Assumir chamada", exact: true }).click();
  await expect(otherRow.getByText("Você está responsável", { exact: true })).toBeVisible();
  // First browser still has an unclaimed snapshot. The real server rejects it.
  await row.getByRole("button", { name: "Assumir chamada", exact: true }).click();
  await expect(row.getByText("Outro operador está responsável", { exact: true })).toBeVisible();
  await expect(row.getByRole("button", { name: "Assumir chamada", exact: true })).toBeDisabled();
  await expect(row.getByRole("button", { name: "Concluir chamada", exact: true })).toBeDisabled();
  const canonical = await api(page, "dispatch/requests/");
  expect(canonical.results.find((r: { id: string }) => r.id === task.id).claimed_by_id).toBeTruthy();

  let failedRead = true;
  await page.route("**/api/attendance/dispatch/requests/", route => failedRead
    ? route.fulfill({ status: 503, json: { code: "TEST_READ_FAILURE", message: "Leitura indisponível no ensaio." } }) : route.continue());
  await panel.getByRole("button", { name: "Atualizar chamadas" }).click();
  await expect(panel.getByText(/Chamadas desatualizadas/)).toBeVisible();
  await expect(panel.getByText("Nenhuma chamada aberta.")).toHaveCount(0);
  await expect(row.getByRole("button", { name: "Concluir chamada", exact: true })).toBeDisabled();
  failedRead = false;
  await panel.getByRole("button", { name: "Atualizar chamadas" }).click();
  await expect(panel.getByText(/Chamadas desatualizadas/)).toHaveCount(0);

  const attempts: { url: string; body: string | null }[] = [];
  await other.route(`**/api/attendance/dispatch/requests/${task.id}/complete/`, async route => {
    attempts.push({ url: new URL(route.request().url()).pathname, body: route.request().postData() });
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.ok()).toBeTruthy();
    if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await otherRow.getByRole("button", { name: "Concluir chamada", exact: true }).click();
  const retry = other.getByRole("button", { name: "Verificar mesma ação", exact: true });
  await expect(retry).toBeEnabled();
  await expect(other.getByText("Chamada concluída.", { exact: true })).toHaveCount(0);
  expect((await api(other, "dispatch/requests/")).results.some((r: { id: string }) => r.id === task.id)).toBe(false);
  await retry.click();
  await expect(other.getByText("Chamada concluída.", { exact: true })).toBeVisible();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
  await expect(otherRow).toHaveCount(0);
  const a11y = await new AxeBuilder({ page }).include('section[aria-labelledby="service-queue-heading"]').analyze();
  expect(a11y.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  for (const button of await row.getByRole("button").all()) expect((await button.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  const out = path.resolve(__dirname, "../../../../visual-artifacts/spec023-024/runtime");
  await mkdir(out, { recursive: true });
  await page.screenshot({ path: path.join(out, `queue-${width}.png`), fullPage: true });
  await api(page, `hospitality/tables/${table.id}/release/`, { expected_occupancy_id: originalOccupancy.id, expected_generation: originalOccupancy.generation });
  await otherContext.close();
});
