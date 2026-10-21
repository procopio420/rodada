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
  await expect(page.getByRole("heading", { name: "Chamados e pedidos de conta" })).toBeVisible();
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
  const initialPanel = page.getByRole("region", { name: "Chamados e pedidos de conta" });
  await expect(initialPanel.getByText(/Chamadas desatualizadas/)).toBeVisible();
  await expect(initialPanel.getByText("Nenhuma chamada aberta.")).toHaveCount(0);
  initialReadFailed = false;
  await page.unroute("**/api/attendance/dispatch/requests/");
  const label = `Acceptance queue ${width} para atendimento com referência operacional longa`;
  const table = await api(page, "hospitality/tables/", { label, guest_ordering_mode: "DIRECT" });
  const originalOccupancy = await api(page, `hospitality/tables/${table.id}/occupy/`, {});
  const task = await api(page, "dispatch/requests/", { request_id: crypto.randomUUID(), task_type: "SERVICE_REQUEST", table_id: table.id });
  await page.getByRole("button", { name: "Atualizar chamadas" }).click();
  const panel = page.getByRole("region", { name: "Chamados e pedidos de conta" });
  const row = panel.getByRole("article").filter({ hasText: `Mesa ${label}` });
  await expect(row.getByText("Sem responsável", { exact: true })).toBeVisible();
  await expect(row.getByText(/há .* min/)).toBeVisible();
  await row.getByRole("button", { name: /Escolher comanda/ }).click();
  const context = page.getByRole("complementary", { name: "Chamado de origem" });
  await expect(context.getByRole("button", { name: "Assumir chamado", exact: true })).toBeEnabled();

  const otherContext = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}` });
  const other = await otherContext.newPage();
  await other.clock.install();
  await login(other, "test-staff");
  const otherRow = other.getByRole("article").filter({ hasText: `Mesa ${label}` });
  await otherRow.getByRole("button", { name: /Escolher comanda/ }).click();
  const otherTask = other.getByRole("complementary", { name: "Chamado de origem" });
  await otherTask.getByRole("button", { name: "Assumir chamado", exact: true }).click();
  await expect(otherTask.getByRole("button", { name: "Atendimento resolvido" })).toBeEnabled();
  // Both contexts loaded OPEN. The first browser's stale action hits the real conflict guard.
  const conflict = page.waitForResponse(r => r.url().includes(`${task.id}/claim`) && r.status() === 409);
  await context.getByRole("button", { name: "Assumir chamado", exact: true }).click();
  await conflict;
  await expect(context.getByText("Outro operador está responsável.", { exact: true })).toBeVisible();
  await expect(context.getByRole("button", { name: "Assumir chamado", exact: true })).toHaveCount(0);
  await expect(context.getByRole("button", { name: "Atendimento resolvido", exact: true })).toHaveCount(0);
  const canonical = await api(page, "dispatch/requests/");
  expect(canonical.results.find((r: { id: string }) => r.id === task.id).claimed_by_id).toBeTruthy();

  // Failed exact-task read preserves the existing task and blocks mutations.
  await page.route(`**/api/attendance/dispatch/tasks/${task.id}/`, route =>
    route.fulfill({ status: 503, json: { code: "TEST_READ_FAILURE", message: "Leitura indisponível no ensaio." } }));
  await expect(context.getByRole("button", { name: "Verificar mesma chamada" })).toBeVisible({ timeout: 20_000 });
  await expect(context.getByText("Outro operador está responsável.", { exact: true })).toBeVisible();
  await expect(context.getByRole("button", { name: "Atendimento resolvido" })).toHaveCount(0);
  await page.unroute(`**/api/attendance/dispatch/tasks/${task.id}/`);
  await context.getByRole("button", { name: "Verificar mesma chamada" }).click();
  await expect(context.getByRole("button", { name: "Verificar mesma chamada" })).toHaveCount(0);

  // Freeze only this browser after the real polling-fallback proof above.
  // A background poll must not consume the lost-ACK recovery before its click.
  await other.clock.pauseAt(new Date(Date.now() + 1000));
  const attempts: { url: string; body: string | null }[] = [];
  await other.route(`**/api/attendance/dispatch/requests/${task.id}/complete/`, async route => {
    attempts.push({ url: new URL(route.request().url()).pathname, body: route.request().postData() });
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.ok()).toBeTruthy();
    await route.abort();
  });
  await otherTask.getByRole("button", { name: "Atendimento resolvido", exact: true }).click();
  // Pending is persisted before POST: wait until the committed response has
  // actually been lost and handled before asserting canonical server state.
  await expect(otherTask.getByRole("button", { name: "Verificar mesma chamada", exact: true })).toBeEnabled();
  await expect(otherTask.getByText("Ação sem confirmação preservada nesta chamada.")).toBeVisible();
  await expect(otherTask.getByText("Chamada concluída no servidor.")).toHaveCount(0);
  expect((await api(other, "dispatch/requests/")).results.some((r: { id: string }) => r.id === task.id)).toBe(false);
  await otherTask.getByRole("button", { name: "Verificar mesma chamada", exact: true }).click();
  await expect(otherTask.getByText("Chamada concluída no servidor.")).toBeVisible();
  // Canonical readback resolves the original intent without a second mutation.
  expect(attempts).toHaveLength(1);
  expect(attempts[0].body).toBe("{}");
  await expect(otherTask.getByText("Ação sem confirmação preservada nesta chamada.")).toHaveCount(0);
  await context.getByRole("button", { name: "Voltar à fila →" }).click();
  await page.reload();
  await expect(row).toHaveCount(0);
  const a11y = await new AxeBuilder({ page }).include('section[aria-labelledby="service-queue-heading"]').analyze();
  expect(a11y.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  for (const button of await page.locator(".ux2BottomNav").getByRole("button").all()) expect((await button.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  const out = path.resolve(__dirname, "../../../../visual-artifacts/spec023-024/runtime");
  await mkdir(out, { recursive: true });
  await page.screenshot({ path: path.join(out, `queue-${width}.png`), fullPage: true });
  await api(page, `hospitality/tables/${table.id}/release/`, { expected_occupancy_id: originalOccupancy.id, expected_generation: originalOccupancy.generation });
  await otherContext.close();
});
