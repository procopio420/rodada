import { attendanceBill } from "./attendance-actions";
import { attendanceDraft, openOtherTabs, closeAttendanceTab } from "./attendance-actions";
import { addCatalogItem } from "./category-actions";
import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

test("service queue preserves ownership and blocks mutations after conflict or stale read", async ({ page }) => {
  await fixture(page, "normal", true);
  let task = { id: "call-test", task_type: "SERVICE_REQUEST", state: "OPEN", destination_label: "Mesa 24", claimed_by_id: null as string | null, age_seconds: 125,
    target_version: 1, target: { kind: "TAB", tab_id: "tab-test", table_id: null, occupancy_id: null, generation: null } };
  let readsFail = false;
  const attempts: string[] = [];
  await page.route("**/api/attendance/dispatch/requests/", route => route.fulfill({ json: { results: [task] } }));
  await page.route("**/api/attendance/dispatch/tasks/call-test/", route => route.fulfill({ status: readsFail ? 503 : 200, json: readsFail ? { message: "Fila indisponível." } : task }));
  await page.route("**/api/attendance/dispatch/requests/call-test/*/", route => {
    attempts.push(new URL(route.request().url()).pathname);
    task = { ...task, claimed_by_id: "other-operator", state: "CLAIMED" };
    return route.fulfill({ status: 409, json: { code: "SERVICE_TASK_ALREADY_CLAIMED", message: "Solicitação tem responsável." } });
  });
  await page.goto("/attendance");
  const panel = page.getByRole("region", { name: "Chamados e pedidos de conta" });
  await expect(panel.getByText("há 2 min", { exact: true })).toBeVisible();
  await panel.getByRole("button", { name: /Mesa 24.*Atender cliente/ }).click();
  const context = page.getByRole("complementary", { name: "Chamado de origem" });
  await layoutAndA11y(page);
  await context.getByRole("button", { name: "Assumir chamado", exact: true }).click();
  await expect(context.getByText("Outro operador está responsável.", { exact: true })).toBeVisible();
  await expect(context.getByRole("button", { name: "Assumir chamado", exact: true })).toHaveCount(0);
  await expect(context.getByRole("button", { name: "Atendimento resolvido", exact: true })).toHaveCount(0);
  readsFail = true; await page.clock.runFor(15001);
  await expect(context.getByRole("button", { name: "Verificar mesma chamada", exact: true })).toBeVisible();
  await expect(context.getByText("Outro operador está responsável.", { exact: true })).toBeVisible();
  await expect(context.getByRole("button", { name: "Atendimento resolvido", exact: true })).toHaveCount(0);
  readsFail = false; await context.getByRole("button", { name: "Verificar mesma chamada", exact: true }).click();
  await expect(context.getByRole("button", { name: "Verificar mesma chamada", exact: true })).toHaveCount(0);
  expect(attempts).toEqual(["/api/attendance/dispatch/requests/call-test/claim/"]);
});

for (const committed of [false, true]) test(`service queue lost ACK reconciles same task, committed=${committed}`, async ({ page }) => {
  await fixture(page, "normal", true);
  let task = { id: "call-test", task_type: "SERVICE_REQUEST", state: "CLAIMED", destination_label: "Mesa 24", claimed_by_id: "operator-test", age_seconds: 125,
    target_version: 1, target: { kind: "TAB", tab_id: "tab-test", table_id: null, occupancy_id: null, generation: null } };
  const attempts: { path: string; body: string | null }[] = [];
  await page.route("**/api/attendance/dispatch/requests/", route => route.fulfill({ json: { results: task.state === "DONE" ? [] : [task] } }));
  await page.route("**/api/attendance/dispatch/tasks/call-test/", route => route.fulfill({ json: task }));
  await page.route("**/api/attendance/dispatch/requests/call-test/complete/", route => {
    attempts.push({ path: new URL(route.request().url()).pathname, body: route.request().postData() });
    if (attempts.length === 1) { if (committed) task = { ...task, state: "DONE" }; return route.abort(); }
    task = { ...task, state: "DONE" }; return route.fulfill({ json: task });
  });
  await page.goto("/attendance"); await page.getByRole("button", { name: /Mesa 24.*Atender cliente/ }).click();
  const context = page.getByRole("complementary", { name: "Chamado de origem" });
  await page.clock.pauseAt(new Date("2026-10-08T21:00:01Z"));
  await context.getByRole("button", { name: "Atendimento resolvido", exact: true }).click();
  await expect(context.getByRole("button", { name: "Verificar mesma chamada", exact: true })).toBeEnabled();
  await expect(context.getByText("Chamada concluída no servidor.")).toHaveCount(0);
  await context.getByRole("button", { name: "Verificar mesma chamada", exact: true }).click();
  if (!committed) await context.getByRole("button", { name: "Verificar mesma ação", exact: true }).click();
  await expect(context.getByText("Chamada concluída no servidor.")).toBeVisible();
  expect(attempts).toHaveLength(committed ? 1 : 2);
  for (const attempt of attempts) expect(attempt).toEqual({ path: "/api/attendance/dispatch/requests/call-test/complete/", body: "{}" });
  await context.getByRole("button", { name: "Voltar à fila →", exact: true }).click();
  await expect(page.getByText("Nenhuma chamada aberta.")).toBeVisible();
});

test("initial service queue failure never claims empty and unknown age is explicit", async ({ page }) => {
  await fixture(page, "normal", true);
  let failing = true;
  await page.route("**/api/attendance/dispatch/requests/", route => route.fulfill({ status: failing ? 503 : 200, json: failing ? { code: "TEMPORARY", message: "Fila indisponível." } : { results: [{ id: "call-test", task_type: "SERVICE_REQUEST", state: "CLAIMED", destination_label: "Mesa 24", claimed_by_id: "operator-test" }] } }));
  await page.goto("/attendance");
  const panel = page.getByRole("region", { name: "Chamados e pedidos de conta" });
  await expect(panel.getByText("Fila indisponível.")).toBeVisible();
  await expect(panel.getByText("Nenhuma chamada aberta.")).toHaveCount(0);
  failing = false; await panel.getByRole("button", { name: "Atualizar chamadas" }).click();
  await expect(panel.getByText("Tempo não informado")).toBeVisible();
  await expect(panel.getByText("Você está responsável")).toBeVisible();
  await expect(panel.getByRole("button", { name: /Atender cliente/ })).toBeEnabled();
});

test("occupancy covers stay out of the simplified table popup without issuing commands", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: {
    staff: { id: "operator-test", display_name: "Operador" }, venue: { id: "venue-test", name: "Teste" },
    session: { id: "session-test" }, capabilities: ["table.manage"],
  } }));
  const requests: string[] = [];
  page.on("request", request => { if (request.url().includes("/party-size/")) requests.push(request.method()); });
  await page.goto("/attendance");
  await page.getByRole("navigation", { name: "Navegação principal" }).getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: /Mesa 24 Ocupada/ }).click();
  const dialog = page.getByRole("region", { name: "Mesa 24", exact: true });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel("Quantidade de pessoas", { exact: true })).toHaveCount(0);
  await expect(dialog.getByText("Pessoas na ocupação", { exact: true })).toHaveCount(0);
  await expect(dialog.getByRole("button", { name: "Grupo saiu · Liberar mesa", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  expect(requests).toEqual([]);
  // Real canonical read/write/replay remains in integration/frontend-pilot.spec.ts
  // and the API party-size suite; the removed UI cannot trigger those commands.
});

for (const width of [360, 390, 430, 1280]) {
  test(`Atendimento nonfinancial navigation never records payments at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 }); await fixture(page, "normal", true);
    const financialWrites: string[] = [];
    page.on("request", request => { if (request.method() !== "GET" && /\/(payments|refunds|cash)\//.test(request.url())) financialWrites.push(request.url()); });
    await page.goto("/attendance");
    await expect(page.getByRole("heading", { name: "Chamados e pedidos de conta", exact: true })).toBeVisible();
    await stable(page); await layoutAndA11y(page);
    await openOtherTabs(page); await page.locator('button[data-tab-id="tab-test"]').click();
    await expect(page.getByRole("heading", { name: "Comanda de teste", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
    await expect(page.getByRole("group", { name: "Categorias", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: /Estornos|Abrir caixa/ })).toHaveCount(0);
    await attendanceBill(page);
    await expect(page.getByRole("button", { name: "Encerrar comanda", exact: true })).toBeDisabled();
    await expect(page.getByText("Saldo canônico em aberto", { exact: true })).toBeVisible();
    await layoutAndA11y(page); await closeAttendanceTab(page);
    await page.getByRole("button", { name: /Mesa 24 Ocupada/ }).click();
    await expect(page.getByRole("button", { name: "Grupo saiu · Liberar mesa", exact: true })).toBeVisible();
    await layoutAndA11y(page); expect(financialWrites).toEqual([]);
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
    await route.fulfill({ status: attempts.length === 1 ? 503 : 200, json: attempts.length === 1 ? { code: "TEMPORARY", message: "Resultado ainda não confirmado." } : { id: "same-order", tab_id: "tab-test" } });
  });
  await page.route("**/api/attendance/tabs/tab-test/", route => route.fulfill({ json: {
    id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 14400,
    orders: attempts.length > 1 ? [{ id: "same-order", items: [] }] : [], payments: [], refund_required_corrections: [],
  } }));
  await page.goto("/attendance");
  await openOtherTabs(page);
  await page.getByRole("button", { name: /Comanda de teste\s/ }).click();
  await addCatalogItem(page, "Fritas");
  await attendanceDraft(page);
  await page.getByRole("button", { name: "Aumentar Fritas", exact: true }).click();
  await layoutAndA11y(page);
  await page.getByRole("button", { name: /^(Confirmar pedido|Enviar )/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Aumentar Fritas", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "＋ Adicionar itens", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Opções do atendimento", exact: true })).toBeDisabled();
  await expect(page.getByRole("navigation", { name: "Navegação principal" })).toBeHidden();
  await expect(page.getByRole("region", { name: "Comanda selecionada", exact: true }).getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [] } }));
  await page.clock.runFor(15000);
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect.poll(() => attempts.length).toBe(2);
  expect(attempts[1]).toEqual(attempts[0]);
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
});

test("Atendimento hostname selects the dedicated browser entry", async ({ request }) => {
  const response = await request.get("/", { headers: { host: "atendimento.rodada.ai" } });
  expect(response.ok()).toBeTruthy();
  expect(await response.text()).toContain("Rodada Atendimento");
  const manifest = await request.get("/manifest.webmanifest", { headers: { host: "atendimento.rodada.ai" } });
  expect(await manifest.json()).toMatchObject({ name: "Rodada Atendimento", start_url: "/attendance" });
});
