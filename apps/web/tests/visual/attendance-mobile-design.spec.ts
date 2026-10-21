import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
import { attendanceWorkspace, attendanceDraft, closeAttendanceTab, openAttendanceTable } from "./attendance-actions";
import { addCatalogItem, chooseCatalogItem, openProductCategory, expectCatalogQuantity } from "./category-actions";

async function setup(page: Page, enabled = true, capabilities = ["table.manage", "tab.open"], settled = false) {
  await fixture(page, "normal", true);
  const tabs = ["tab-test", "tab-other"].map((id, index) => ({ id, display_label: index ? "Comanda B" : "Comanda de teste", table_label: "02", state: settled ? "CLOSED" : "OPEN", version: 1, exposure_cents: settled ? 0 : 2400, payable_cents: settled ? 0 : 2400, orders: [{ id: "original", status: "CONFIRMED", confirmed_at: "2026-10-08T20:00:00Z", items: [{ id: `item-${id}`, product_id: "fries", product_name: "Fritas", quantity: 2, unit_price_cents: 1200, state: "READY" }] }] }));
  const tables = [
    { id: "available", label: "01", status: "AVAILABLE" },
    { id: "occupied", label: "02", status: "OCCUPIED", active_occupancy: { id: "visit", generation: 7, tabs } },
    { id: "dirty", label: "03", status: "DIRTY" },
    { id: "cleaning", label: "04", status: "CLEANING" },
    { id: "out", label: "05", status: "OUT_OF_SERVICE" },
  ];
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "operator-test", display_name: "Operador de teste" }, venue: { id: "venue-test", name: "Estabelecimento de teste" }, session: { id: "session-test" }, capabilities } }));
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { table_service_enabled: enabled, results: tables } }));
  await page.route(/\/api\/attendance\/tabs\/(\?.*)?$/, route => route.fulfill({ json: { results: tabs, next_offset: null } }));
  await page.route(/\/api\/attendance\/tabs\/(tab-test|tab-other)\/(\?.*)?$/, route => route.fulfill({ json: tabs.find(tab => route.request().url().includes(tab.id)) }));
  return { tabs, tables };
}
async function openTable(page: Page) {
  if (await page.getByRole("button", { name: "Mesas", exact: true }).isVisible()) await page.getByRole("button", { name: "Mesas", exact: true }).click();
  if (!await page.locator(".ux2TablePage").isVisible()) await page.getByRole("button", { name: /Mesa 02 Ocupada/ }).click();
  await page.locator('button[data-tab-id="tab-test"]').click();
  const popup = attendanceWorkspace(page);
  await expect(popup).toBeVisible();
  return popup;
}

for (const width of [360, 390, 430, 1280]) test(`inline catalog quantity and optional summary keep selection compact at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  const popup = await openTable(page);
  await popup.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  await expect(popup.getByRole("group", { name: "Categorias", exact: true })).toBeVisible();
  await page.screenshot({ path: `visual-artifacts/033/mobile/catalog-${width}.png` });
  await addCatalogItem(page, "Fritas", 3);
  await expectCatalogQuantity(page, "Fritas", 3);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `visual-artifacts/033/mobile/quantity-${width}.png` });
  await attendanceDraft(page);
  await expect(popup.getByText("3× Fritas", { exact: true })).toBeVisible();
});

test("item cancel leaves draft untouched and personalization separates configurations", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); await openTable(page);
  let writes = 0;
  await page.route("**/orders/confirm/**", route => { writes++; return route.abort(); });
  const item = await chooseCatalogItem(page, "Fritas");
  await page.keyboard.press("Escape");
  await expect(item).not.toBeVisible();
  await expectCatalogQuantity(page, "Fritas", 0);
  await chooseCatalogItem(page, "Fritas");
  await item.getByLabel("Pedido especial (opcional)").fill("Separado");
  await item.getByRole("button", { name: /^Adicionar ·/ }).click();
  const draft = await attendanceDraft(page);
  await draft.getByRole("button", { name: "Aumentar Fritas", exact: true }).click();
  await addCatalogItem(page, "Fritas");
  await attendanceDraft(page);
  await expect(draft.locator(".ux2ReviewRow")).toHaveCount(2);
  await expect(draft.getByText("2× Fritas", { exact: true })).toBeVisible();
  await expect(draft.getByText("Observação: Separado", { exact: true })).toBeVisible();
  expect(writes).toBe(0);
});

test("quantity and configuration edits cannot exceed 99 units", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); await openTable(page);
  await addCatalogItem(page, "Fritas", 60);
  const item = await chooseCatalogItem(page, "Fritas");
  await item.getByLabel("Pedido especial (opcional)").fill("Separado");
  await item.getByRole("button", { name: /^Adicionar ·/ }).click();
  const draft = await attendanceDraft(page);
  const separate = draft.locator(".ux2ReviewRow").filter({ hasText: "Observação: Separado" });
  for (let count = 1; count < 40; count++) await separate.getByRole("button", { name: "Aumentar Fritas", exact: true }).click();
  await separate.getByRole("button", { name: "Editar", exact: true }).click();
  const edit = page.getByRole("dialog", { name: "Personalizar Fritas", exact: true });
  await edit.getByLabel("Pedido especial (opcional)").fill("");
  await expect(edit.getByRole("button", { name: /^Adicionar ·/ })).toBeDisabled();
  await expect(edit.getByText(/Máximo de 99 unidades/)).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(draft.locator(".ux2ReviewRow")).toHaveCount(2);
  await expect(draft.getByText("60× Fritas", { exact: true })).toBeVisible();
  await expect(draft.getByText("40× Fritas", { exact: true })).toBeVisible();
  await separate.getByRole("button", { name: "Reduzir Fritas", exact: true }).click();
  await separate.getByRole("button", { name: "Editar", exact: true }).click();
  await edit.getByLabel("Pedido especial (opcional)").fill("");
  await expect(edit.getByRole("button", { name: /^Adicionar ·/ })).toBeEnabled();
  await edit.getByRole("button", { name: /^Adicionar ·/ }).click();
  await expect(edit).not.toBeVisible();
  const equivalent = draft.locator(".ux2ReviewRow").filter({ has: page.getByText("39× Fritas", { exact: true }) });
  await equivalent.getByRole("button", { name: "Aumentar Fritas", exact: true }).click();
  await expect(draft.getByText("60× Fritas", { exact: true })).toBeVisible();
  await expect(draft.getByText("39× Fritas", { exact: true })).toBeVisible();
  await expect(draft.getByText("40× Fritas", { exact: true })).toHaveCount(0);
});

test("quantity popup remains usable with doubled text", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); await openTable(page);
  const item = await chooseCatalogItem(page, "Fritas");
  await item.getByLabel("Pedido especial (opcional)").fill("Separado");
  await item.evaluate(element => { for (const node of element.querySelectorAll<HTMLElement>("*")) node.style.fontSize = `${parseFloat(getComputedStyle(node).fontSize) * 2}px`; });
  await item.getByRole("button", { name: /^Adicionar ·/ }).scrollIntoViewIfNeeded();
  await expect(item.getByRole("button", { name: /^Adicionar ·/ })).toBeVisible();
  await layoutAndA11y(page);
  await page.screenshot({ path: "visual-artifacts/029/categories/quantity-360-font200.png" });
});

test("overlapping list refreshes share one read and leave tab selection responsive", async ({ page }) => {
  await setup(page);
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await expect(page.getByRole("button", { name: /Mesa 02 Ocupada/ })).toBeEnabled();
  let reads = 0;
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route(/\/api\/attendance\/tabs\/\?.*$/, async route => {
    const params = new URL(route.request().url()).searchParams;
    if (params.get("active") !== "true" || params.get("offset") !== "0") return route.fallback();
    reads++;
    await held;
    await route.fallback();
  });
  await page.getByRole("button", { name: "Opções do atendimento", exact: true }).click();
  await page.getByRole("dialog", { name: "Opções do atendimento", exact: true }).getByRole("button", { name: "Atualizar", exact: true }).click();
  await expect.poll(() => reads).toBe(1);
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  const popup = await openTable(page);
  await expect(popup).toContainText("Comanda de teste");
  expect(reads).toBe(1);
  release();
});

test("release waits for a fresh canonical read after an older list refresh", async ({ page }) => {
  const { tables } = await setup(page, true, ["table.manage", "tab.open"], true);
  // Pause before mount so only the explicit interval below can initiate polling.
  // Real elapsed time and SSE reconnect timers must not add a third unrelated read.
  await page.clock.pauseAt(new Date("2026-10-08T21:01:00Z"));
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: /Mesa 02 Ocupada/ }).click();
  await page.getByRole("button", { name: "Grupo saiu · Liberar mesa", exact: true }).click();
  let reads = 0;
  let committed = false;
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/attendance/hospitality/tables/", async route => {
    reads++;
    const snapshot = structuredClone(tables);
    if (reads === 1) await held;
    await route.fulfill({ json: { table_service_enabled: true, results: snapshot } });
  });
  // A realtime update can start while the confirmation dialog is open.
  await page.clock.runFor(15000);
  await expect.poll(() => reads).toBe(1);
  await page.route("**/api/attendance/hospitality/tables/occupied/release/", route => {
    committed = true; tables[1].status = "DIRTY"; tables[1].active_occupancy = undefined;
    return route.fulfill({ json: {} });
  });
  await page.getByRole("button", { name: "Confirmar liberação", exact: true }).click();
  await expect.poll(() => committed).toBe(true);
  await expect(page.getByRole("dialog", { name: "Liberar mesa 02?", exact: true })).toBeVisible();
  release();
  await expect.poll(() => reads).toBe(2);
  await expect(page.locator(".attendanceTableDialog")).not.toBeVisible();
  await expect(page.getByRole("button", { name: /Mesa 02 Aguardando limpeza/ })).toBeVisible();
});
for (const width of [360, 390, 430, 1280]) test(`unified tables and popup journey at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await setup(page);
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await expect(page.getByRole("button", { name: "Contas", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Mesas", exact: true })).toHaveAttribute("aria-current", "page");
  await stable(page);
  await expect(page.getByRole("navigation", { name: "Filtrar mesas por estado" })).toHaveCount(0);
  await page.screenshot({ path: `visual-artifacts/029/unified/tables-${width}.png`, fullPage: true });
  const popup = await openTable(page);
  await expect(popup).toContainText("Mesa 02");
  await expect(popup.getByRole("heading", { name: "Comandas abertas" })).toHaveCount(0);
  await expect(popup.getByRole("button", { name: "Abrir comanda", exact: true })).toHaveCount(0);
  await addCatalogItem(page, "Fritas");
  await addCatalogItem(page, "Fritas");
  await expectCatalogQuantity(page, "Fritas", 2);
  await expect(popup.getByRole("button", { name: "Ver resumo", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await expect(popup.getByRole("button", { name: /^Enviar 2 itens/ })).toBeInViewport({ ratio: 1 });
  await page.screenshot({ path: `visual-artifacts/029/unified/catalog-${width}.png` });
  await attendanceDraft(page);
  await expect(popup.getByText("2× Fritas", { exact: true })).toBeVisible();
  await expect(popup.getByRole("button", { name: /^Enviar / })).toBeEnabled();
  await popup.getByRole("button", { name: "Voltar", exact: true }).click();
  await popup.getByRole("button", { name: "Voltar", exact: true }).click();
  await popup.getByRole("button", { name: "Conferir / fechar conta", exact: true }).click();
  await expect(popup.getByRole("region", { name: "Resumo da conta", exact: true })).toHaveCount(0);
  await expect(popup.getByText("R$ 24,00", { exact: true }).first()).toBeVisible();
  await closeAttendanceTab(page);
  await expect(popup).not.toBeVisible();
  await page.locator('button[data-tab-id="tab-test"]').click();
  await attendanceDraft(page);
  await expect(popup.getByText("2× Fritas", { exact: true })).toBeVisible();
  await layoutAndA11y(page);
});

test("A to B to A preserves drafts and returns focus to the selected table", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); await openTable(page);
  await addCatalogItem(page, "Fritas");
  await closeAttendanceTab(page);
  await expect(page.locator('button[data-tab-id="tab-test"]')).toBeFocused();
  await page.locator('button[data-tab-id="tab-other"]').click();
  await expectCatalogQuantity(page, "Fritas", 0);
  await addCatalogItem(page, "Omelete");
  await closeAttendanceTab(page); await page.locator('button[data-tab-id="tab-test"]').click();
  await expectCatalogQuantity(page, "Fritas", 1);
  await expectCatalogQuantity(page, "Omelete", 0);
});

test("table options dialog restores its page trigger without losing table context", async ({ page }) => {
  await setup(page); await page.goto("/attendance");
  await openAttendanceTable(page, "occupied");
  const table = page.locator(".ux2TablePage");
  await table.getByText("Opções da mesa", { exact: true }).click();
  const trigger = table.getByRole("button", { name: "Organizar mesa 02", exact: true });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Organizar mesa 02", exact: true });
  await expect(dialog).toBeVisible();
  await layoutAndA11y(page);
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await expect(table.locator('button[data-tab-id="tab-test"]')).toBeVisible();
});

test("command search keeps unknown reads distinct from empty", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByLabel("Buscar mesa ou comanda").fill("Comanda B");
  await expect(page.locator(".attendanceTable")).toHaveCount(1);
  await page.getByLabel("Buscar mesa ou comanda").fill("mesa inexistente");
  await expect(page.getByText("Nenhuma mesa encontrada. Ajuste a busca.")).toBeVisible();
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ status: 503, json: { code: "READ_UNAVAILABLE", message: "Leitura indisponível." } }));
  await page.reload(); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await expect(page.getByText("Mesas indisponíveis. Atualize para tentar novamente.")).toBeVisible();
  await expect(page.getByText("Nenhuma mesa cadastrada.")).toHaveCount(0);
});

test("search finds standalone tabs and exposes matches without opening a table", async ({ page }) => {
  await setup(page);
  const standalone = { id: "tab-standalone", display_label: "Comanda da varanda", state: "OPEN", version: 1, exposure_cents: 0, payable_cents: 0, orders: [] };
  await page.route(/\/api\/attendance\/tabs\/(\?.*)?$/, route => route.fulfill({ json: { results: [standalone], next_offset: null } }));
  await page.route("**/api/attendance/tabs/tab-standalone/", route => route.fulfill({ json: standalone }));
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByLabel("Buscar mesa ou comanda").fill("varanda");
  const others = page.getByRole("region", { name: "Outras comandas" });
  await expect(page.locator(".attendanceTable")).toHaveCount(0);
  await expect(others.getByRole("button", { name: /Comanda da varanda/ })).toBeVisible();
  await others.getByRole("button", { name: /Comanda da varanda/ }).click();
  await expect(attendanceWorkspace(page)).toBeVisible();
});

test("rejected context read never reveals the previous tab as the new target", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); const popup = await openTable(page); await closeAttendanceTab(page);
  await page.route("**/api/attendance/tabs/tab-other/?*", route => route.fulfill({ status: 409, json: { code: "CONFLICT", message: "A comanda mudou de mesa." } }));
  await page.locator('button[data-tab-id="tab-other"]').click();
  await expect(page.getByRole("alert").filter({ hasText: "A comanda mudou de mesa" })).toContainText("A comanda mudou de mesa");
  await expect(popup).not.toBeVisible();
});

for (const target of ["available", "occupied", "lost"]) test(`open a tab from its table: ${target}`, async ({ page }) => {
  const { tables } = await setup(page); const attempts: unknown[] = [];
  const tableId = target === "occupied" ? "occupied" : "available";
  const path = target === "occupied" ? "hospitality/occupancies/visit/tabs/open/" : "hospitality/tables/available/service/open-tab/";
  await page.route(`**/api/attendance/${path}`, route => {
    attempts.push(route.request().postDataJSON());
    if (target === "lost" && attempts.length === 1) return route.abort();
    return route.fulfill({ json: { tab_id: "tab-new", table_id: tableId, table_label: target === "occupied" ? "02" : "01" } });
  });
  await page.route("**/api/attendance/tabs/tab-new/", route => route.fulfill({ json: { id: "tab-new", display_label: "Comanda de teste", table_label: target === "occupied" ? "02" : "01", state: "OPEN", exposure_cents: 0, payable_cents: 0, orders: [] } }));
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  if (target === "available") { const previous = await openTable(page); await addCatalogItem(page, "Fritas"); await closeAttendanceTab(page); await expect(previous).not.toBeVisible(); await page.locator(".ux2TablePage").getByRole("button", { name: "Voltar", exact: true }).click(); }
  await page.getByRole("button", { name: new RegExp(`Mesa ${tables.find(table => table.id === tableId)!.label} `) }).click();
  await page.getByRole("button", { name: "＋ Abrir nova comanda", exact: true }).click();
  const form = page.getByRole("dialog", { name: /Nova comanda/ });
  await expect(form.getByRole("button", { name: "Abrir e pedir", exact: true })).toBeDisabled();
  await form.getByLabel("Nome ou apelido").fill("   ");
  await expect(form.getByRole("button", { name: "Abrir e pedir", exact: true })).toBeDisabled();
  await form.getByLabel("Nome ou apelido").fill("Comanda de teste");
  await form.getByRole("button", { name: "Abrir e pedir", exact: true }).click();
  if (target === "lost") {
    await expect(form.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
    await form.getByRole("button", { name: "Verificar mesma intenção", exact: true }).click();
    expect(attempts[1]).toEqual(attempts[0]);
  }
  expect(attempts[0]).toMatchObject({ display_label: "Comanda de teste", ...(target === "occupied" ? { expected_generation: 7 } : {}) });
  await expect(attendanceWorkspace(page)).toBeVisible();
  await expect(attendanceWorkspace(page).getByRole("group", { name: "Categorias", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  if (target === "available") { await closeAttendanceTab(page); await page.locator(".ux2TablePage").getByRole("button", { name: "Voltar", exact: true }).click(); await page.getByRole("button", { name: /Mesa 02 Ocupada/ }).click(); await page.locator('button[data-tab-id="tab-test"]').click(); await expectCatalogQuantity(page, "Fritas", 1); }
});

test("uncertain order locks popup and reload retries the identical original intent", async ({ page }) => {
  const { tabs } = await setup(page); const attempts: unknown[] = [];
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", route => {
    attempts.push(route.request().postDataJSON());
    if (attempts.length === 1) return route.abort();
    tabs[0].orders.push({ id: "confirmed", status: "CONFIRMED", confirmed_at: "2026-10-08T21:00:00Z", items: [] });
    return route.fulfill({ json: { id: "confirmed", tab_id: "tab-test" } });
  });
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); const popup = await openTable(page);
  await addCatalogItem(page, "Fritas");
  await attendanceDraft(page);
  await popup.getByRole("button", { name: /^Enviar / }).click();
  await expect(popup.getByRole("button", { name: "Verificar mesmo pedido", exact: true })).toBeEnabled();
  await expect(popup.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
  await page.keyboard.press("Escape"); await expect(popup).toBeVisible();
  await page.reload(); await expect(popup).toBeVisible();
  await popup.getByRole("button", { name: "Verificar mesmo pedido", exact: true }).click();
  await expect(popup.getByRole("region", { name: "Último pedido confirmado", exact: true })).toContainText("Pedido #confirmed confirmado");
  expect(attempts).toHaveLength(2); expect(attempts[1]).toEqual(attempts[0]);
  await expect(popup.getByRole("button", { name: "Voltar", exact: true })).toBeEnabled();
});

test("nested customization and discard dialogs retain the parent and draft", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); const popup = await openTable(page);
  await addCatalogItem(page, "Fritas");
  await attendanceDraft(page);
  await popup.getByRole("button", { name: "← Continuar escolhendo itens", exact: true }).click();
  await chooseCatalogItem(page, "Fritas");
  await expect(page.getByRole("dialog", { name: "Personalizar Fritas", exact: true })).toBeVisible();
  await layoutAndA11y(page); await page.keyboard.press("Escape"); await expect(popup).toBeVisible();
  await attendanceDraft(page);
  await popup.getByRole("button", { name: "Descartar rascunho", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Descartar rascunho?", exact: true })).toBeVisible();
  await page.keyboard.press("Escape"); await expect(popup.getByText("1× Fritas", { exact: true })).toBeVisible();
  await closeAttendanceTab(page);
  await page.locator(".ux2TablePage").getByRole("button", { name: "Voltar", exact: true }).click();
  await page.getByRole("button", { name: "Histórico", exact: true }).click();
  await expect(page.getByRole("dialog", { name: /Histórico/ })).toBeVisible();
  await page.keyboard.press("Escape"); await expect(page.getByRole("button", { name: "Histórico", exact: true })).toBeFocused();
});

test("missing capability keeps tab creation out of the table", async ({ page }) => {
  await setup(page, true, []); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: /Mesa 01 Disponível/ }).click();
  await expect(page.getByRole("button", { name: "＋ Abrir nova comanda", exact: true })).toHaveCount(0);
});

test("unavailable draft item can decrease but cannot increase or be sent", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); const popup = await openTable(page);
  await addCatalogItem(page, "Fritas");
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [{ id: "fries", name: "Fritas", active: true, availability: "UNAVAILABLE", price_cents: 7200 }] } }));
  await page.clock.runFor(15000);
  const category = await openProductCategory(page, "Fritas");
  await expect(category.getByRole("button", { name: "Adicionar Fritas", exact: true })).toBeDisabled();
  await expect(category.getByRole("button", { name: "Personalizar Fritas", exact: true })).toBeDisabled();
  await attendanceDraft(page);
  await expect(popup.getByRole("button", { name: /^Enviar / })).toBeDisabled();
  await expect(popup.getByRole("button", { name: "Aumentar Fritas", exact: true })).toBeDisabled();
  await popup.getByRole("button", { name: "Reduzir Fritas", exact: true }).click();
  await expect(popup.locator(".ux2ReviewRow")).toHaveCount(0);
});

for (const failure of ["unavailable", "stale"] as const) {
  test(`customization opened before refresh cannot add a ${failure} product`, async ({ page }) => {
    await setup(page);
    await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
    const popup = await openTable(page);
    const customize = await chooseCatalogItem(page, "Fritas");
    const add = customize.getByRole("button", { name: /Adicionar ·/ });
    await expect(add).toBeEnabled();
    await page.route("**/api/attendance/catalog/products/", route =>
      failure === "unavailable"
        ? route.fulfill({ json: { results: [{ id: "fries", name: "Fritas", active: true, availability: "UNAVAILABLE", price_cents: 7200 }] } })
        : route.fulfill({ status: 503, json: { message: "Catálogo indisponível" } }),
    );
    await page.clock.runFor(15000);
    await expect(add).toBeDisabled();
    await expect(customize.getByText("Produto indisponível ou catálogo desatualizado.")).toBeVisible();
    await customize.getByRole("region", { name: "Configurar Fritas" }).getByRole("button", { name: "Voltar", exact: true }).click();
    await expect(popup.getByRole("button", { name: "Adicionar Fritas", exact: true })).toBeDisabled();
    await expect(popup.getByRole("status", { name: "Quantidade de Fritas", exact: true })).toHaveText("0");
    await expect(popup.locator(".ux2ReviewRow")).toHaveCount(0);
  });
}

test("legacy venue can still create a standalone tab in the unified area", async ({ page }) => {
  await setup(page, false); let writes = 0;
  await page.route("**/api/attendance/tabs/", route => {
    if (route.request().method() !== "POST") return route.fallback();
    writes++;
    return route.fulfill({ json: { id: "standalone", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 0, payable_cents: 0, orders: [] } });
  });
  await page.route("**/api/attendance/tabs/standalone/", route => route.fulfill({ json: { id: "standalone", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 0, payable_cents: 0, orders: [] } }));
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();

  await page.getByRole("button", { name: "Abrir comanda sem mesa", exact: true }).click();
  const form = page.getByRole("dialog", { name: "Comandas", exact: true });
  await expect(form.getByRole("button", { name: "Abrir comanda", exact: true })).toBeDisabled();
  await form.getByLabel("Nome ou apelido", { exact: true }).fill("   ");
  await expect(form.getByRole("button", { name: "Abrir comanda", exact: true })).toBeDisabled();
  await form.getByLabel("Nome ou apelido", { exact: true }).fill("Comanda de teste");
  await form.getByRole("button", { name: "Abrir comanda", exact: true }).click();
  const popup = attendanceWorkspace(page);
  await expect(popup.getByRole("group", { name: "Categorias", exact: true })).toBeVisible();
  expect(writes).toBe(1);
});

for (const readbackFails of [false, true]) test(`release and direct cleaning return only after canonical read: failure=${readbackFails}`, async ({ page }) => {
  const { tables } = await setup(page, true, ["table.manage", "tab.open"], true);
  const paths: string[] = [];
  let released = false;
  await page.route("**/api/attendance/hospitality/tables/occupied/release/", route => {
    paths.push("release"); released = true; tables[1].status = "DIRTY"; tables[1].active_occupancy = undefined;
    return route.fulfill({ json: {} });
  });
  await page.route("**/api/attendance/hospitality/tables/occupied/cleaning/start/", route => { paths.push("start"); tables[1].status = "CLEANING"; return route.fulfill({ json: {} }); });
  await page.route("**/api/attendance/hospitality/tables/occupied/cleaning/complete/", route => {
    paths.push("complete"); tables[1].status = "AVAILABLE";
    return route.fulfill({ json: {} });
  });
  await page.route("**/api/attendance/hospitality/tables/", route => readbackFails && released ? route.fulfill({ status: 503, json: { code: "READ_UNAVAILABLE", message: "Leitura indisponível." } }) : route.fulfill({ json: { table_service_enabled: true, results: tables } }));
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: /Mesa 02 Ocupada/ }).click();
  await page.getByRole("button", { name: "Grupo saiu · Liberar mesa", exact: true }).click();
  await page.getByRole("button", { name: "Confirmar liberação", exact: true }).click();
  if (readbackFails) {
    await expect(page.getByRole("dialog", { name: "Liberar mesa 02?", exact: true })).toBeVisible();
    await expect(page.getByRole("dialog", { name: "Liberar mesa 02?", exact: true }).getByRole("alert")).toContainText("Leitura indisponível");
    expect(paths).toEqual(["release"]); return;
  }
  await expect(page.locator(".attendanceTableDialog")).not.toBeVisible();
  await page.getByRole("button", { name: /Mesa 02 Aguardando limpeza/ }).click();
  const dirty = page.locator(".ux2TablePage");
  await expect(dirty.getByRole("button", { name: "Mesa limpa · Disponibilizar", exact: true })).toHaveCount(0);
  await dirty.getByRole("button", { name: "Iniciar limpeza", exact: true }).click();
  await expect(dirty.getByText("Em limpeza", { exact: true }).first()).toBeVisible();
  await dirty.getByRole("button", { name: "Mesa limpa · Disponibilizar", exact: true }).click();
  await expect(dirty).not.toBeVisible();
  await expect(page.getByRole("button", { name: /Mesa 02 Disponível/ })).toBeVisible();
  expect(paths).toEqual(["release", "start", "complete"]);
});

for (const responseLost of [false, true]) test(`release retains confirmed occupancy across refresh: lost response=${responseLost}`, async ({ page }) => {
  const { tables } = await setup(page, true, ["table.manage", "tab.open"], true);
  await page.clock.pauseAt(new Date("2026-10-08T21:01:00Z"));
  const original = structuredClone(tables[1].active_occupancy!);
  const payloads: unknown[] = [];
  await page.route("**/api/attendance/hospitality/tables/occupied/release/", route => {
    payloads.push(route.request().postDataJSON());
    if (responseLost && payloads.length === 1) return route.abort();
    return route.fulfill({ status: 409, json: { code: "STALE_OCCUPANCY", message: "Ocupação original alterada." } });
  });
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: /Mesa 02 Ocupada/ }).click();
  await page.getByRole("button", { name: "Grupo saiu · Liberar mesa", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Liberar mesa 02?", exact: true });
  const confirm = dialog.getByRole("button", { name: "Confirmar liberação", exact: true });
  if (responseLost) {
    await confirm.click();
    await expect.poll(() => payloads.length).toBe(1);
    await expect(confirm).toBeEnabled();
  }
  tables[1].active_occupancy = { ...original, id: "replacement-occupancy", generation: original.generation + 1 };
  const refreshed = page.waitForResponse(response => response.url().endsWith("/api/attendance/hospitality/tables/"));
  await page.clock.runFor(15000);
  await refreshed;
  await expect(page.getByText("Atualizando…", { exact: true })).toHaveCount(0);
  await expect(confirm).toBeDisabled();
  await expect(dialog.getByRole("alert").filter({ hasText: "A ocupação mudou" })).toBeVisible();
  expect(payloads).toEqual(Array(responseLost ? 1 : 0).fill({ expected_occupancy_id: original.id, expected_generation: original.generation }));
  expect(tables[1].active_occupancy.id).toBe("replacement-occupancy");
});


test("return focus waits for the held core refresh to recover online", async ({ page }) => {
  const { tables } = await setup(page);
  await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click(); await openTable(page);
  await addCatalogItem(page, "Fritas");
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ status: 503, json: { message: "Core temporariamente indisponível" } }));
  await page.clock.runFor(15_000);
  await expect(page.getByRole("button", { name: "Opções do atendimento", exact: true })).toContainText("Desatualizado");
  let release!: () => void, reads = 0;
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/attendance/hospitality/tables/", async route => {
    reads++; await held;
    await route.fulfill({ json: { table_service_enabled: true, results: tables } });
  });
  try {
    await closeAttendanceTab(page);
    await expect.poll(() => reads).toBe(1);
    await expect(page.locator('button[data-tab-id="tab-test"]')).toBeDisabled();
    await expect(page.locator('button[data-tab-id="tab-test"]')).not.toBeFocused();
  } finally { release(); }
  await expect(page.locator('button[data-tab-id="tab-test"]')).toBeEnabled();
  await expect(page.locator('button[data-tab-id="tab-test"]')).toBeFocused();
});
