import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

test("service queue preserves ownership, conflicts and same-task lost-response retry", async ({ page }) => {
  await fixture(page, "normal", true);
  let task = { id: "call-test", task_type: "BILL_REQUEST", state: "OPEN", destination_label: "Mesa com nome longo para conferir atendimento durante o turno", claimed_by_id: null as string | null, age_seconds: 125 };
  let visible = true, readsFail = false;
  const attempts: string[] = [];
  await page.route("**/api/attendance/dispatch/requests/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() === "GET") return route.fulfill({ status: readsFail ? 503 : 200, json: readsFail ? { code: "TEMPORARY", message: "Fila indisponível." } : { results: visible ? [task] : [] } });
    attempts.push(path);
    if (path.endsWith("/claim/")) {
      task = { ...task, claimed_by_id: "other-operator", state: "CLAIMED" };
      return route.fulfill({ status: 409, json: { code: "SERVICE_TASK_ALREADY_CLAIMED", message: "Solicitação tem responsável." } });
    }
    if (attempts.filter(p => p.endsWith("/complete/")).length === 1) return route.abort();
    visible = false;
    return route.fulfill({ json: { ...task, state: "DONE" } });
  });
  await page.goto("/attendance");
  const panel = page.getByRole("region", { name: "Chamadas de atendimento" });
  await expect(panel.getByText("Solicitado há 2 min")).toBeVisible();
  await layoutAndA11y(page);
  await panel.getByRole("button", { name: "Assumir chamada" }).click();
  await expect(panel.getByText("Outro operador está responsável")).toBeVisible();
  await expect(panel.getByRole("button", { name: "Concluir chamada" })).toBeDisabled();
  task = { ...task, state: "OPEN", claimed_by_id: null };
  readsFail = true;
  await panel.getByRole("button", { name: "Atualizar chamadas" }).click();
  await expect(panel.getByText("Chamadas desatualizadas.", { exact: false })).toBeVisible();
  await expect(panel.getByRole("button", { name: "Concluir chamada" })).toBeDisabled();
  readsFail = false;
  await panel.getByRole("button", { name: "Atualizar chamadas" }).click();
  await expect(panel.getByRole("button", { name: "Concluir chamada" })).toBeEnabled();
  await panel.getByRole("button", { name: "Concluir chamada" }).click();
  await expect(panel.getByRole("button", { name: "Verificar mesma ação" })).toBeEnabled();
  await expect(panel.getByText("Chamada concluída.", { exact: true })).toHaveCount(0);
  await panel.getByRole("button", { name: "Verificar mesma ação" }).click();
  await expect(panel.getByText("Chamada concluída.", { exact: true })).toBeVisible();
  await expect(panel.getByText("Nenhuma chamada aberta.")).toBeVisible();
  expect(attempts.slice(-2)).toEqual(["/api/attendance/dispatch/requests/call-test/complete/", "/api/attendance/dispatch/requests/call-test/complete/"]);
});

test("initial service queue failure never claims empty and unknown age is explicit", async ({ page }) => {
  await fixture(page, "normal", true);
  let failing = true;
  await page.route("**/api/attendance/dispatch/requests/", route => route.fulfill({ status: failing ? 503 : 200, json: failing ? { code: "TEMPORARY", message: "Fila indisponível." } : { results: [{ id: "call-test", task_type: "SERVICE_REQUEST", state: "CLAIMED", destination_label: "Mesa 24", claimed_by_id: "operator-test" }] } }));
  await page.goto("/attendance");
  const panel = page.getByRole("region", { name: "Chamadas de atendimento" });
  await expect(panel.getByText("Fila indisponível.")).toBeVisible();
  await expect(panel.getByText("Nenhuma chamada aberta.")).toHaveCount(0);
  failing = false;
  await panel.getByRole("button", { name: "Atualizar chamadas" }).click();
  await expect(panel.getByText("Tempo não informado")).toBeVisible();
  await expect(panel.getByText("Você está responsável")).toBeVisible();
  await expect(panel.getByRole("button", { name: "Assumir chamada" })).toHaveCount(0);
});

test("occupancy covers remain canonical through conflict and lost response", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: {
    staff: { id: "operator-test", display_name: "Operador" }, venue: { id: "venue-test", name: "Teste" },
    session: { id: "session-test" }, capabilities: ["table.manage"],
  } }));
  let current = { covers_count: null as number | null, version: 0, source: null as string | null };
  const writes: Record<string, unknown>[] = [];
  await page.route("**/api/attendance/hospitality/occupancies/occupancy-test/party-size/", async route => {
    if (route.request().method() === "GET") return route.fulfill({ json: { current, history: [] } });
    writes.push(route.request().postDataJSON());
    if (writes.length === 1) {
      current = { covers_count: 3, version: 1, source: "GUEST" };
      return route.fulfill({ status: 409, json: { code: "PARTY_SIZE_VERSION_CONFLICT", message: "Quantidade alterada por outro operador." } });
    }
    if (writes.length === 2) return route.abort();
    current = { covers_count: 4, version: 2, source: "STAFF" };
    return route.fulfill({ json: current });
  });
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await expect(page.getByText("Quantidade não informada", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Quantidade de pessoas", { exact: true })).toHaveValue("");
  await page.getByRole("button", { name: "Selecionar 4 pessoas", exact: true }).click();
  await page.getByRole("button", { name: "Confirmar quantidade" }).click();
  await expect(page.getByText("3 pessoa(s) · Informado pelo cliente")).toBeVisible();
  expect(writes).toHaveLength(1);
  await page.getByRole("button", { name: "Confirmar quantidade" }).click();
  await expect(page.getByRole("button", { name: "Verificar mesma quantidade" })).toBeVisible();
  await expect(page.getByLabel("Quantidade de pessoas", { exact: true })).toBeDisabled();
  await expect(page.getByText("3 pessoa(s) · Informado pelo cliente")).toBeVisible();
  await page.getByRole("button", { name: "Verificar mesma quantidade" }).click();
  await expect(page.getByText("4 pessoa(s) · Informado pela equipe")).toBeVisible();
  expect(writes[2]).toEqual(writes[1]);
  expect(writes[1]).toMatchObject({ covers_count: 4, expected_version: 1 });
  await layoutAndA11y(page);
});

for (const width of [360, 390, 430, 1280]) {
  test(`Atendimento browser operations without payments at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await fixture(page, "normal", true);
    await page.goto("/attendance");
    await expect(page.getByRole("heading", { name: "Entregas prontas" })).toBeVisible();
    await expect(page.getByText("Teste sem pagamentos.", { exact: false })).toBeVisible();
    await stable(page); await layoutAndA11y(page);
    await page.getByRole("button", { name: "Contas", exact: true }).click();
    await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
    await expect(page.getByRole("button", { name: /Fritas/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "Receber em dinheiro" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /Estornos|Abrir caixa/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Fechar comanda", exact: true })).toBeDisabled();
    await layoutAndA11y(page);
    await page.getByRole("button", { name: "Mesas", exact: true }).click();
    await expect(page.getByRole("button", { name: "Liberar mesa 24" })).toBeVisible();
    await layoutAndA11y(page);
  });
}
test("Atendimento manifest and financial gateway exclusion", async ({ request }) => {
  const manifest = await request.get("/attendance/manifest.webmanifest");
  expect(await manifest.json()).toMatchObject({ name: "Rodada Atendimento", start_url: "/attendance", display: "standalone" });
  for (const route of ["tabs/test/payments", "tabs/test/payments/integrated", "payments/capabilities", "refunds", "cash/points"]) {
    const result = await request.post(`/api/attendance/${route}/`, { data: {} });
    expect(result.status()).toBe(403);
    expect((await result.json()).code).toBe("ATTENDANCE_OPERATION_DISABLED");
  }
});

test("ambiguous order retry preserves payload after catalog changes", async ({ page }) => {
  await fixture(page, "normal", true);
  const attempts: unknown[] = [];
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", async route => {
    attempts.push(route.request().postDataJSON());
    await route.fulfill({ status: attempts.length === 1 ? 503 : 200, json: attempts.length === 1 ? { code: "TEMPORARY", message: "Resultado ainda não confirmado." } : { id: "same-order" } });
  });
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Contas", exact: true }).click();
  await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
  await page.getByRole("button", { name: /Fritas/ }).click();
  await page.getByLabel("Quantidade de Fritas").fill("2");
  await layoutAndA11y(page);
  await page.getByRole("button", { name: /Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeVisible();
  await expect(page.getByLabel("Quantidade de Fritas")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Abrir", exact: true })).toBeDisabled();
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [] } }));
  await page.clock.runFor(15000);
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
});

test("Atendimento hostname selects the dedicated browser entry", async ({ request }) => {
  const response = await request.get("/", { headers: { host: "atendimento.rodada.ai" } });
  expect(response.ok()).toBeTruthy();
  expect(await response.text()).toContain("Rodada Atendimento");
  const manifest = await request.get("/manifest.webmanifest", { headers: { host: "atendimento.rodada.ai" } });
  expect(await manifest.json()).toMatchObject({ name: "Rodada Atendimento", start_url: "/attendance" });
});
