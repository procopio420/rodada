import { addCatalogItem } from "./category-actions";
import { openOtherTabs } from "./attendance-actions";
import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const key = "rodada.intent.staff-order.v1";
async function setup(page: Page, surface = "attendance") {
  await fixture(page, "normal", true);
  const attempts: string[] = [];
  let readback = true;
  await page.route(/\/api\/(attendance|pos)\/tabs\/tab-test\/orders\/confirm\/$/, route => {
    attempts.push(route.request().postData()!);
    return attempts.length === 1 ? route.abort() : route.fulfill({ json: { id: "order-recovered", tab_id: "tab-test" } });
  });
  await page.route(/\/api\/(attendance|pos)\/tabs\/tab-test\/$/, route => route.fulfill(readback
    ? { json: { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 7200, version: 2,
      orders: attempts.length > 1 ? [{ id: "order-recovered", items: [] }] : [], payments: [], refund_required_corrections: [] } }
    : { status: 503, json: { code: "TEMPORARY", message: "Leitura indisponível" } }));
  await page.goto(`/${surface}`);
  if (surface === "attendance") await openOtherTabs(page);
  await page.getByRole("button", { name: /^Comanda de teste ·/ }).click();
  if (surface === "attendance") {
    await addCatalogItem(page, "Fritas");
    await page.locator(".attendanceOrderDialog").getByRole("button", { name: /^Pedido atual/ }).click();
  } else await page.getByRole("button", { name: /^Fritas/ }).click();
  return { attempts, failReadback: () => { readback = false; }, restoreReadback: () => { readback = true; } };
}
for (const surface of ["attendance", "pos"]) for (const width of [360, 390, 430]) test(`Staff order lost response reload immutable recovery ${surface} ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  const state = await setup(page, surface);
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  const saved = await page.evaluate(k => sessionStorage.getItem(k), key); expect(saved).toBeTruthy();
  await page.reload();
  const verify = page.getByRole("button", { name: "Verificar mesmo pedido" }); await expect(verify).toBeEnabled();
  expect(state.attempts).toHaveLength(1);
  if (surface === "pos") await expect(page.getByRole("button", { name: "Abrir", exact: true })).toBeDisabled();
  else await expect(page.locator(".attendanceOrderDialog").locator(":scope > button").last()).toBeDisabled();
  await layoutAndA11y(page); await page.screenshot({ path: `../../visual-artifacts/spec026/t05-order-${surface}-${width}.png`, fullPage: true });
  state.failReadback(); await verify.click();
  await expect(page.getByText("Resultado ainda não confirmado. Verifique este mesmo pedido; não envie outro.", { exact: true })).toBeVisible();
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(saved);
  state.restoreReadback(); await verify.dblclick();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(3); expect(new Set(state.attempts).size).toBe(1);
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  if (surface === "pos") {
    await page.getByLabel("Nome ou apelido", { exact: true }).fill("Nova comanda de teste");
    await expect(page.getByRole("button", { name: "Abrir", exact: true })).toBeEnabled();
  }
  else await expect(page.locator(".attendanceOrderDialog").locator(":scope > button").last()).toBeEnabled();
});

for (const failure of ["different-session", "revoked", "changed-envelope"]) test(`Order recovery blocks ${failure}`, async ({ page }) => {
  const state = await setup(page);
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  if (failure === "changed-envelope") await page.evaluate(k => { const i = JSON.parse(sessionStorage.getItem(k)!); i.payload.lines[0].quantity = 9; sessionStorage.setItem(k, JSON.stringify(i)); }, key);
  else await page.route("**/api/auth/me", route => route.fulfill(failure === "revoked"
    ? { status: 401, json: { code: "AUTH_REQUIRED", message: "Sessão revogada" } }
    : { json: { venue: { id: "venue-test" }, staff: { id: "operator-test" }, session: { id: "other-session" } } }));
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect(page.getByRole("alert").filter({ hasText: failure === "different-session" ? "sessão original" : failure === "revoked" ? "Confira sua sessão" : "Resultado ainda" })).toBeVisible();
  expect(state.attempts).toHaveLength(1);
  await expect(page.getByRole("button", { name: "Descartar rascunho", exact: true })).toBeDisabled();
});
for (const failure of ["invalid", "write-failure"]) test(`Order storage blocks ${failure} before POST`, async ({ page }) => {
  await page.addInitScript(({ key, failure }) => {
    if (failure === "invalid") sessionStorage.setItem(key, "{}");
    else { const original = Storage.prototype.setItem; Storage.prototype.setItem = function(k, v) { if (k === key) throw new Error("storage unavailable"); return original.call(this, k, v); }; }
  }, { key, failure });
  if (failure === "invalid") {
    await fixture(page, "normal", true); await page.goto("/attendance");
    await expect(page.getByText("Não foi possível preservar o pedido neste navegador. Confira o histórico antes de continuar.", { exact: true })).toBeVisible();
    await expect(page.locator(".attendanceOrderDialog").locator(":scope > button").last()).toBeDisabled();
  } else {
    const state = await setup(page); await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
    await expect(page.getByText("Não foi possível preparar o pedido. Verifique a sessão e o armazenamento antes de continuar.", { exact: true })).toBeVisible();
    expect(state.attempts).toHaveLength(0);
  }
});
test("Initial known rejection allows review but recovered rejection preserves intent", async ({ page }) => {
  const state = await setup(page);
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", route => route.fulfill({ status: 409, json: { code: "PRODUCTS_NOT_CONFIRMABLE", message: "Revise os itens" } }));
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByText("Revise os itens", { exact: true })).toBeVisible();
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  await expect(page.getByRole("button", { name: "Descartar rascunho", exact: true })).toBeEnabled();
  await page.unroute("**/api/attendance/tabs/tab-test/orders/confirm/");
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  await page.route("**/api/attendance/tabs/tab-test/orders/confirm/", route => route.fulfill({ status: 409, json: { code: "PRODUCTS_NOT_CONFIRMABLE", message: "Revise os itens" } }));
  await page.reload(); await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect(page.getByText("Revise os itens", { exact: true })).toBeVisible();
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeTruthy(); expect(state.attempts).toHaveLength(1);
  await expect(page.locator(".attendanceOrderDialog").locator(":scope > button").last()).toBeDisabled();
});

test("Attendance pending order recovers from POS through original gateway", async ({ page }) => {
  const state = await setup(page);
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  const paths: string[] = [];
  page.on("request", request => { if (request.url().includes("/orders/confirm/")) paths.push(new URL(request.url()).pathname); });
  await page.goto("/pos");
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(2); expect(state.attempts[1]).toBe(state.attempts[0]);
  expect(paths).toEqual(["/api/attendance/tabs/tab-test/orders/confirm/"]);
});

for (const surface of ["attendance", "pos"]) test(`Pending order remains recoverable after closed tab reload ${surface}`, async ({ page }) => {
  const state = await setup(page, surface);
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  const saved = await page.evaluate(k => sessionStorage.getItem(k), key);
  await page.route(/\/api\/(attendance|pos)\/tabs\/tab-test\/$/, route => route.fulfill({ json: {
    id: "tab-test", display_label: "Comanda encerrada", state: "CLOSED", exposure_cents: 0, version: 3,
    orders: [{ id: "order-recovered", items: [] }], payments: [], refund_required_corrections: [],
  } }));
  await page.route(/\/api\/(attendance|pos)\/tabs\/(\?.*)?$/, route => route.fulfill({ json: { results: surface === "pos" ? [{ id: "tab-test", display_label: "Comanda encerrada", state: "CLOSED", exposure_cents: 0, version: 3 }] : [], next_offset: null } }));
  if (surface === "pos") {
    await page.clock.runFor(16000);
    await expect(page.getByRole("heading", { name: "Comanda encerrada", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Verificar mesmo pedido", exact: true })).toBeEnabled();
    expect(state.attempts).toHaveLength(1);
  }
  await page.reload();
  if (surface === "attendance") {
    await expect(page.getByRole("heading", { name: "Comanda encerrada", exact: true })).toBeVisible();
    await expect(page.getByRole("region", { name: "Pedido atual" })).toHaveCount(0);
  }
  const verify = page.getByRole("button", { name: "Verificar mesmo pedido", exact: true });
  await expect(verify).toBeEnabled();
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(saved);
  expect(state.attempts).toHaveLength(1);
  await verify.click();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(state.attempts).toHaveLength(2);
  expect(state.attempts[1]).toBe(state.attempts[0]);
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
});
