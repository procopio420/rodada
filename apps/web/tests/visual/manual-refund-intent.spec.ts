import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const storageKey = "rodada.intent.refund.v1";
async function setup(page: Page, correction = false) {
  await fixture(page, "normal", true);
  let committed = false;
  const reason = correction ? "correction:WRONG_ENTRY" : "Devolução de teste";
  const tab = () => ({ id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: committed ? 500 : 0,
    payments: [{ id: "payment-test", method: "CASH", amount_cents: 1200, status: committed ? "PARTIALLY_REFUNDED" : "CONFIRMED", refunded_cents: committed ? 500 : 0,
      refunds: committed ? [{ id: "refund-test", amount_cents: 500, status: "CONFIRMED", reason }] : [] }],
    refund_required_corrections: correction && !committed ? [{ id: "correction-test", item_name: "Item corrigido", reason_code: "WRONG_ENTRY", refund_required_cents: 500 }] : [] });
  await page.route("**/api/pos/tabs/tab-test/", route => route.fulfill({ json: tab() }));
  const path = correction ? "**/api/pos/corrections/correction-test/settle-refund/" : "**/api/pos/payments/payment-test/refunds/";
  const canonical = correction ? { id: "correction-test", status: "APPLIED", refund_id: "refund-test", refund_status: "CONFIRMED" }
    : { id: "refund-test", payment_id: "payment-test", amount_cents: 500, status: "CONFIRMED" };
  return { path, canonical, commit: () => { committed = true; } };
}
async function choose(page: Page, correction = false) {
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test");
  if (!correction) {
    await page.getByLabel("Valor a estornar").fill("5,00");
    await page.getByLabel("Motivo do estorno").fill("Devolução de teste");
  }
}
async function saved(page: Page) { return page.evaluate(key => sessionStorage.getItem(key), storageKey); }

for (const correction of [false, true]) for (const width of [360, 390, 430]) test(`Manual ${correction ? "correction" : "refund"} lost response reload double tap at ${width}`, async ({ page }) => {
  const state = await setup(page, correction); await page.setViewportSize({ width, height: 900 });
  const bodies: string[] = [];
  await page.route(state.path, route => {
    bodies.push(route.request().postData()!); state.commit();
    return bodies.length === 1 ? route.abort() : route.fulfill({ status: 200, json: state.canonical });
  });
  await choose(page, correction); await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/refund-${correction ? "correction" : "form"}-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: correction ? "Estornar R$ 5,00" : "Confirmar estorno", exact: true })
    .evaluate((button: HTMLButtonElement) => { button.click(); button.click(); });
  const verify = page.getByRole("button", { name: "Verificar mesmo estorno" });
  await expect(verify).toBeEnabled(); expect(bodies).toHaveLength(1);
  await expect(page.getByLabel("Comanda", { exact: true })).toBeDisabled();
  await expect(page.getByLabel("Pagamento elegível")).toBeDisabled();
  await expect(page.getByLabel("Caixa que devolverá o dinheiro")).toBeDisabled();
  if (!correction) {
    await expect(page.getByLabel("Valor a estornar")).toBeDisabled();
    await expect(page.getByLabel("Motivo do estorno")).toBeDisabled();
  }
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/refund-pending-${correction}-${width}.png`, fullPage: true });
  const envelope = await saved(page); expect(envelope).toBeTruthy();
  expect(JSON.parse(envelope!)).toMatchObject({ payment: "payment-test", amount_cents: 500, session: "session-test", cash_point_id: "cash-test" });
  await page.reload(); await expect(verify).toBeEnabled(); expect(bodies).toHaveLength(1);
  await verify.click();
  await expect(page.getByText("Estorno confirmado. O pagamento original foi preservado no histórico.")).toBeVisible();
  expect(bodies[1]).toBe(bodies[0]); expect(await saved(page)).toBeNull();
  await expect(page.getByLabel("Comanda", { exact: true })).toBeEnabled();
});

test("Refund readback failure preserves same command until canonical history returns", async ({ page }) => {
  const state = await setup(page); await choose(page);
  let fails = true; const bodies: string[] = [];
  await page.route("**/api/pos/tabs/tab-test/", route => fails ? route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Leitura indisponível" } }) : route.fallback());
  await page.route(state.path, route => { bodies.push(route.request().postData()!); state.commit(); return route.fulfill({ status: 201, json: state.canonical }); });
  await page.getByRole("button", { name: "Confirmar estorno", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo estorno" });
  await expect(verify).toBeEnabled(); expect(await saved(page)).toBeTruthy();
  fails = false; await verify.click();
  await expect(page.getByText(/^Estorno confirmado\./)).toBeVisible();
  expect(bodies[1]).toBe(bodies[0]); expect(await saved(page)).toBeNull();
});

test("Refund reauthentication preserves intention and conflicting retry never releases it", async ({ page }) => {
  const state = await setup(page); const bodies: string[] = []; let reauthed = false;
  await page.route("**/api/auth/reauthenticate", route => { reauthed = true; return route.fulfill({ json: { ok: true } }); });
  await page.route(state.path, route => {
    bodies.push(route.request().postData()!);
    return route.fulfill({ status: reauthed ? 409 : 403, json: { code: reauthed ? "IDEMPOTENCY_CONFLICT" : "REAUTH_REQUIRED", message: "Confira o estorno original" } });
  });
  await choose(page); await page.getByRole("button", { name: "Confirmar estorno", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo estorno" });
  await expect(verify).toBeEnabled(); const original = await saved(page);
  await page.getByLabel("PIN do gerente").fill("2468"); await page.getByRole("button", { name: "Confirmar PIN", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("PIN confirmado");
  await verify.click(); await expect(page.getByText("Confira o estorno original")).toBeVisible();
  expect(bodies[1]).toBe(bodies[0]); expect(await saved(page)).toBe(original);
});

test("Initial refund rejection permits correction with a new deliberate key", async ({ page }) => {
  const state = await setup(page); const bodies: { idempotency_key: string }[] = [];
  await page.route(state.path, route => {
    bodies.push(route.request().postDataJSON());
    if (bodies.length === 1) return route.fulfill({ status: 409, json: { code: "REFUND_EXCEEDS_PAYMENT", message: "Confira o valor" } });
    state.commit(); return route.fulfill({ status: 201, json: state.canonical });
  });
  await choose(page); await page.getByRole("button", { name: "Confirmar estorno", exact: true }).click();
  await expect(page.getByText("Confira o valor")).toBeVisible(); expect(await saved(page)).toBeNull();
  await expect(page.getByLabel("Valor a estornar")).toBeEnabled();
  await page.getByRole("button", { name: "Confirmar estorno", exact: true }).click();
  await expect(page.getByText(/^Estorno confirmado\./)).toBeVisible();
  expect(bodies[0].idempotency_key).not.toBe(bodies[1].idempotency_key);
});

test("Refund changed and revoked sessions never adopt or discard pending operation", async ({ page }) => {
  const state = await setup(page); let sends = 0;
  await page.route(state.path, route => { sends++; return route.abort(); });
  await choose(page);
  const auth = await page.evaluate(async () => (await fetch("/api/auth/me")).json());
  await page.getByRole("button", { name: "Confirmar estorno", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo estorno" }); await expect(verify).toBeEnabled();
  const original = await saved(page);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { ...auth, session: { ...auth.session, id: "another-session" } } }));
  await page.reload(); await verify.click(); await expect(page.getByText(/ele não será enviado nesta sessão/)).toBeVisible();
  expect(sends).toBe(1); expect(await saved(page)).toBe(original);
  await page.route("**/api/auth/me", route => route.fulfill({ status: 403, json: { code: "SESSION_REVOKED", message: "Sessão revogada" } }));
  await verify.click(); await expect(page.getByText(/Confira sua sessão antes de retomar/)).toBeVisible();
  expect(sends).toBe(1); expect(await saved(page)).toBe(original);
});

for (const mode of ["unavailable", "corrupt", "empty"] as const) test(`Refund storage ${mode} blocks before mutation`, async ({ page }) => {
  const state = await setup(page); let sends = 0;
  await page.route(state.path, route => { sends++; return route.abort(); });
  await page.addInitScript(({ mode, storageKey }) => {
    if (mode === "unavailable") Storage.prototype.setItem = () => { throw new Error("Storage unavailable"); };
    else sessionStorage.setItem(storageKey, mode === "empty" ? "" : "{invalid");
  }, { mode, storageKey });
  await page.goto("/refunds"); await expect(page.getByText(/Não foi possível preservar o estorno/)).toBeVisible();
  await expect(page.getByLabel("Comanda", { exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Verificar armazenamento" }).click(); expect(sends).toBe(0);
});
