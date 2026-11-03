import { expect, test, type Page } from "./fixtures";
import { writeFile } from "node:fs/promises";

// Spec033 AC-12..16/20: one persisted Web/BFF/API/PostgreSQL shift.
// Guest ordering and production use UI; setup, delivery and finance use real
// same-origin BFF commands. This is not a fully manual operator walkthrough.
async function api(page: Page, path: string, data?: unknown) {
  const result = await page.evaluate(async ({ path, data }) => {
    const response = await fetch(`/api/pos/${path}`, data === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return { status: response.status, body: await response.json() };
  }, { path, data });
  expect(result.status, path).toBeLessThan(300);
  return result.body;
}

test("approved Web pilot: two Tabs, mixed production, settlement, cash and table release", async ({ page, browser }, info) => {
  test.setTimeout(90_000);
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const point = (await api(page, "cash/points/")).results[0];
  const shift = await api(page, "cash/shifts/", { cash_point_id: point.id,
    opening_float_cents: 10000, business_date: "2026-11-03", idempotency_key: "pilot-shift-open" });
  const table = await api(page, "hospitality/tables/", { label: "Pilot integrated", guest_ordering_mode: "DIRECT" });
  const occupancy = await api(page, `hospitality/tables/${table.id}/occupy/`, {});
  const staff = await api(page, "tabs/", { display_label: "Pilot shift staff" });
  await api(page, `hospitality/occupancies/${occupancy.id}/tabs/`, { tab_id: staff.id });
  const products = (await api(page, "catalog/products/")).results;
  const bar = products.find((p: { name: string }) => p.name === "Bar E2E item");
  const kitchen = products.find((p: { name: string }) => p.name === "Kitchen E2E item");
  const intent = { idempotency_key: "pilot-mixed-order", lines: [
    { product_id: bar.id, quantity: 1 }, { product_id: kitchen.id, quantity: 1 },
  ] };
  const order = await api(page, `tabs/${staff.id}/orders/confirm/`, intent);
  expect((await api(page, `tabs/${staff.id}/orders/confirm/`, intent)).id).toBe(order.id);
  expect(order.items.every((i: { state: string }) => i.state === "NEW")).toBe(true);
  const guestContext = await browser.newContext({ baseURL: info.project.use.baseURL });
  try {
    const guest = await guestContext.newPage();
    await guest.goto(`/guest/${table.public_token}`);
    await guest.getByText("Adicionar nome ou apelido (opcional)", { exact: true }).click();
    await guest.getByLabel("Seu nome ou apelido (opcional)").fill("Pilot shift guest");
    await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    await expect(guest.getByRole("heading", { name: "Mesa Pilot integrated", exact: true })).toBeVisible();
    await guest.getByRole("button", { name: /^Bar E2E item/ }).click();
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    await expect(guest.getByRole("heading", { name: "Meus pedidos", exact: true })).toBeVisible();
    const guestTab = (await api(page, "tabs/")).results.find((t: { display_label: string }) => t.display_label === "Pilot shift guest");
    expect(guestTab.id).not.toBe(staff.id);
    const guestDetail = await api(page, `tabs/${guestTab.id}/`);
    expect(guestDetail.orders).toHaveLength(1);
    expect(guestDetail.orders[0].source).toBe("GUEST");

    for (const [route, label] of [["/bar", "Pilot shift staff"], ["/kitchen", "Pilot shift staff"], ["/bar", "Pilot shift guest"]]) {
      await page.goto(route);
      await page.getByRole("button", { name: new RegExp(`^Iniciar preparo:.*${label}$`) }).click();
      const tabId = label.endsWith("staff") ? staff.id : guestTab.id;
      const station = route === "/bar" ? "BAR" : "KITCHEN";
      const productId = station === "BAR" ? bar.id : kitchen.id;
      const item = (await api(page, `tabs/${tabId}/`)).orders[0].items.find((i: { product_id: string }) => i.product_id === productId);
      await expect.poll(async () => (await api(page, `tabs/${tabId}/`)).orders[0].items.find((i: { id: string }) => i.id === item.id).state).toBe("PREPARING");
      await page.getByRole("button", { name: new RegExp(`^Pronto:.*${label}$`) }).click();
      await expect.poll(async () => (await api(page, `tabs/${tabId}/`)).orders[0].items.find((i: { id: string }) => i.id === item.id).state).toBe("READY");
    }
    const tasks = (await api(page, "dispatch/delivery/")).results;
    expect(tasks).toHaveLength(3);
    const itemIds = [...order.items, ...guestDetail.orders[0].items].map((i: { id: string }) => i.id);
    for (const task of tasks) {
      expect(itemIds).toContain(task.order_item_id);
      expect(task.destination_table_id).toBe(table.id);
      expect((await api(page, `dispatch/delivery/${task.id}/complete/`, {})).state).toBe("DONE");
    }
    const partialIntent = { amount_cents: 500, amount_tendered_cents: 500,
      method: "CASH", cash_point_id: point.id, idempotency_key: "pilot-partial" };
    const partial = await api(page, `tabs/${staff.id}/payments/`, partialIntent);
    expect((await api(page, `tabs/${staff.id}/payments/`, partialIntent)).id).toBe(partial.id);
    const partialTab = await api(page, `tabs/${staff.id}/`);
    expect(partialTab.exposure_cents).toBe(1000);
    expect(partialTab.state).toBe("OPEN");
    expect(partialTab.payments).toHaveLength(1);
    const final = await api(page, `tabs/${staff.id}/payments/`, {
      amount_cents: 1000, method: "CARD", idempotency_key: "pilot-card" });
    expect((await api(page, `tabs/${staff.id}/`)).state).toBe("CLOSED");
    const tableState = async () => (await api(page, "hospitality/tables/")).results.find((t: { id: string }) => t.id === table.id).status;
    expect(await tableState()).toBe("OCCUPIED");
    expect((await api(page, `tabs/${guestTab.id}/`)).exposure_cents).toBe(500);
    const guestPayment = await api(page, `tabs/${guestTab.id}/payments/`, {
      amount_cents: 500, amount_tendered_cents: 1000, method: "CASH",
      cash_point_id: point.id, idempotency_key: "pilot-guest-cash" });
    expect((await api(page, `tabs/${guestTab.id}/`)).state).toBe("CLOSED");
    expect(await tableState()).toBe("OCCUPIED");
    await api(page, `hospitality/tables/${table.id}/release/`, {
      expected_occupancy_id: occupancy.id, expected_generation: occupancy.generation });
    expect(await tableState()).toBe("DIRTY");
    await api(page, `hospitality/tables/${table.id}/cleaning/start/`, {});
    expect(await tableState()).toBe("CLEANING");
    await api(page, `hospitality/tables/${table.id}/cleaning/complete/`, {});
    expect(await tableState()).toBe("AVAILABLE");
    const revoked = await guest.evaluate(async qr => {
      const r = await fetch("/api/guest/context/", { headers: { "X-Guest-Session": qr } });
      return { status: r.status, code: (await r.json()).code };
    }, table.public_token);
    expect(revoked).toEqual({ status: 403, code: "GUEST_SESSION_REVOKED" });
    const counting = await api(page, `cash/shifts/${shift.id}/count/start/`, {});
    expect(counting.expected_cents).toBe(11000);
    const closed = await api(page, `cash/shifts/${shift.id}/close/`, {
      counted_amount_cents: 11000, review_threshold_cents: 0, expected_version: counting.version });
    expect(closed.status).toBe("CLOSED");
    expect(closed.discrepancy_cents).toBe(0);
    await page.goto("/manage");
    await expect(page.getByText("Comandas abertas", { exact: true })).toBeVisible();
    await page.screenshot({ path: info.outputPath("management.png"), fullPage: true });
    // Public QR selectors and session/auth material intentionally omitted.
    const record = { table_id: table.id, occupancy_id: occupancy.id,
      tab_ids: [staff.id, guestTab.id], order_ids: [order.id, guestDetail.orders[0].id],
      task_ids: tasks.map((t: { id: string }) => t.id),
      payment_ids: [partial.id, final.id, guestPayment.id], shift_id: shift.id,
      consumption_cents: 2000, cash_cents: 1000, card_cents: 1000,
      opening_float_cents: 10000, expected_cents: closed.expected_cents,
      counted_amount_cents: closed.counted_amount_cents, discrepancy_cents: closed.discrepancy_cents,
      table_status: await tableState(), guest_revoked: revoked };
    const evidence = info.outputPath("canonical-shift.json");
    await writeFile(evidence, JSON.stringify(record, null, 2));
    await info.attach("canonical-shift", { path: evidence, contentType: "application/json" });
  } finally { await guestContext.close(); }
});
