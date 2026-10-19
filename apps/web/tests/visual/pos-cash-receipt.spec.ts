import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

const storageKey = "rodada.intent.pos-cash.v1";
async function setup(page: Page) {
  await fixture(page, "normal", true);
  let committed = false;
  const tab = () => ({ id: "tab-test", display_label: "Comanda de teste", version: committed ? 3 : 2,
    state: "OPEN", exposure_cents: committed ? 6200 : 7200, charges_cents: 8400, payable_cents: 8400,
    payments_cents: committed ? 2200 : 1200, orders: [],
    payments: committed ? [{ id: "cash-receipt", method: "CASH", amount_cents: 1000, status: "CONFIRMED" }] : [] });
  await page.route("**/api/pos/tabs/", route => route.fulfill({ json: { results: [tab()] } }));
  await page.route("**/api/pos/tabs/tab-test/", route => route.fulfill({ json: tab() }));
  return { commit: () => { committed = true; } };
}
async function choose(page: Page) {
  await page.goto("/pos");
  await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
  await page.getByLabel("Valor do pagamento").fill("10,00");
}
async function saved(page: Page) {
  return page.evaluate(key => sessionStorage.getItem(key), storageKey);
}

for (const width of [360, 390, 430]) test(`POS cash double tap, lost response and reload at ${width}`, async ({ page }) => {
  const state = await setup(page); await page.setViewportSize({ width, height: 900 });
  const requests: string[] = [];
  await page.route("**/api/pos/tabs/tab-test/payments/", route => {
    requests.push(route.request().postData()!); state.commit();
    return requests.length === 1 ? route.abort() : route.fulfill({ status: 201, json: { id: "cash-receipt", status: "CONFIRMED" } });
  });
  await choose(page);
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/cash-form-${width}.png`, fullPage: true });
  const receive = page.getByRole("button", { name: "Receber em dinheiro", exact: true });
  await receive.evaluate((button: HTMLButtonElement) => { button.click(); button.click(); });
  const verify = page.getByRole("button", { name: "Verificar mesmo recebimento" });
  await expect(verify).toBeEnabled();
  expect(requests).toHaveLength(1);
  await expect(page.getByRole("button", { name: /Comanda de teste ·/ })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Fechar comanda", exact: true })).toBeDisabled();
  expect(await saved(page)).toBeTruthy();
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/cash-pending-${width}.png`, fullPage: true });
  await page.reload();
  await expect(verify).toBeEnabled();
  expect(requests).toHaveLength(1); // Reload never submits automatically.
  await verify.click();
  await expect(page.getByText("Recebimento confirmado. Saldo atualizado.")).toBeVisible();
  expect(requests).toHaveLength(2); expect(requests[1]).toBe(requests[0]);
  expect(await saved(page)).toBeNull();
  await expect(page.getByRole("button", { name: /Comanda de teste ·/ })).toBeEnabled();
  await expect(page.getByLabel("Valor do pagamento")).toHaveValue("");
});

for (const code of ["VERSION_CONFLICT", "SERVICE_REASSESSMENT_REQUIRED"]) test(`Initial ${code} rejection allows correction with a new explicit intention`, async ({ page }) => {
  const state = await setup(page); const bodies: { idempotency_key: string; amount_cents: number }[] = [];
  await page.route("**/api/pos/tabs/tab-test/payments/", route => {
    bodies.push(route.request().postDataJSON());
    if (bodies.length === 1) return route.fulfill({ status: 409, json: { code, message: "Confira a comanda." } });
    state.commit(); return route.fulfill({ status: 201, json: { id: "cash-receipt", status: "CONFIRMED" } });
  });
  await choose(page); await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  await expect(page.getByText("Confira a comanda.")).toBeVisible();
  await expect(page.getByLabel("Valor do pagamento")).toBeEnabled();
  expect(await saved(page)).toBeNull();
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  await expect(page.getByText("Recebimento confirmado. Saldo atualizado.")).toBeVisible();
  expect(bodies[0].idempotency_key).not.toBe(bodies[1].idempotency_key);
});

test("Canonical receipt without readback remains pending and retries the same payload", async ({ page }) => {
  const state = await setup(page); const bodies: string[] = []; let readbackFails = true;
  await choose(page);
  await page.route("**/api/pos/tabs/tab-test/", route => readbackFails
    ? route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Leitura indisponível." } }) : route.fallback());
  await page.route("**/api/pos/tabs/tab-test/payments/", route => {
    bodies.push(route.request().postData()!); state.commit();
    return route.fulfill({ status: 201, json: { id: "cash-receipt", status: "CONFIRMED" } });
  });
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo recebimento" })).toBeEnabled();
  expect(await saved(page)).toBeTruthy(); readbackFails = false;
  await page.getByRole("button", { name: "Verificar mesmo recebimento" }).click();
  await expect(page.getByText("Recebimento confirmado. Saldo atualizado.")).toBeVisible();
  expect(bodies[1]).toBe(bodies[0]);
});

for (const schema of [1, 2]) test(`Cash schema ${schema}: changed or revoked session preserves envelope and never adopts or resends`, async ({ page }) => {
  await setup(page); let sends = 0;
  await page.route("**/api/pos/tabs/tab-test/payments/", route => { sends++; return route.abort(); });
  await page.route("**/api/attendance/tabs/tab-test/**", route => { sends++; return route.abort(); });
  await choose(page);
  const auth = await page.evaluate(async () => (await fetch("/api/auth/me")).json());
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo recebimento" });
  await expect(verify).toBeEnabled();
  if (schema === 2) await page.evaluate(key => {
    const pending = JSON.parse(sessionStorage.getItem(key)!);
    sessionStorage.setItem(key, JSON.stringify({ ...pending, schema: 2, api_root: "/api/attendance",
      phase: "PAYMENT_CONFIRMED", payment_id: "canonical-payment-for-session-negative", close_requested: true }));
  }, storageKey);
  const original = await saved(page);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { ...auth, session: { ...auth.session, id: "another-session" } } }));
  await page.reload(); await verify.click();
  await expect(page.getByText(/ele não será enviado nesta sessão/)).toBeVisible();
  expect(sends).toBe(1); expect(await saved(page)).toBe(original);
  await page.route("**/api/auth/me", route => route.fulfill({ status: 403, json: { code: "SESSION_REVOKED", message: "Sessão revogada." } }));
  await verify.click(); await expect(page.getByText(/Confira sua sessão antes de retomar/)).toBeVisible();
  expect(sends).toBe(1); expect(await saved(page)).toBe(original);
});

for (const mode of ["unavailable", "corrupt"] as const) test(`Receipt storage ${mode} fails closed`, async ({ page }) => {
  await setup(page);
  await page.addInitScript(({ mode, storageKey }) => {
    if (mode === "corrupt") sessionStorage.setItem(storageKey, "{invalid");
    else Storage.prototype.setItem = () => { throw new Error("Storage unavailable"); };
  }, { mode, storageKey });
  let sends = 0;
  await page.route("**/api/pos/tabs/tab-test/payments/", route => { sends++; return route.abort(); });
  await page.goto("/pos");
  await expect(page.getByText(/Não foi possível preservar o recebimento/)).toBeVisible();
  await expect(page.getByRole("button", { name: /Comanda de teste ·/ })).toBeDisabled();
  await page.getByRole("button", { name: "Verificar armazenamento" }).click();
  expect(sends).toBe(0);
  if (mode === "corrupt") {
    expect(await saved(page)).toBe("{invalid");
    await page.evaluate(key => sessionStorage.setItem(key, ""), storageKey);
    // Same mounted component revalidates storage without replacing it.
    await page.getByRole("button", { name: "Verificar armazenamento" }).click();
    await expect(page.getByText(/Não foi possível preservar o recebimento/)).toBeVisible();
    expect(await saved(page)).toBe(""); expect(sends).toBe(0);
  }
});

test("A 5xx then fingerprint conflict never releases the pending identity", async ({ page }) => {
  await setup(page); let sends = 0;
  await page.route("**/api/pos/tabs/tab-test/payments/", route => {
    sends++;
    return route.fulfill({ status: sends === 1 ? 503 : 409, json: { code: sends === 1 ? "UNAVAILABLE" : "IDEMPOTENCY_CONFLICT", message: "Confira o recebimento original." } });
  });
  await choose(page); await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo recebimento" }); await expect(verify).toBeEnabled();
  const original = await saved(page); await verify.click();
  await expect(verify).toBeEnabled(); expect(await saved(page)).toBe(original);
  await expect(page.getByRole("button", { name: /Comanda de teste ·/ })).toBeDisabled();
});
