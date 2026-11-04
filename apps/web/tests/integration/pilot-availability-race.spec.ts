import { expect, test, type Page } from "./fixtures";
import { addCatalogItem } from "../visual/category-actions";
import { chooseBarAvailability } from "../visual/station-availability-actions";
import { openNamedAttendanceTab } from "./attendance-helpers";
import { writeFile } from "node:fs/promises";

async function login(page: Page, operator: string) {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill(operator);
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
}
async function read(page: Page, path: string) {
  return page.evaluate(async path => {
    const response = await fetch(`/api/pos/${path}`, { method: "GET" });
    if (!response.ok) throw new Error(`Readback ${response.status}: ${path}`);
    return response.json();
  }, path);
}

// Spec033 AC-07 and Spec014 stale availability: genuine two-operator UI race.
// Only scheduling of the submitted request is controlled; no mocked response.
test.describe.configure({ mode: "serial" });
for (const station of ["BAR", "KITCHEN"] as const) test(`two UI operators: ${station} becomes unavailable after mixed cart submission`, async ({ page, browser }, info) => {
  test.setTimeout(90_000);
  const target = station === "BAR" ? "Bar E2E item" : "Kitchen E2E item";
  const label = `Availability race ${station}`;
  await login(page, "test-staff");
  await page.goto("/attendance");
  await openNamedAttendanceTab(page, label);
  await addCatalogItem(page, target);
  const workspace = page.getByRole("region", { name: "Comanda selecionada", exact: true });
  await workspace.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await workspace.getByRole("button", { name: /^Enviar 1 item/ }).click();
  await expect(workspace.getByRole("button", { name: "Conferir / fechar conta", exact: true })).toBeVisible();
  const tab = (await read(page, "tabs/")).results.find((t: { display_label: string }) => t.display_label === label);
  const before = await read(page, `tabs/${tab.id}/`);
  expect(before.orders).toHaveLength(1);
  const originalItem = before.orders[0].items[0];
  expect(originalItem.state).toBe("NEW");
  await addCatalogItem(page, "Bar E2E item");
  await addCatalogItem(page, "Kitchen E2E item");
  await workspace.getByRole("button", { name: "Ver resumo", exact: true }).click();
  const managerContext = await browser.newContext({ baseURL: info.project.use.baseURL });
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  let captured = false;
  let result: { status: number; code: string; message: string } | null = null;
  let attempts = 0;
  try {
    const manager = await managerContext.newPage();
    await login(manager, "test-manager");
    const staffSession = await page.evaluate(async () => (await fetch("/api/auth/me")).json());
    const managerSession = await manager.evaluate(async () => (await fetch("/api/auth/me")).json());
    expect(staffSession.staff.id).not.toBe(managerSession.staff.id);
    expect(staffSession.session.id).not.toBe(managerSession.session.id);
    await manager.goto(station === "BAR" ? "/bar" : "/kitchen");
    await page.route(/\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/, async route => {
      attempts++;
      const payload = route.request().postDataJSON();
      expect(payload.lines).toHaveLength(2);
      captured = true;
      await held;
      const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
      const body = await response.json();
      result = { status: response.status(), code: body.code, message: body.message };
      await route.fulfill({ response });
    });
    await workspace.getByRole("button", { name: /^Enviar 2 itens/ }).click();
    await expect.poll(() => captured).toBe(true);
    if (station === "BAR") {
      await chooseBarAvailability(manager, target);
      await manager.getByRole("button", { name: "Sim, indisponibilizar", exact: true }).click();
      await expect(manager.getByRole("dialog")).not.toBeVisible();
    } else await manager.getByRole("button", { name: `Indisponibilizar ${target}`, exact: true }).click();
    await expect.poll(async () => (await read(manager, "catalog/products/")).results.find((p: { name: string }) => p.name === target).availability).toBe("UNAVAILABLE");
    const product = (await read(manager, "catalog/products/")).results.find((p: { name: string }) => p.name === target);
    expect(product.availability).toBe("UNAVAILABLE");
    release();
    await expect.poll(() => result?.status).toBe(409);
    expect(result!.code).toBe("PRODUCTS_NOT_CONFIRMABLE");
    expect(attempts).toBe(1);
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem("rodada.intent.staff-order.v1"))).toBeNull();
    await expect(workspace.getByText(result!.message, { exact: true })).toBeVisible();
    await expect(workspace.getByText("2 item(ns) não enviados.", { exact: true })).toBeVisible();
    await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
    await workspace.getByRole("button", { name: "Ver resumo", exact: true }).click();
    await expect(workspace.getByRole("button", { name: "Aumentar Bar E2E item", exact: true })).toBeVisible();
    await expect(workspace.getByRole("button", { name: "Aumentar Kitchen E2E item", exact: true })).toBeVisible();
    const after = await read(page, `tabs/${tab.id}/`);
    for (const key of ["orders", "charges_cents", "payments_cents", "payments", "exposure_cents"]) expect(after[key]).toEqual(before[key]);
    expect(after.orders[0].items[0].id).toBe(originalItem.id);
    expect(after.orders[0].items[0].state).toBe("NEW");
    await page.screenshot({ path: info.outputPath(`${station}-rejected-cart.png`), fullPage: true });
    // Availability changes must not cancel work that was already confirmed.
    await manager.getByRole("button", { name: new RegExp(`^Iniciar preparo:.*${label}$`) }).click();
    await expect.poll(async () => (await read(manager, `tabs/${tab.id}/`)).orders[0].items[0].state).toBe("PREPARING");
    if (station === "BAR") {
      await chooseBarAvailability(manager, target, true);
      await manager.getByRole("button", { name: "Sim, reativar", exact: true }).click();
      await expect(manager.getByRole("dialog")).not.toBeVisible();
    } else await manager.getByRole("button", { name: `Reativar ${target}`, exact: true }).click();
    await expect.poll(async () => (await read(manager, "catalog/products/")).results.find((p: { id: string }) => p.id === product.id).availability).toBe("AVAILABLE");
    const record = { station, result: "PASS", product_sha: "67972d09200d43357b5b88dc0f64218967e4c24b",
      schedule: "UI submits mixed cart; request held before backend; other operator marks unavailable via UI; release original request to real backend",
      tab_id: tab.id, product_id: product.id, prior_order_id: before.orders[0].id, prior_item_id: originalItem.id,
      distinct_operators: true, distinct_sessions: true, rejected_http_status: result!.status, rejected_code: result!.code,
      new_order_attempts: attempts, orders_after_rejection: after.orders.length,
      charges_before_cents: before.charges_cents, charges_after_cents: after.charges_cents,
      exposure_before_cents: before.exposure_cents, exposure_after_cents: after.exposure_cents,
      payments_after_rejection: after.payments.length, draft_lines_preserved: 2,
      prior_item_after_rejection: "NEW", prior_item_after_explicit_start: "PREPARING", product_restored: "AVAILABLE" };
    await writeFile(info.outputPath(`${station}-availability-race.json`), JSON.stringify(record, null, 2));
    await info.attach(`${station}-availability-race`, { path: info.outputPath(`${station}-availability-race.json`), contentType: "application/json" });
  } finally {
    release();
    await managerContext.close();
  }
});
