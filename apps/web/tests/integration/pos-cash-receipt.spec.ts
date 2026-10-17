import { expect, test, type Page } from "./fixtures";

async function api(page: Page, path: string, body?: unknown) {
  return page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(`${response.status} ${JSON.stringify(result)}`);
    return result;
  }, { path, body });
}

test("POS lost cash response after PostgreSQL commit survives reload with one drawer effect", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const point = (await api(page, "cash/points/")).results[0];
  const shift = point.active_shift ?? await api(page, "cash/shifts/", {
    cash_point_id: point.id, opening_float_cents: 0, business_date: "2026-10-12", idempotency_key: "t03-cash-shift",
  });
  const beforeShift = await api(page, `cash/shifts/${shift.id}/`);
  const product = (await api(page, "catalog/products/")).results.find((p: { name: string }) => p.name === "Kitchen E2E item");
  const tab = await api(page, "tabs/", { display_label: "Cash recovery E2E" });
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: "t03-cash-order", lines: [{ product_id: product.id, quantity: 2 }] });
  const requests: string[] = []; let paymentId = "";
  await page.route(new RegExp(`/api/pos/tabs/${tab.id}/payments/?$`), async route => {
    requests.push(route.request().postData()!);
    // Fetch the canonical URL directly so the interception includes the commit,
    // rather than only Next's trailing-slash redirect.
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(201);
    const body = await response.json();
    if (!paymentId) paymentId = body.id; else expect(body.id).toBe(paymentId);
    if (requests.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.goto("/pos");
  await page.getByRole("button", { name: /Cash recovery E2E ·/ }).click();
  await page.getByLabel("Valor do pagamento").fill("10,00");
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo recebimento" });
  await expect(verify).toBeEnabled();
  const committed = await api(page, `tabs/${tab.id}/`);
  expect(committed.payments).toHaveLength(1); expect(committed.payments[0].id).toBe(paymentId);
  expect(committed.exposure_cents).toBe(1000);
  await page.reload(); await expect(verify).toBeEnabled(); expect(requests).toHaveLength(1);
  await verify.click();
  await expect(page.getByText("Recebimento confirmado. Saldo atualizado.")).toBeVisible();
  expect(requests[1]).toBe(requests[0]);
  const recovered = await api(page, `tabs/${tab.id}/`);
  expect(recovered.payments).toEqual(committed.payments); expect(recovered.exposure_cents).toBe(1000);
  const afterShift = await api(page, `cash/shifts/${shift.id}/`);
  expect(afterShift.expected_cents - beforeShift.expected_cents).toBe(1000);
  expect(afterShift.movements.filter((m: { payment_id: string }) => m.payment_id === paymentId)).toHaveLength(1);
});

// This exercises the reusable component's persisted attendance flow while the
// workspace's opt-in presentation is integrated separately. All domain effects
// use the real BFF, Django and PostgreSQL; only transport failures are injected.
test("Attendance full receipt resumes close after reload without reposting confirmed Payment", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const point = (await api(page, "cash/points/")).results[0];
  const shift = point.active_shift ?? await api(page, "cash/shifts/", {
    cash_point_id: point.id, opening_float_cents: 0, business_date: "2026-10-16", idempotency_key: "033-full-shift",
  });
  const before = await api(page, `cash/shifts/${shift.id}/`);
  const product = (await api(page, "catalog/products/")).results.find((p: { name: string }) => p.name === "Kitchen E2E item");
  const tab = await api(page, "tabs/", { display_label: "UX2 full recovery" });
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: "033-full-order", lines: [{ product_id: product.id, quantity: 1 }] });
  const bill = await api(page, `tabs/${tab.id}/`);
  const auth = await page.evaluate(async () => (await fetch("/api/auth/me")).json());
  const intent = { schema: 2, api_root: "/api/attendance", phase: "PAYMENT_PENDING", payment_id: null,
    close_requested: true, venue: auth.venue.id, staff: auth.staff.id, session: auth.session.id,
    tab: tab.id, captured_at: new Date().toISOString(), payload: { amount_cents: bill.exposure_cents,
      expected_version: bill.version, method: "CASH", cash_point_id: point.id,
      idempotency_key: crypto.randomUUID(), originating_session_id: auth.session.id } };
  await page.evaluate(intent => sessionStorage.setItem("rodada.intent.pos-cash.v1", JSON.stringify(intent)), intent);
  let paymentPosts = 0, closePosts = 0, rejectClose = true;
  const bodies: string[] = [];
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/payments/?$`), async route => {
    paymentPosts++; bodies.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(201);
    if (paymentPosts === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/close/?$`), async route => {
    closePosts++;
    if (rejectClose) return route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Encerramento indisponível." } });
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    expect(response.status()).toBe(200);
    // Commit happened but the acknowledgement is lost.
    await route.abort();
  });
  await page.goto("/pos");
  const verify = page.getByRole("button", { name: "Verificar mesmo recebimento" });
  await expect(verify).toBeEnabled();
  await verify.click();
  await expect(page.getByText(/Resultado ainda não confirmado/)).toBeVisible();
  expect(paymentPosts).toBe(1); expect(closePosts).toBe(0);
  expect((await api(page, `tabs/${tab.id}/`)).payments).toHaveLength(1);
  await page.reload(); await expect(verify).toBeEnabled();
  expect(paymentPosts).toBe(1);
  await verify.click();
  await expect(page.getByText(/Recebimento confirmado; encerramento pendente/)).toBeVisible();
  expect(paymentPosts).toBe(2); expect(closePosts).toBe(1);
  expect(bodies[1]).toBe(bodies[0]);
  const saved = await page.evaluate(() => JSON.parse(sessionStorage.getItem("rodada.intent.pos-cash.v1")!));
  expect(saved.phase).toBe("PAYMENT_CONFIRMED"); expect(saved.payment_id).toBeTruthy();
  expect(saved.payload).toEqual(intent.payload);
  const received = await api(page, `tabs/${tab.id}/`);
  expect(received.payments).toHaveLength(1); expect(received.state).toBe("OPEN"); expect(received.exposure_cents).toBe(0);
  rejectClose = false;
  await page.reload(); await expect(verify).toBeEnabled();
  expect(paymentPosts).toBe(2); expect(closePosts).toBe(1);
  await verify.click(); await expect(verify).toBeEnabled();
  expect(paymentPosts).toBe(2); expect(closePosts).toBe(2);
  expect((await api(page, `tabs/${tab.id}/`)).state).toBe("CLOSED");
  await page.reload(); await verify.click();
  // POS hides collection controls for a closed Tab; canonical readback and
  // envelope retirement prove completion, rather than a transient toast.
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("rodada.intent.pos-cash.v1"))).toBeNull();
  expect(paymentPosts).toBe(2); expect(closePosts).toBe(2); expect(bodies).toHaveLength(2);
  expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.pos-cash.v1"))).toBeNull();
  const after = await api(page, `cash/shifts/${shift.id}/`);
  expect(after.expected_cents - before.expected_cents).toBe(bill.exposure_cents);
  expect(after.movements.filter((m: { payment_id: string }) => m.payment_id === saved.payment_id)).toHaveLength(1);
});

test("Attendance CASH gateway preserves server capability guard", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-staff");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const tab = await api(page, "tabs/", { display_label: "Capability test no receipt" });
  const result = await page.evaluate(async tabId => {
    const auth = await (await fetch("/api/auth/me")).json();
    const point = await fetch("/api/attendance/cash/points/");
    const payment = await fetch(`/api/attendance/tabs/${tabId}/payments/`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method: "CASH", amount_cents: 100, expected_version: 1,
        cash_point_id: crypto.randomUUID(), idempotency_key: crypto.randomUUID(), originating_session_id: auth.session.id }),
    });
    return { pointStatus: point.status, paymentStatus: payment.status, body: await payment.json() };
  }, tab.id);
  expect(result.pointStatus).toBe(403); expect(result.paymentStatus).toBe(403);
  expect(result.body.code).toBe("CAPABILITY_REQUIRED");
  expect((await api(page, `tabs/${tab.id}/`)).payments).toEqual([]);
});

test("Confirmed receipt with concurrent new consumption can explicitly keep Tab open without charging again", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const point = (await api(page, "cash/points/")).results[0];
  const shift = point.active_shift ?? await api(page, "cash/shifts/", {
    cash_point_id: point.id, opening_float_cents: 0, business_date: "2026-10-16", idempotency_key: "033-race-shift",
  });
  const product = (await api(page, "catalog/products/")).results.find((p: { name: string }) => p.name === "Kitchen E2E item");
  const tab = await api(page, "tabs/", { display_label: "Concurrent consumption after receipt" });
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: "033-race-before", lines: [{ product_id: product.id, quantity: 1 }] });
  const bill = await api(page, `tabs/${tab.id}/`);
  const auth = await page.evaluate(async () => (await fetch("/api/auth/me")).json());
  const payload = { amount_cents: bill.exposure_cents, expected_version: bill.version, method: "CASH",
    cash_point_id: point.id, idempotency_key: crypto.randomUUID(), originating_session_id: auth.session.id };
  const receipt = await api(page, `tabs/${tab.id}/payments/`, payload);
  // Another canonical order arrives after receipt, before the close readback.
  await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: "033-race-after", lines: [{ product_id: product.id, quantity: 1 }] });
  const before = await api(page, `cash/shifts/${shift.id}/`);
  await page.evaluate(intent => sessionStorage.setItem("rodada.intent.pos-cash.v1", JSON.stringify(intent)), {
    schema: 2, api_root: "/api/attendance", phase: "PAYMENT_CONFIRMED", payment_id: receipt.id,
    close_requested: true, venue: auth.venue.id, staff: auth.staff.id, session: auth.session.id,
    tab: tab.id, captured_at: new Date().toISOString(), payload,
  });
  let mutationAttempts = 0;
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/(payments|close)/?$`), route => {
    mutationAttempts++; return route.abort();
  });
  await page.goto("/pos");
  await page.getByRole("button", { name: "Verificar mesmo recebimento" }).click();
  await expect(page.getByText(/O saldo mudou/)).toBeVisible();
  const keep = page.getByRole("button", { name: "Manter comanda aberta", exact: true });
  await expect(keep).toBeEnabled();
  await keep.click();
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("rodada.intent.pos-cash.v1"))).toBeNull();
  expect(mutationAttempts).toBe(0);
  const current = await api(page, `tabs/${tab.id}/`);
  expect(current.state).toBe("OPEN"); expect(current.exposure_cents).toBe(product.price_cents);
  expect(current.payments).toHaveLength(1); expect(current.payments[0].id).toBe(receipt.id);
  const after = await api(page, `cash/shifts/${shift.id}/`);
  expect(after.expected_cents).toBe(before.expected_cents);
  expect(after.movements.filter((m: { payment_id: string }) => m.payment_id === receipt.id)).toHaveLength(1);
  await expect(page.getByLabel("Valor do pagamento")).toBeEnabled();
});
