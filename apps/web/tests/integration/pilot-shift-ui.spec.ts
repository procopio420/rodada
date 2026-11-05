import { expect, test, type Page } from "./fixtures";
import { addCatalogItem } from "../visual/category-actions";
import { writeFile } from "node:fs/promises";

// Spec033 AC-12..16/20. Every business mutation is a UI action. The fixture
// seeds only identities/catalog/cash point; this helper permits GET readback only.
async function read(page: Page, path: string) {
  return page.evaluate(async path => {
    const response = await fetch(`/api/pos/${path}`, { method: "GET" });
    if (!response.ok) throw new Error(`Readback ${response.status}: ${path}`);
    return response.json();
  }, path);
}

test("entire pilot shift through Web UI with two Tabs and read-only verification", async ({ page, browser }, info) => {
  test.setTimeout(150_000);
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/manage/setup");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-owner");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Preparar estabelecimento" })).toBeVisible();
  await page.getByLabel("Nome ou identificação").fill("Turno UI");
  await page.getByLabel("Pedidos pelo QR").selectOption("DIRECT");
  await page.getByRole("button", { name: "Cadastrar mesa", exact: true }).click();
  await expect(page.getByRole("list", { name: "Mesas cadastradas" })).toContainText("Turno UI");
  const table = (await read(page, "hospitality/tables/")).results.find((t: { label: string }) => t.label === "Turno UI");
  await page.goto("/cash");
  await page.getByLabel("Fundo inicial").fill("100,00");
  await page.getByRole("button", { name: "Confirmar abertura", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Caixa aberto", exact: true })).toBeVisible();
  const point = (await read(page, "cash/points/")).results[0];
  const shiftId = point.active_shift.id;

  await page.goto("/attendance");
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: /^Mesa Turno UI/ }).click();
  await page.getByRole("button", { name: "＋ Abrir nova comanda", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: /Nova comanda · Mesa Turno UI/ });
  await dialog.getByLabel("Nome ou apelido").fill("Turno UI staff");
  await dialog.getByRole("button", { name: "Abrir e pedir", exact: true }).click();
  await addCatalogItem(page, "Bar E2E item");
  await addCatalogItem(page, "Kitchen E2E item");
  const workspace = page.getByRole("region", { name: "Comanda selecionada", exact: true });
  await workspace.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await workspace.getByRole("button", { name: /^Enviar 2 itens/ }).click();
  await expect(workspace.getByRole("button", { name: "Conferir / fechar conta", exact: true })).toBeVisible();
  const staff = (await read(page, "tabs/")).results.find((t: { display_label: string }) => t.display_label === "Turno UI staff");
  const staffDetail = await read(page, `tabs/${staff.id}/`);
  expect(staffDetail.orders).toHaveLength(1);
  expect(staffDetail.orders[0].items.every((i: { state: string }) => i.state === "NEW")).toBe(true);

  const guestContext = await browser.newContext({ baseURL: info.project.use.baseURL });
  try {
    const guest = await guestContext.newPage();
    guest.on("pageerror", error => errors.push(error.message));
    await guest.goto(`/guest/${table.public_token}`);
    await guest.getByText("Adicionar nome ou apelido (opcional)", { exact: true }).click();
    await guest.getByLabel("Seu nome ou apelido (opcional)").fill("Turno UI guest");
    await guest.getByRole("button", { name: "Abrir minha comanda", exact: true }).click();
    await expect(guest.getByRole("heading", { name: "Mesa Turno UI", exact: true })).toBeVisible();
    await guest.getByRole("button", { name: /^Bar E2E item/ }).click();
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    await expect(guest.getByRole("heading", { name: "Meus pedidos", exact: true })).toBeVisible();
    const guestTab = (await read(page, "tabs/")).results.find((t: { display_label: string }) => t.display_label === "Turno UI guest");
    const occupied = (await read(page, "hospitality/tables/")).results.find((t: { id: string }) => t.id === table.id);
    expect(occupied.active_occupancy.tabs.map((t: { id: string }) => t.id).sort()).toEqual([staff.id, guestTab.id].sort());

    for (const [route, label] of [["/bar", "Turno UI staff"], ["/kitchen", "Turno UI staff"], ["/bar", "Turno UI guest"]]) {
      await page.goto(route);
      await page.getByRole("button", { name: new RegExp(`^Iniciar preparo:.*${label}$`) }).click();
      await expect(page.getByRole("button", { name: new RegExp(`^Pronto:.*${label}$`) })).toBeVisible();
      await page.getByRole("button", { name: new RegExp(`^Pronto:.*${label}$`) }).click();
      await expect(page.getByRole("button", { name: new RegExp(`^Pronto:.*${label}$`) })).toHaveCount(0);
    }
    await page.goto("/attendance");
    await page.getByRole("button", { name: "Agora", exact: true }).click();
    await page.getByRole("button", { name: /^Entregas / }).click();
    const tasks = (await read(page, "dispatch/delivery/")).results;
    expect(tasks).toHaveLength(3);
    let remaining = tasks.length;
    while (remaining > 0) {
      const row = page.locator(".ux2DeliveryRow").first();
      const group = row.getByRole("button", { name: "Confirmar entrega", exact: true });
      if (await group.isVisible()) await group.click();
      else {
        await row.getByRole("button", { name: "Registrar entrega", exact: true }).click();
        await page.getByRole("dialog", { name: "Registrar entrega", exact: true }).getByRole("button", { name: "Confirmar entrega", exact: true }).click();
      }
      await expect.poll(async () => (await read(page, "dispatch/delivery/")).results.length).toBeLessThan(remaining);
      remaining = (await read(page, "dispatch/delivery/")).results.length;
      await expect(page.getByRole("button", { name: `Entregas ${remaining}`, exact: true })).toBeVisible();
    }
    expect((await read(page, "dispatch/delivery/")).results).toHaveLength(0);

    async function openAccount(id: string) {
      await page.goto("/attendance");
      await page.getByRole("button", { name: "Mesas", exact: true }).click();
      await page.getByRole("button", { name: /^Mesa Turno UI/ }).click();
      await page.locator(`button[data-tab-id="${id}"]`).click();
      await workspace.getByRole("button", { name: "Conferir / fechar conta", exact: true }).click();
    }
    await openAccount(staff.id);
    const receipt = page.getByRole("region", { name: "Recebimento em dinheiro", exact: true });
    await receipt.getByRole("button", { name: /^Receber R/ }).click();
    await receipt.getByLabel("Valor recebido (R$)", { exact: true }).fill("5,00");
    await receipt.getByRole("button", { name: "Registrar recebimento", exact: true }).click();
    await expect(receipt.getByText("Recebimento confirmado. Saldo atualizado.", { exact: true })).toBeVisible();
    expect((await read(page, `tabs/${staff.id}/`)).exposure_cents).toBe(1000);
    expect((await read(page, `tabs/${staff.id}/`)).state).toBe("OPEN");
    await receipt.getByRole("button", { name: /^Receber R/ }).click();
    await receipt.getByRole("button", { name: "Receber e encerrar comanda", exact: true }).click();
    await expect.poll(async () => (await read(page, `tabs/${staff.id}/`)).state).toBe("CLOSED");
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem("rodada.intent.pos-cash.v1"))).toBeNull();
    const tableState = async () => (await read(page, "hospitality/tables/")).results.find((t: { id: string }) => t.id === table.id).status;
    expect(await tableState()).toBe("OCCUPIED");
    expect((await read(page, `tabs/${guestTab.id}/`)).exposure_cents).toBe(500);
    await openAccount(guestTab.id);
    await receipt.getByRole("button", { name: /^Receber R/ }).click();
    await receipt.getByRole("button", { name: "Receber e encerrar comanda", exact: true }).click();
    await expect.poll(async () => (await read(page, `tabs/${guestTab.id}/`)).state).toBe("CLOSED");
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem("rodada.intent.pos-cash.v1"))).toBeNull();
    expect(await tableState()).toBe("OCCUPIED");
    await page.goto("/attendance");
    await page.getByRole("button", { name: "Mesas", exact: true }).click();
    await page.getByRole("button", { name: /^Mesa Turno UI/ }).click();
    const refreshDeliveries = page.getByRole("button", { name: "Atualizar entregas", exact: true });
    if (await refreshDeliveries.isVisible()) await refreshDeliveries.click();
    await page.getByRole("button", { name: "Grupo saiu · Liberar mesa", exact: true }).click();
    await page.getByRole("button", { name: "Confirmar liberação", exact: true }).click();
    await expect(page.getByRole("button", { name: /^Mesa Turno UI Aguardando limpeza/ })).toBeVisible();
    await page.getByRole("button", { name: /^Mesa Turno UI Aguardando limpeza/ }).click();
    await page.getByRole("button", { name: "Iniciar limpeza", exact: true }).click();
    await expect.poll(tableState).toBe("CLEANING");
    await page.getByRole("button", { name: "Mesa limpa · Disponibilizar", exact: true }).click();
    await expect.poll(tableState).toBe("AVAILABLE");
    await page.goto("/cash");
    await page.getByRole("button", { name: "Conferir caixa", exact: true }).click();
    await page.getByLabel("Contado", { exact: true }).fill("120,00");
    await page.getByRole("button", { name: "Confirmar fechamento", exact: true }).click();
    await expect.poll(async () => (await read(page, `cash/shifts/${shiftId}/`)).status).toBe("CLOSED");
    await page.getByLabel("Selecionar turno atual ou fechamento antigo").selectOption(shiftId);
    await expect(page.getByRole("heading", { name: "Turno fechado", exact: true })).toBeVisible();
    const closed = await read(page, `cash/shifts/${shiftId}/`);
    expect(closed.status).toBe("CLOSED");
    expect(closed.expected_cents).toBe(12000);
    expect(closed.counted_amount_cents).toBe(12000);
    expect(closed.discrepancy_cents).toBe(0);
    const finals = await Promise.all([read(page, `tabs/${staff.id}/`), read(page, `tabs/${guestTab.id}/`)]);
    expect(finals.map(t => t.exposure_cents)).toEqual([0, 0]);
    expect(finals.map(t => t.payments.length)).toEqual([2, 1]);
    expect(errors).toEqual([]);
    await page.screenshot({ path: info.outputPath("cash-closed-ui.png"), fullPage: true });
    const evidence = { business_mutations: "UI only; readback helper GET only", table_id: table.id,
      occupancy_id: occupied.active_occupancy.id, tab_ids: finals.map(t => t.id),
      order_ids: finals.flatMap(t => t.orders.map((o: { id: string }) => o.id)),
      payment_ids: finals.flatMap(t => t.payments.map((p: { id: string }) => p.id)),
      task_ids: tasks.map((t: { id: string }) => t.id), shift_id: shiftId,
      consumption_cents: 2000, cash_cents: 2000, opening_float_cents: 10000,
      expected_cents: closed.expected_cents, counted_cents: closed.counted_amount_cents,
      discrepancy_cents: closed.discrepancy_cents, table_status: await tableState() };
    await writeFile(info.outputPath("shift-ui.json"), JSON.stringify(evidence, null, 2));
    await info.attach("shift-ui", { path: info.outputPath("shift-ui.json"), contentType: "application/json" });
  } finally { await guestContext.close(); }
});
