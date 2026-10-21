import { test, expect, type Page } from "./fixtures";

async function login(page: Page) {
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Agora", exact: true })).toBeVisible();
  await page.goto("/manage/spending-policy");
  await expect(page.getByRole("region", { name: "Política de consumo atual" })).toBeVisible();
}

test("manager changes canonical policy; lost ACK reload reuses the original intent", async ({ page }) => {
  await login(page);
  const commands: unknown[] = [];
  let lose = true;
  await page.route("**/api/pos/house-account/enforcement/", async route => {
    if (route.request().method() !== "PUT") return route.continue();
    commands.push(route.request().postDataJSON());
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    if (lose) await route.abort(); else await route.fulfill({ response });
  });
  await page.getByLabel("Modo do limite operacional").selectOption("WARN_ONLY");
  await page.getByLabel("Motivo da alteração").fill("   ");
  await page.getByLabel("Confirme seu PIN").fill("2468");
  await page.getByRole("button", { name: "Confirmar alteração da política", exact: true }).click();
  await expect(page.getByText("Informe um motivo para alterar a política.", { exact: true })).toBeVisible();
  expect(commands).toHaveLength(0);
  expect(await page.evaluate(() => Object.keys(sessionStorage).filter(key => key.startsWith("rodada.spending-policy.v1:")))).toEqual([]);
  await expect(page.getByLabel("Motivo da alteração")).toBeEnabled();
  await page.getByLabel("Motivo da alteração").fill("Synthetic live rehearsal");
  await page.getByLabel("Confirme seu PIN").fill("2468");
  await page.getByRole("button", { name: "Confirmar alteração da política", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesma alteração", exact: true })).toBeEnabled();
  await page.reload();
  await expect(page.getByRole("button", { name: "Verificar mesma alteração", exact: true })).toBeEnabled();
  lose = false;
  await page.getByLabel("Confirme seu PIN").fill("2468");
  await page.getByRole("button", { name: "Verificar mesma alteração", exact: true }).click();
  await expect(page.getByText("Alteração confirmada pelo servidor. Em vigor: Só alertar, versão 2.", { exact: true })).toBeVisible();
  expect(commands).toHaveLength(2);
  expect(commands[1]).toEqual(commands[0]);
  const result = await page.evaluate(async () => {
    const me = await (await fetch("/api/auth/me")).json();
    const policy = await (await fetch("/api/pos/house-account/enforcement/")).json();
    return { me, policy };
  });
  expect(result.policy).toMatchObject({ venue_id: result.me.venue.id, mode: "WARN_ONLY", version: 2 });
  expect(commands[0]).toMatchObject({ expected_venue_id: result.me.venue.id, expected_session_id: result.me.session.id, expected_version: 1 });
  const consumption = await page.evaluate(async () => {
    const request = async (path: string, body?: unknown) => {
      const response = await fetch(`/api/attendance/${path}`, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
      const value = await response.json();
      if (!response.ok) throw new Error(`${path}: ${response.status} ${JSON.stringify(value)}`);
      return value;
    };
    const tab = await request("tabs/", { display_label: "WARN live canonical" });
    const products = await request("catalog/products/");
    const product = products.results.find((row: { price_cents: number }) => row.price_cents === 500);
    if (!product) throw new Error("Synthetic BAR fixture missing");
    const command = { idempotency_key: crypto.randomUUID(), lines: [{ product_id: product.id, quantity: 8 }] };
    const order = await request(`tabs/${tab.id}/orders/confirm/`, command);
    const replay = await request(`tabs/${tab.id}/orders/confirm/`, command);
    const detail = await request(`tabs/${tab.id}/`);
    return { order, replay, detail };
  });
  expect(consumption.replay.id).toBe(consumption.order.id);
  expect(consumption.detail).toMatchObject({ spending_limit_mode: "WARN_ONLY", exposure_cents: 4000, consumption_blocked: false });
  expect(consumption.detail.orders).toHaveLength(1);

});

test("cookie swap after editor session read cannot change another Venue", async ({ page }) => {
  await login(page);
  let arm = false, captured = false, release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  let write: { status: number; code?: string } | undefined;
  page.on("response", response => {
    if (response.url().endsWith("/api/auth/reauthenticate") && response.ok()) arm = true;
  });
  await page.route("**/api/auth/me", async route => {
    if (!arm || captured) return route.continue();
    const response = await route.fetch();
    captured = true;
    await held;
    await route.fulfill({ response });
  });
  await page.route("**/api/pos/house-account/enforcement/", async route => {
    if (route.request().method() !== "PUT") return route.continue();
    const response = await route.fetch();
    write = { status: response.status(), code: (await response.json()).code };
    await route.fulfill({ response });
  });
  await page.getByLabel("Modo do limite operacional").selectOption("ENFORCE");
  await page.getByLabel("Motivo da alteração").fill("Synthetic captured A intent");
  await page.getByLabel("Confirme seu PIN").fill("2468");
  await page.getByRole("button", { name: "Confirmar alteração da política", exact: true }).click();
  await expect.poll(() => captured).toBe(true);
  try {
    const statuses = await page.evaluate(async () => {
      const login = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ venue_slug: "other-e2e", login_identifier: "test-other", pin: "2468" }) });
      const reauth = await fetch("/api/auth/reauthenticate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pin: "2468" }) });
      return { login: login.status, reauth: reauth.status };
    });
    expect(statuses).toEqual({ login: 200, reauth: 200 });
  } finally { release(); }
  await expect.poll(() => write).toEqual({ status: 409, code: "ACTOR_CONTEXT_CHANGED" });
  const foreign = await page.evaluate(async () => (await fetch("/api/pos/house-account/enforcement/")).json());
  expect(foreign).toMatchObject({ mode: "ENFORCE", version: 1 });
  expect(await page.evaluate(() => Object.keys(sessionStorage).filter(key => key.startsWith("rodada.spending-policy.v1:")))).toHaveLength(1);
});

test("Guest uses the same WARN_ONLY ledger and labels excess without claiming a block", async ({ page, browser }) => {
  await login(page);
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }, { path, body });
  const table = await api("hospitality/tables/", { label: "Guest WARN synthetic", guest_ordering_mode: "DIRECT" });
  await api(`hospitality/tables/${table.id}/occupy/`, {});
  const guestContext = await browser.newContext({ baseURL: new URL(page.url()).origin });
  try {
    const guest = await guestContext.newPage();
    await guest.goto(`/guest/${table.public_token}`);
    await guest.getByRole("button", { name: "Abrir minha comanda", exact: true }).click();
    const bar = guest.getByRole("button", { name: /^Bar E2E item/ });
    for (let i = 0; i < 8; i++) await bar.click();
    let tabId = "";
    guest.on("response", async response => {
      if (response.url().includes("/api/guest/orders/confirm") && response.ok()) tabId = (await response.json()).tab_id;
    });
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    await expect(guest.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
    await expect.poll(() => tabId).not.toBe("");
    const detail = await api(`tabs/${tabId}/`);
    expect(detail).toMatchObject({ spending_limit_mode: "WARN_ONLY", exposure_cents: 4000, limit_exceeded: true, consumption_blocked: false });
    expect(detail.orders).toHaveLength(1);
    await expect(guest.getByText("Consumo acima da referência. O estabelecimento utiliza o modo Só alertar.", { exact: true })).toBeVisible();
  } finally { await guestContext.close(); }
});
