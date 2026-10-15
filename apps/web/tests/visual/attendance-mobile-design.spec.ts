import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

async function setup(page: Page, enabled = true, capabilities = ["table.manage", "tab.open"]) {
  await fixture(page, "normal", true);
  const tabs = ["tab-test", "tab-other"].map((id, index) => ({ id, display_label: index ? "Comanda B" : "Comanda de teste", table_label: "02", state: "OPEN", version: 1, exposure_cents: 2400, payable_cents: 2400, orders: [{ id: "original", items: [{ id: `item-${id}`, product_id: "fries", product_name: "Fritas", quantity: 2, unit_price_cents: 1200, state: "READY" }] }] }));
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
  await page.getByRole("button", { name: /Mesa 02 Ocupada/ }).click();
  await page.locator('button[data-tab-id="tab-test"]').click();
  const popup = page.locator(".attendanceOrderDialog");
  await expect(popup).toBeVisible();
  return popup;
}
for (const width of [360, 390, 430, 1280]) test(`unified tables and popup journey at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await setup(page);
  await page.goto("/attendance");
  await expect(page.getByRole("button", { name: "Contas", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Mesas e comandas", exact: true })).toHaveAttribute("aria-current", "page");
  await stable(page);
  await page.screenshot({ path: `visual-artifacts/029/unified/tables-${width}.png`, fullPage: true });
  const popup = await openTable(page);
  await expect(popup).toContainText("Mesa 02");
  await expect(popup.getByRole("heading", { name: "Comandas abertas" })).toHaveCount(0);
  await expect(popup.getByRole("button", { name: "Abrir comanda", exact: true })).toHaveCount(0);
  await popup.getByRole("button", { name: "Adicionar Fritas", exact: true }).click();
  await popup.getByRole("button", { name: "Adicionar Fritas", exact: true }).click();
  await expect(popup.getByRole("status", { name: "Quantidade selecionada de Fritas", exact: true })).toHaveText("2");
  await expect(popup.getByRole("navigation", { name: "Nesta comanda" })).toContainText("2 itens");
  await layoutAndA11y(page);
  await expect(popup.locator(":scope > button")).toBeInViewport({ ratio: 1 });
  await page.screenshot({ path: `visual-artifacts/029/unified/catalog-${width}.png` });
  await popup.getByRole("button", { name: /Pedido atual/ }).click();
  await expect(popup.getByRole("region", { name: "Pedido atual" }).getByText("2× Fritas", { exact: true })).toBeVisible();
  await expect(popup.getByRole("button", { name: /Confirmar pedido/ })).toBeEnabled();
  await popup.getByRole("button", { name: "Conta", exact: true }).click();
  await expect(popup.getByText("R$ 12,00 un. · R$ 24,00", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(popup).not.toBeVisible();
  await page.locator('button[data-tab-id="tab-test"]').click();
  await popup.getByRole("button", { name: /Pedido atual/ }).click();
  await expect(popup.getByRole("region", { name: "Pedido atual" }).getByText("2× Fritas", { exact: true })).toBeVisible();
  await layoutAndA11y(page);
});

test("A to B to A preserves drafts and returns focus to the selected table", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); const popup = await openTable(page);
  await popup.getByRole("button", { name: "Adicionar Fritas", exact: true }).click();
  await page.keyboard.press("Escape");
  await expect(page.locator('button[data-tab-id="tab-test"]')).toBeFocused();
  await page.locator('button[data-tab-id="tab-other"]').click();
  await expect(popup.getByRole("status", { name: "Quantidade selecionada de Fritas", exact: true })).toHaveText("0");
  await popup.getByRole("button", { name: "Adicionar Omelete", exact: true }).click();
  await page.keyboard.press("Escape"); await page.locator('button[data-tab-id="tab-test"]').click();
  await expect(popup.getByRole("status", { name: "Quantidade selecionada de Fritas", exact: true })).toHaveText("1");
  await expect(popup.getByRole("status", { name: "Quantidade selecionada de Omelete", exact: true })).toHaveText("0");
});

test("table state and combined command search keep unknown reads distinct from empty", async ({ page }) => {
  await setup(page); await page.goto("/attendance");
  await page.getByLabel("Buscar mesa ou comanda").fill("Comanda B");
  await expect(page.locator(".attendanceTable")).toHaveCount(1);
  await page.getByRole("button", { name: "Disponível (1)", exact: true }).click();
  await expect(page.getByText("Nenhuma mesa encontrada. Ajuste a busca ou o estado.")).toBeVisible();
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ status: 503, json: { message: "Leitura indisponível." } }));
  await page.reload();
  await expect(page.getByText("Mesas indisponíveis. Atualize para tentar novamente.")).toBeVisible();
  await expect(page.getByText("Nenhuma mesa cadastrada.")).toHaveCount(0);
});

test("search finds standalone tabs and exposes matches without opening a table", async ({ page }) => {
  await setup(page);
  const standalone = { id: "tab-standalone", display_label: "Comanda da varanda", state: "OPEN", version: 1, exposure_cents: 0, payable_cents: 0, orders: [] };
  await page.route(/\/api\/attendance\/tabs\/(\?.*)?$/, route => route.fulfill({ json: { results: [standalone], next_offset: null } }));
  await page.route("**/api/attendance/tabs/tab-standalone/", route => route.fulfill({ json: standalone }));
  await page.goto("/attendance");
  await page.getByLabel("Buscar mesa ou comanda").fill("varanda");
  const others = page.getByRole("region", { name: "Outras comandas" });
  await expect(page.locator(".attendanceTable")).toHaveCount(0);
  await expect(others.getByRole("button", { name: /Comanda da varanda/ })).toBeVisible();
  await others.getByRole("button", { name: /Comanda da varanda/ }).click();
  await expect(page.locator(".attendanceOrderDialog")).toBeVisible();
});

test("rejected context read never reveals the previous tab as the new target", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); const popup = await openTable(page); await page.keyboard.press("Escape");
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
  await page.goto("/attendance");
  if (target === "available") { const previous = await openTable(page); await previous.getByRole("button", { name: "Adicionar Fritas", exact: true }).click(); await page.keyboard.press("Escape"); }
  await page.getByRole("button", { name: new RegExp(`Mesa ${tables.find(table => table.id === tableId)!.label} `) }).click();
  await page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
  const form = page.getByRole("dialog", { name: /Nova comanda/ });
  await form.getByLabel("Nome da comanda (opcional)").fill("Comanda de teste");
  await form.getByRole("button", { name: "Abrir e pedir", exact: true }).click();
  if (target === "lost") {
    await expect(form.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
    await form.getByRole("button", { name: "Verificar mesma intenção", exact: true }).click();
    expect(attempts[1]).toEqual(attempts[0]);
  }
  expect(attempts[0]).toMatchObject({ display_label: "Comanda de teste", ...(target === "occupied" ? { expected_generation: 7 } : {}) });
  await expect(page.locator(".attendanceOrderDialog")).toBeVisible();
  await expect(page.locator(".attendanceOrderDialog").getByRole("button", { name: "Adicionar Fritas", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  if (target === "available") { await page.keyboard.press("Escape"); await page.getByRole("button", { name: /Mesa 02 Ocupada/ }).click(); await page.locator('button[data-tab-id="tab-test"]').click(); await expect(page.locator(".attendanceOrderDialog").getByRole("status", { name: "Quantidade selecionada de Fritas", exact: true })).toHaveText("1"); }
});

test("uncertain order locks popup and reload retries the identical original intent", async ({ page }) => {
  const { tabs } = await setup(page); const attempts: unknown[] = [];
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", route => {
    attempts.push(route.request().postDataJSON());
    if (attempts.length === 1) return route.abort();
    tabs[0].orders.push({ id: "confirmed", items: [] });
    return route.fulfill({ json: { id: "confirmed", tab_id: "tab-test" } });
  });
  await page.goto("/attendance"); const popup = await openTable(page);
  await popup.getByRole("button", { name: "Adicionar Fritas", exact: true }).click();
  await popup.getByRole("button", { name: /Pedido atual/ }).click();
  await popup.getByRole("button", { name: /Confirmar pedido/ }).click();
  await expect(popup.getByRole("button", { name: "Verificar mesmo pedido", exact: true })).toBeEnabled();
  await expect(popup.getByRole("button", { name: "Voltar", exact: true })).toBeDisabled();
  await page.keyboard.press("Escape"); await expect(popup).toBeVisible();
  await page.reload(); await expect(popup).toBeVisible();
  await popup.getByRole("button", { name: /Pedido atual/ }).click();
  await popup.getByRole("button", { name: "Verificar mesmo pedido", exact: true }).click();
  await expect(popup.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(attempts).toHaveLength(2); expect(attempts[1]).toEqual(attempts[0]);
  await expect(popup.getByRole("button", { name: "Voltar", exact: true })).toBeEnabled();
});

test("nested customization and discard dialogs retain the parent and draft", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); const popup = await openTable(page);
  await popup.getByRole("button", { name: "Adicionar Fritas", exact: true }).click();
  await popup.getByRole("button", { name: /Pedido atual/ }).click();
  await popup.getByRole("button", { name: "Editar", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Personalizar Fritas", exact: true })).toBeVisible();
  await layoutAndA11y(page); await page.keyboard.press("Escape"); await expect(popup).toBeVisible();
  await popup.getByRole("button", { name: "Descartar rascunho", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Descartar rascunho?", exact: true })).toBeVisible();
  await page.keyboard.press("Escape"); await expect(popup.getByText("1× Fritas", { exact: true })).toBeVisible();
  await popup.getByRole("button", { name: "Histórico", exact: true }).click();
  await expect(page.getByRole("dialog", { name: /Histórico/ })).toBeVisible();
  await page.keyboard.press("Escape"); await expect(popup).toBeVisible();
});

test("missing capability keeps tab creation out of the table", async ({ page }) => {
  await setup(page, true, []); await page.goto("/attendance");
  await page.getByRole("button", { name: /Mesa 01 Disponível/ }).click();
  await expect(page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true })).toHaveCount(0);
});

test("unavailable draft item can decrease but cannot increase or be sent", async ({ page }) => {
  await setup(page); await page.goto("/attendance"); const popup = await openTable(page);
  await popup.getByRole("button", { name: "Adicionar Fritas", exact: true }).click();
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [{ id: "fries", name: "Fritas", active: true, availability: "UNAVAILABLE", price_cents: 7200 }] } }));
  await page.clock.runFor(15000);
  await expect(popup.getByRole("button", { name: "Adicionar Fritas", exact: true })).toBeDisabled();
  await expect(popup.locator(".posProduct").filter({ hasText: "Fritas" }).getByRole("button", { name: "Personalizar" })).toBeDisabled();
  await popup.getByRole("button", { name: /Pedido atual/ }).click();
  // Editing/removing an existing draft remains possible after inventory changes.
  await popup.getByRole("button", { name: "Editar", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Personalizar Fritas", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(popup.getByRole("button", { name: /Confirmar pedido/ })).toBeDisabled();
  await popup.getByRole("button", { name: "Diminuir quantidade de Fritas", exact: true }).click();
  await expect(popup.getByRole("region", { name: "Pedido atual" }).locator("article")).toHaveCount(0);
});

for (const failure of ["unavailable", "stale"] as const) {
  test(`customization opened before refresh cannot add a ${failure} product`, async ({ page }) => {
    await setup(page);
    await page.goto("/attendance");
    const popup = await openTable(page);
    await popup.locator(".posProduct").filter({ hasText: "Fritas" }).getByRole("button", { name: "Personalizar" }).click();
    const customize = page.getByRole("dialog", { name: "Personalizar Fritas", exact: true });
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
    await customize.getByRole("button", { name: "Voltar" }).click();
    await expect(popup.locator(".posProduct").filter({ hasText: "Fritas" }).getByRole("button", { name: "Personalizar" })).toBeDisabled();
    await popup.getByRole("button", { name: /Pedido atual/ }).click();
    await expect(popup.getByRole("region", { name: "Pedido atual" }).locator("article")).toHaveCount(0);
  });
}

test("legacy venue can still create a standalone tab in the unified area", async ({ page }) => {
  await setup(page, false); let writes = 0;
  await page.route("**/api/attendance/tabs/", route => {
    if (route.request().method() !== "POST") return route.fallback();
    writes++;
    return route.fulfill({ json: { id: "standalone", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 0, payable_cents: 0, orders: [] } });
  });
  await page.goto("/attendance");
  await page.getByRole("region", { name: "Outras comandas" }).locator("summary").click();
  await page.getByRole("button", { name: "Abrir comanda sem mesa", exact: true }).click();
  const popup = page.locator(".attendanceOrderDialog");
  await popup.getByLabel("Nome da Comanda", { exact: true }).fill("Comanda de teste");
  await popup.getByRole("button", { name: "Abrir comanda", exact: true }).click();
  await expect(popup.getByRole("button", { name: "Adicionar Fritas", exact: true })).toBeVisible();
  expect(writes).toBe(1);
});
