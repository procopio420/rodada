import { test, expect, type Page } from "./fixtures";
import { selectExistingAttendanceTab } from "./attendance-helpers";
import { layoutAndA11y } from "../visual/fixtures";
const key = "rodada.intent.pos-cash.v1";

async function login(page: Page, operator = "test-manager", venue = "web-e2e") {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill(venue);
  await page.getByLabel("Operador", { exact: true }).fill(operator);
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
}
async function api(page: Page, path: string, data?: unknown) {
  return page.evaluate(async ({ path, data }) => {
    const r = await fetch(`/api/pos/${path}`, data === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
    });
    if (!r.ok) throw new Error(`Fixture/readback ${path}: ${r.status}`);
    return r.json();
  }, { path, data });
}
async function setup(page: Page, label: string) {
  await login(page);
  const product = (await api(page, "catalog/products/")).results.find((p: { name: string }) => p.name === "Kitchen E2E item");
  const tab = await api(page, "tabs/", { display_label: label });
  const table = await api(page, "hospitality/tables/", { label: `Receipt ${label}`, guest_ordering_mode: "DISABLED" });
  const occupancy = await api(page, `hospitality/tables/${table.id}/occupy/`, {});
  await api(page, `hospitality/occupancies/${occupancy.id}/tabs/`, { tab_id: tab.id });
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: `${label}-order`, lines: [{ product_id: product.id, quantity: 2 }] });
  await page.goto("/attendance");
  await selectExistingAttendanceTab(page, label);
  await page.getByRole("button", { name: "Conferir / fechar conta", exact: true }).click();
  return tab.id as string;
}
async function external(page: Page, amount?: string) {
  await page.getByRole("button", { name: /^Receber R/ }).click();
  await page.getByRole("button", { name: "Cartão externo", exact: true }).click();
  if (amount) await page.getByLabel("Valor recebido (R$)", { exact: true }).fill(amount);
  await expect(page.getByRole("button", { name: /^(Registrar recebimento|Receber e encerrar comanda)$/ })).toBeDisabled();
  await page.getByRole("checkbox", { name: "Conferi a aprovação na maquininha externa" }).check();
}

for (const width of [360, 390, 430]) test(`external terminal explicit approval, partial and full without drawer ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 900 });
  const id = await setup(page, `External happy ${width}`);
  const tableId = (await api(page, "hospitality/tables/")).results.find((t: { active_occupancy?: { tabs: { id: string }[] } }) => t.active_occupancy?.tabs.some(row => row.id === id)).id;
  const pointsBefore = (await api(page, "cash/points/")).results;
  expect(pointsBefore.every((p: { active_shift: unknown }) => !p.active_shift)).toBe(true);
  await external(page, "5,00");
  await layoutAndA11y(page);
  await page.screenshot({ path: info.outputPath(`external-${width}.png`), fullPage: true });
  await page.getByRole("button", { name: "Registrar recebimento", exact: true }).click();
  await expect.poll(async () => (await api(page, `tabs/${id}/`)).exposure_cents).toBe(1500);
  await expect.poll(() => page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  const partial = await api(page, `tabs/${id}/`);
  expect(partial.state).toBe("OPEN");
  expect(partial.payments).toHaveLength(1);
  expect(partial.payments[0]).toMatchObject({ method: "EXTERNAL_TERMINAL", amount_cents: 500, status: "CONFIRMED" });
  await external(page);
  await page.getByRole("button", { name: "Receber e encerrar comanda", exact: true }).click();
  await expect.poll(async () => (await api(page, `tabs/${id}/`)).state).toBe("CLOSED");
  await expect.poll(() => page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  const final = await api(page, `tabs/${id}/`);
  expect(final.exposure_cents).toBe(0);
  expect(final.payments).toHaveLength(2);
  expect(final.payments.every((p: { method: string }) => p.method === "EXTERNAL_TERMINAL")).toBe(true);
  const tables = (await api(page, "hospitality/tables/")).results;
  const table = tables.find((t: { id: string }) => t.id === tableId);
  expect(table.status).toBe("OCCUPIED");
  expect((await api(page, "cash/points/")).results).toEqual(pointsBefore);
});

for (const fault of ["ack", "readback", "session", "invalid-envelope"] as const) test(`external terminal preserves frozen receipt after ${fault}`, async ({ page, browser }) => {
  const id = await setup(page, `External recovery ${fault}`);
  const attempts: string[] = [];
  let paymentId = "";
  await page.route(new RegExp(`/api/attendance/tabs/${id}/payments/?$`), async route => {
    attempts.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(201);
    const body = await response.json();
    if (!paymentId) paymentId = body.id; else expect(body.id).toBe(paymentId);
    if (attempts.length === 1 && fault !== "readback") await route.abort();
    else await route.fulfill({ response });
  });
  let wrongReadback = fault === "readback";
  await page.route(new RegExp(`/api/attendance/tabs/${id}/?$`), async route => {
    const response = await route.fetch();
    if (wrongReadback) {
      const body = await response.json();
      body.payments = body.payments.map((p: { method: string }) => ({ ...p, method: "CASH" }));
      await route.fulfill({ response, json: body });
    } else await route.fulfill({ response });
  });
  await external(page, "5,00");
  await page.getByRole("button", { name: "Registrar recebimento", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo recebimento", exact: true });
  await expect(verify).toBeEnabled();
  const raw = await page.evaluate(k => sessionStorage.getItem(k), key);
  const saved = JSON.parse(raw!);
  expect(saved.schema).toBe(3);
  expect(saved.payload.method).toBe("EXTERNAL_TERMINAL");
  expect(saved.payload).not.toHaveProperty("cash_point_id");
  expect(saved.phase).toBe(fault === "readback" ? "PAYMENT_CONFIRMED" : "PAYMENT_PENDING");
  if (fault === "invalid-envelope") {
    saved.payload.method = "CASH";
    await page.evaluate(({ key, saved }) => sessionStorage.setItem(key, JSON.stringify(saved)), { key, saved });
    await page.reload();
    await expect(page.getByText("Não foi possível preservar o recebimento neste navegador. Confira o histórico com a gerência antes de continuar.", { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(1);
    expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(JSON.stringify(saved));
  } else if (fault === "session") {
    const replacement = await browser.newContext({ baseURL: page.url().split("/attendance")[0] });
    try {
      await login(await replacement.newPage());
      await page.context().clearCookies();
      await page.context().addCookies(await replacement.cookies());
      await page.reload();
      await verify.click();
      await expect(page.getByText("Este recebimento pertence à sessão original. Solicite revisão à gerência; ele não será enviado nesta sessão.", { exact: true })).toBeVisible();
      expect(attempts).toHaveLength(1);
      expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(raw);
    } finally { await replacement.close(); }
  } else {
    wrongReadback = false;
    await page.reload();
    await expect(verify).toBeEnabled();
    expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(raw);
    await verify.dblclick();
    await expect.poll(() => page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
    expect(attempts).toHaveLength(fault === "readback" ? 1 : 2);
    if (fault === "ack") expect(attempts[1]).toBe(attempts[0]);
  }
  const final = await api(page, `tabs/${id}/`);
  expect(final.payments).toHaveLength(1);
  expect(final.payments[0].id).toBe(paymentId);
  expect(final.payments[0].method).toBe("EXTERNAL_TERMINAL");
  expect(final.exposure_cents).toBe(1500);
});

test("Attendance terminal gateway denies unsupported methods, fields, permissions and foreign Venue", async ({ page, browser }) => {
  const id = await setup(page, "External gateway");
  const auth = await page.evaluate(async () => (await fetch("/api/auth/me")).json());
  const detail = await api(page, `tabs/${id}/`);
  const valid = { method: "EXTERNAL_TERMINAL", amount_cents: 500, expected_version: detail.version,
    idempotency_key: "external-gateway-key", originating_session_id: auth.session.id };
  async function post(target: Page, body: unknown) {
    return target.evaluate(async ({ id, body }) => {
      const r = await fetch(`/api/attendance/tabs/${id}/payments/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      return r.status;
    }, { id, body });
  }
  for (const method of ["CARD", "PIX", "TAP_TO_PAY", "CARD_ONLINE", "OTHER", ["EXTERNAL_TERMINAL"]]) expect(await post(page, { ...valid, method })).toBe(403);
  for (const body of [{ ...valid, cash_point_id: "foreign" }, { ...valid, provider: "fake" }, { ...valid, amount_cents: 0 }, { ...valid, amount_cents: 1.5 }]) expect(await post(page, body)).toBe(403);
  expect(await post(page, { ...valid, originating_session_id: crypto.randomUUID() })).toBe(403);
  for (const operator of ["test-staff", "test-other"]) {
    const context = await browser.newContext({ baseURL: page.url().split("/attendance")[0] });
    try {
      const other = await context.newPage();
      await login(other, operator, operator === "test-other" ? "other-e2e" : "web-e2e");
      const session = await other.evaluate(async () => (await fetch("/api/auth/me")).json());
      expect([403, 404]).toContain(await post(other, { ...valid, originating_session_id: session.session.id }));
    } finally { await context.close(); }
  }
  expect((await api(page, `tabs/${id}/`)).payments).toHaveLength(0);
});

test("mixed cash and external terminal receipts affect the drawer only for cash", async ({ page }) => {
  const id = await setup(page, "External mixed receipt");
  const point = (await api(page, "cash/points/")).results[0];
  const shift = await api(page, "cash/shifts/", { cash_point_id: point.id,
    opening_float_cents: 5000, business_date: "2026-11-03", idempotency_key: "external-mixed-shift" });
  // Refresh the account normally so its available cash points include the new shift.
  await page.reload();
  await selectExistingAttendanceTab(page, "External mixed receipt");
  await page.getByRole("button", { name: "Conferir / fechar conta", exact: true }).click();
  await external(page, "5,00");
  await page.getByRole("button", { name: "Registrar recebimento", exact: true }).click();
  await expect.poll(() => page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  await page.getByRole("button", { name: /^Receber R/ }).click();
  await page.getByLabel("Valor recebido (R$)", { exact: true }).fill("5,00");
  await page.getByRole("button", { name: "Registrar recebimento", exact: true }).click();
  await expect.poll(() => page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  await external(page);
  await page.getByRole("button", { name: "Receber e encerrar comanda", exact: true }).click();
  await expect.poll(async () => (await api(page, `tabs/${id}/`)).state).toBe("CLOSED");
  const final = await api(page, `tabs/${id}/`);
  expect(final.payments.map((p: { method: string }) => p.method).sort()).toEqual(["CASH", "EXTERNAL_TERMINAL", "EXTERNAL_TERMINAL"]);
  const drawer = await api(page, `cash/shifts/${shift.id}/`);
  expect(drawer.expected_cents).toBe(5500);
  const receipts = drawer.movements.filter((m: { payment_id: string | null }) => m.payment_id);
  expect(receipts).toHaveLength(1);
  expect(final.payments.find((p: { id: string }) => p.id === receipts[0].payment_id).method).toBe("CASH");
});

test("revoked original session cannot replay an external receipt even with its old cookie", async ({ page, browser }) => {
  const id = await setup(page, "External revoked session");
  const pattern = new RegExp(`/api/attendance/tabs/${id}/payments/?$`);
  await page.route(pattern, async route => {
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(201);
    await route.abort();
  });
  await external(page, "5,00");
  await page.getByRole("button", { name: "Registrar recebimento", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo recebimento", exact: true })).toBeEnabled();
  const original = await page.evaluate(k => sessionStorage.getItem(k), key);
  const payload = JSON.parse(original!).payload;
  const cookies = await page.context().cookies();
  await page.unroute(pattern);
  expect(await page.evaluate(async () => (await fetch("/api/auth/logout", { method: "POST" })).status)).toBe(204);
  await page.context().addCookies(cookies);
  const denied = await page.evaluate(async ({ id, payload }) => (await fetch(`/api/attendance/tabs/${id}/payments/`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  })).status, { id, payload });
  expect(denied).toBe(401);
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(original);
  const context = await browser.newContext({ baseURL: page.url().split("/attendance")[0] });
  try {
    const observer = await context.newPage();
    await login(observer);
    const final = await api(observer, `tabs/${id}/`);
    expect(final.payments).toHaveLength(1);
    expect(final.payments[0]).toMatchObject({ method: "EXTERNAL_TERMINAL", amount_cents: 500 });
    expect(final.exposure_cents).toBe(1500);
  } finally { await context.close(); }
});
