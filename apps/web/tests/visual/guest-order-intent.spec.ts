import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const key = "rodada.intent.guest-order.v1.test-qr";
async function setup(page: Page) {
  await fixture(page, "normal", true);
  const scope = { venue_id: "venue-test", session_id: "guest-session", table_id: "table-test", occupancy_id: "visit-test", generation: 1 };
  const tab = { id: "tab-test", display_label: "Minha comanda", state: "OPEN", exposure_cents: 0, charges_cents: 0, payments_cents: 0,
    consumption_blocked: false, remaining_capacity_cents: 30000, orders: [] as { id: string; status: string; items: unknown[] }[] };
  const context = { session_scope: scope, table: { label: "24" }, occupancy_active: true, can_start_occupancy: false, tab,
    guest_policy: { emergency_blocked: false }, guest_session_token: "guest-test-credential" };
  const attempts: string[] = []; let failReadback = false, failNext = false, revoked = false, resolves = 0;
  await page.route("**/api/guest/qr/resolve/", route => { resolves++; return route.fulfill({ json: context }); });
  await page.route("**/api/guest/context/", route => {
    if (revoked) return route.fulfill({ status: 403, json: { code: "GUEST_SESSION_REVOKED", message: "Visita encerrada" } });
    if (failNext) { failNext = false; return route.fulfill({ status: 503, json: { code: "UNAVAILABLE" } }); }
    return route.fulfill({ json: context });
  });
  await page.route("**/api/guest/orders/confirm/", route => {
    attempts.push(route.request().postData()!);
    tab.orders = [{ id: "order-guest", status: "CONFIRMED", items: [] }]; tab.exposure_cents = 7200;
    if (attempts.length === 1) return route.abort();
    if (failReadback) { failNext = true; failReadback = false; }
    return route.fulfill({ json: { id: "order-guest", tab_id: tab.id } });
  });
  await page.goto("/guest/test-qr"); await page.getByRole("button", { name: /^Fritas/ }).click();
  return { context, attempts, failReadback: () => { failReadback = true; }, revoke: () => { revoked = true; }, resolves: () => resolves };
}
for (const width of [360, 390, 430]) test(`Guest lost response reload readback preserves same order ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const state = await setup(page);
  await page.getByRole("button", { name: /^Enviar ·/ }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo pedido" }); await expect(verify).toBeEnabled();
  const saved = await page.evaluate(k => sessionStorage.getItem(k), key);
  expect(saved).not.toContain("guest-test-credential");
  await page.reload(); await expect(verify).toBeEnabled(); expect(state.attempts).toHaveLength(1); expect(state.resolves()).toBe(1);
  await expect(page.getByRole("button", { name: /^Fritas/ })).toBeDisabled();
  await layoutAndA11y(page); await page.screenshot({ path: `../../visual-artifacts/spec026/t05b-guest-${width}.png`, fullPage: true });
  state.failReadback(); await verify.click();
  await expect(page.getByText("Resultado ainda não confirmado. Verifique este mesmo pedido; não envie outro.", { exact: true })).toBeVisible();
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(saved);
  await verify.dblclick(); await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(3); expect(new Set(state.attempts).size).toBe(1);
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
});
for (const field of ["venue_id", "session_id", "table_id", "occupancy_id", "generation", "tab"]) test(`Guest recovery does not adopt changed ${field}`, async ({ page }) => {
  const state = await setup(page); await page.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  if (field === "tab") state.context.tab.id = "other-tab";
  else if (field === "generation") state.context.session_scope.generation++;
  else state.context.session_scope[field as "venue_id" | "session_id" | "table_id" | "occupancy_id"] = "other";
  await page.reload(); await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect(page.getByText("Este pedido pertence à visita original. Peça ajuda à equipe; ele não será enviado nesta sessão.", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(1); expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeTruthy();
});
test("Revoked guest keeps pending envelope and never resolves a replacement session", async ({ page }) => {
  const state = await setup(page); await page.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  state.revoke(); await page.reload();
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect(page.getByText("Não foi possível validar esta visita. O pedido pendente foi preservado; peça ajuda à equipe.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Tentar de novo" }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeVisible();
  expect(state.resolves()).toBe(1); expect(state.attempts).toHaveLength(1);
});
test("Emergency guest block preserves pending order without POST", async ({ page }) => {
  const state = await setup(page); await page.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  state.context.guest_policy.emergency_blocked = true;
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect(page.getByText("Os pedidos por QR estão pausados. Peça ajuda à equipe.", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(1);
});
for (const failure of ["invalid", "write-failure"]) test(`Guest storage ${failure} blocks confirmation`, async ({ page }) => {
  await page.addInitScript(({ key, failure }) => {
    if (failure === "invalid") sessionStorage.setItem(key, "{}");
    else { const original = Storage.prototype.setItem; Storage.prototype.setItem = function(k, v) { if (k === key) throw new Error("storage failure"); return original.call(this, k, v); }; }
  }, { key, failure });
  if (failure === "invalid") {
    await fixture(page, "normal", true); await page.goto("/guest/test-qr");
    await expect(page.getByText("Não foi possível preservar seu pedido neste navegador. Peça ajuda à equipe antes de enviar.", { exact: true })).toBeVisible();
  } else {
    const state = await setup(page); await page.getByRole("button", { name: /^Enviar ·/ }).click();
    await expect(page.getByText("Não foi possível preservar seu pedido. Peça ajuda à equipe antes de enviar.", { exact: true })).toBeVisible();
    expect(state.attempts).toHaveLength(0);
  }
});
test("Initial guest rejection allows edit; recovered rejection stays pending", async ({ page }) => {
  const state = await setup(page);
  await page.route("**/api/guest/orders/confirm/", route => route.fulfill({ status: 409, json: { code: "PRODUCTS_NOT_CONFIRMABLE", message: "Revise os itens" } }));
  await page.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(page.getByText("Revise os itens", { exact: true })).toBeVisible();
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  await expect(page.getByRole("button", { name: "Remover", exact: true })).toBeEnabled();
  await page.unroute("**/api/guest/orders/confirm/");
  await page.route("**/api/guest/orders/confirm/", route => { state.attempts.push(route.request().postData()!); return route.abort(); });
  await page.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  await page.route("**/api/guest/orders/confirm/", route => route.fulfill({ status: 409, json: { code: "PRODUCTS_NOT_CONFIRMABLE", message: "Revise os itens" } }));
  await page.reload(); await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect(page.getByText("Revise os itens", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(1); expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeTruthy();
});
