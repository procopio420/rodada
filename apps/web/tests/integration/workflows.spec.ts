import { expect, test, type Page } from "@playwright/test";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";

async function evidence(page: Page, name: string) {
  const directory = path.resolve(process.cwd(), "../../visual-artifacts/real-api");
  await mkdir(directory, { recursive: true });
  await page.screenshot({ path: path.join(directory, `${name}-390.png`), fullPage: true });
}

async function login(page: Page, operator = "test-manager") {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill(operator);
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
}

async function api(page: Page, path: string, data?: unknown) {
  const result = await page.evaluate(async ({ path, data }) => {
    const r = await fetch(path, { method: data === undefined ? "GET" : "POST", headers: data === undefined ? {} : { "Content-Type": "application/json" }, body: data === undefined ? undefined : JSON.stringify(data) });
    return { status: r.status, body: await r.json() };
  }, { path, data });
  expect(result.status, `${path}: ${JSON.stringify(result.body)}`).toBeLessThan(300);
  return result.body;
}

test("real staff, production, guest ordering, management and cash/refund workflows", async ({ page, browser }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await login(page);
  await evidence(page, "staff");
  const cookies = await page.context().cookies();
  expect(cookies.filter(cookie => cookie.name.startsWith("rodada_staff_") && cookie.name !== "rodada_staff_device").every(cookie => cookie.httpOnly)).toBe(true);
  expect(await page.evaluate(() => document.cookie)).not.toContain("rodada_staff_access");
  const { results: products } = await api(page, "/api/pos/catalog/products/");
  const kitchen = products.find((p: { fulfillment_station: string }) => p.fulfillment_station === "KITCHEN");
  const bar = products.find((p: { fulfillment_station: string }) => p.fulfillment_station === "BAR");
  const tab = await api(page, "/api/pos/tabs/", { display_label: "Real Web E2E tab" });
  const order = await api(page, `/api/pos/tabs/${tab.id}/orders/confirm/`, { idempotency_key: "real-web-order", lines: [{ product_id: kitchen.id, quantity: 1 }, { product_id: bar.id, quantity: 1 }] });
  const replay = await api(page, `/api/pos/tabs/${tab.id}/orders/confirm/`, { idempotency_key: "real-web-order", lines: [{ product_id: kitchen.id, quantity: 1 }, { product_id: bar.id, quantity: 1 }] });
  expect(replay.id).toBe(order.id);
  for (const [route, product] of [["/kitchen", kitchen], ["/bar", bar]] as const) {
    await page.goto(route);
    await expect(page.getByText(product.name, { exact: true }).first()).toBeVisible();
    await page.getByRole("button", { name: `Indisponibilizar ${product.name}`, exact: true }).click();
    await expect(page.getByRole("button", { name: `Reativar ${product.name}`, exact: true })).toBeEnabled();
    const catalog = await api(page, "/api/pos/catalog/products/");
    expect(catalog.results.find((p: { id: string }) => p.id === product.id).availability).toBe("UNAVAILABLE");
    await page.goto("/pos");
    await page.getByRole("button", { name: /Real Web E2E tab/ }).click();
    await expect(page.getByRole("button", { name: new RegExp(`${product.name}.*Indisponível`) })).toBeDisabled();
    await evidence(page, "pos-unavailable");
    await page.goto(route);
    await page.getByRole("button", { name: `Reativar ${product.name}`, exact: true }).click();
    await expect(page.getByRole("button", { name: `Indisponibilizar ${product.name}`, exact: true })).toBeEnabled();
    for (const label of ["Aceitar", "Preparar", "Pronto"]) {
      await page.getByRole("button", { name: new RegExp(`^${label}:.*Real Web E2E tab$`) }).click();
      await expect(page.getByRole("button", { name: new RegExp(`^${label}:.*Real Web E2E tab$`) })).toHaveCount(0);
    }
    const item = (await api(page, `/api/pos/tabs/${tab.id}/`)).orders[0].items.find((i: { product_id: string }) => i.product_id === product.id);
    expect(item.state).toBe("READY");
    await evidence(page, route.slice(1));
  }

  const table = await api(page, "/api/pos/hospitality/tables/", { label: "Web E2E 24", guest_ordering_mode: "DIRECT" });
  await api(page, `/api/pos/hospitality/tables/${table.id}/occupy/`, {});
  const guestContext = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}` });
  const guest = await guestContext.newPage();
  guest.on("pageerror", error => errors.push(error.message));
  await guest.goto(`/guest/${table.public_token}`);
  await guest.getByLabel("Seu nome ou apelido (opcional)").fill("Real guest E2E");
  await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
  await expect(guest.getByRole("heading", { name: "Real guest E2E" })).toBeVisible();
  await guest.getByRole("button", { name: new RegExp(kitchen.name) }).click();
  await guest.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(guest.getByRole("heading", { name: "Meus pedidos", exact: true })).toBeVisible();
  const guestTab = (await api(page, "/api/pos/tabs/")).results.find((t: { display_label: string }) => t.display_label === "Real guest E2E");
  expect(guestTab.id).not.toBe(tab.id);
  const guestDetail = await api(page, `/api/pos/tabs/${guestTab.id}/`);
  expect(guestDetail.orders[0].source).toBe("GUEST");
  expect(guestDetail.exposure_cents).toBe(kitchen.price_cents);
  await evidence(guest, "guest");

  await page.goto("/manage");
  await expect(page.getByText("Comandas abertas", { exact: true })).toBeVisible();
  await evidence(page, "manage");
  await page.getByRole("link", { name: "Abrir caixa", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Turno de caixa" })).toBeVisible();
  await page.getByLabel("Fundo inicial").fill("100,00");
  await page.getByRole("button", { name: "Confirmar abertura" }).click();
  await expect(page.getByRole("heading", { name: "Caixa aberto" })).toBeVisible();
  await evidence(page, "cash");
  await page.goto("/manage");
  await page.getByRole("link", { name: "Estornos", exact: true }).click();
  await page.getByLabel("Comanda", { exact: true }).selectOption(tab.id);
  await expect(page.getByText("Restante reembolsável")).toHaveCount(0); // No payment invented.
  await expect(page.getByRole("button", { name: "Confirmar estorno" })).toBeDisabled();
  await evidence(page, "refunds");

  const point = (await api(page, "/api/pos/cash/points/")).results[0];
  const counting = await api(page, `/api/pos/cash/shifts/${point.active_shift.id}/count/start/`, {});
  await api(page, `/api/pos/cash/shifts/${point.active_shift.id}/close/`, { counted_amount_cents: 9000, review_threshold_cents: 0, expected_version: counting.version });
  await page.goto("/manage");
  await expect(page.getByRole("heading", { name: "Divergências de caixa pendentes" })).toBeVisible();
  await page.getByRole("link", { name: "Revisar caixa" }).click();
  await expect(page.getByText("Divergência aguardando revisão de gerente.")).toBeVisible();
  await page.getByLabel("Motivo da revisão").fill("Conferência E2E da diferença");
  await page.getByRole("button", { name: "Revisar divergência" }).click();
  await page.getByLabel("Seu PIN").fill("2468");
  await page.getByRole("button", { name: "Confirmar e continuar" }).click();
  await expect(page.getByText("Divergência revisada.")).toBeVisible();
  await evidence(page, "cash-success");

  // Keep the old access for the explicit stale-session request; SSE may already clear storage.
  const oldSession = await guest.evaluate(token => sessionStorage.getItem(`rodada.guest.session.${token}`), table.public_token);
  expect(oldSession).toBeTruthy();
  await api(page, `/api/pos/hospitality/tables/${table.id}/release/`, {});
  const revoked = await guest.evaluate(async oldSession => {
    const result = await fetch("/api/guest/context/", { headers: { "X-Guest-Session": oldSession ?? "" } });
    return { status: result.status, body: await result.json() };
  }, oldSession);
  expect(revoked.status).toBe(403);
  expect(revoked.body.code).toBe("GUEST_SESSION_REVOKED");
  await guest.reload();
  await expect(guest.getByRole("heading", { name: "Não foi possível abrir o pedido" })).toBeVisible();
  await expect(guest.getByRole("button", { name: /^Enviar ·/ })).toHaveCount(0);
  await guestContext.close();
  expect(errors).toEqual([]);
});

test("real authorization failure is visible and never becomes an empty success", async ({ page }) => {
  await login(page, "test-staff");
  await page.goto("/cash");
  await expect(page.locator(".notice[role=alert]")).toContainText("CAPABILITY_REQUIRED");
  await page.goto("/manage");
  await expect(page.locator(".notice[role=alert]")).toBeVisible();
  await expect(page.getByText("Comandas abertas")).toHaveCount(0);
  await evidence(page, "manage-permission-denied");
});

test("real expired session clears privileged cookies", async ({ page, context }) => {
  await context.addCookies([
    { name: "rodada_staff_access", value: "rat_e2e-expired-only", url: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}`, httpOnly: true, sameSite: "Lax" },
    { name: "rodada_staff_refresh", value: "rrt_e2e-expired-only", url: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}`, httpOnly: true, sameSite: "Lax" },
  ]);
  const response = page.waitForResponse("**/api/auth/me");
  await page.goto("/staff");
  const result = await response;
  expect(result.status()).toBe(401);
  expect((await result.json()).code).toBe("SESSION_EXPIRED");
  await expect(page.getByRole("heading", { name: "Entrar no atendimento" })).toBeVisible();
  expect((await context.cookies()).filter(c => c.name === "rodada_staff_access" || c.name === "rodada_staff_refresh")).toEqual([]);
});

test("canonical and compatibility hosts select the correct surface and manifest", async ({ request }) => {
  for (const [host, title, route] of [
    ["bar.rodada.ai", "Rodada Bar", "/bar"], ["cozinha.rodada.ai", "Rodada Cozinha", "/kitchen"],
    ["gerencia.rodada.ai", "Rodada Gerência", "/manage"], ["app.rodada.ai", "Rodada Gerência", "/manage"],
    ["cliente.rodada.ai", "Rodada Cliente", "/guest"], ["pedido.rodada.ai", "Rodada Cliente", "/guest"],
  ]) {
    const manifest = await request.get("/manifest.webmanifest", { headers: { host } });
    expect((await manifest.json()).name).toBe(title);
    expect((await manifest.json()).start_url).toBe(route);
    const response = await request.get(route === "/guest" ? "/qr-test-token" : "/", { headers: { host } });
    expect(response.status()).toBe(200);
    expect(await response.text()).toContain(`<title>${title}</title>`);
  }
});

test("completed catalog, persistent guest tracking, historical cash review and report export use real APIs", async ({ page, browser }) => {
  await login(page);
  await page.goto("/kitchen");
  const name = "=Teste CSV real";
  await page.getByRole("button", { name: "+ Item", exact: true }).click();
  await page.getByLabel("Nome do produto").fill(name);
  await page.getByRole("option", { name: `Criar “${name}”`, exact: true }).click();
  await page.getByLabel("Preço (R$)").fill("18,00");
  await page.getByRole("button", { name: "Criar item", exact: true }).click();
  await expect(page.getByText("Item criado e disponível para vender.")).toBeVisible();
  const catalog = await api(page, `/api/pos/catalog/products/?q=${encodeURIComponent(name)}`);
  expect(catalog.results).toHaveLength(1);
  const product = catalog.results[0];
  const reused = await api(page, "/api/pos/catalog/products/resolve/", { name: name.toUpperCase(), price_cents: 9999, fulfillment_station: "BAR" });
  expect(reused.created).toBe(false); expect(reused.product.id).toBe(product.id); expect(reused.product.price_cents).toBe(1800);
  await page.getByRole("button", { name: "Fechar", exact: true }).click();
  await page.getByRole("button", { name: "+ Item", exact: true }).click();
  await page.getByLabel("Nome do produto").fill("Teste CSV");
  await page.getByRole("option", { name: new RegExp(name.replace("=", "")) }).click();
  await expect(page.getByText("Item disponível no catálogo existente.")).toBeVisible();
  const table = await api(page, "/api/pos/hospitality/tables/", { label: "Tracking E2E", guest_ordering_mode: "DIRECT" });
  await api(page, `/api/pos/hospitality/tables/${table.id}/occupy/`, {});
  const guestContext = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}` });
  const guest = await guestContext.newPage();
  await guest.goto(`/guest/${table.public_token}`);
  await guest.getByLabel("Seu nome ou apelido (opcional)").fill("Tracking guest");
  await guest.getByRole("button", { name: "Abrir minha comanda", exact: true }).click();
  await guest.getByRole("button", { name: new RegExp("Teste CSV real") }).click();
  await guest.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(guest.getByRole("heading", { name: "Meus pedidos" })).toBeVisible();
  await guest.reload();
  await expect(guest.getByText("1× =Teste CSV real", { exact: true })).toBeVisible();
  const tab = (await api(page, "/api/pos/tabs/")).results.find((row: { display_label: string }) => row.display_label === "Tracking guest");
  const detail = await api(page, `/api/pos/tabs/${tab.id}/`);
  const item = detail.orders[0].items[0];
  for (const state of ["ACCEPTED", "PREPARING", "READY"]) await api(page, `/api/pos/order-items/${item.id}/transition/`, { state });
  await expect(guest.getByText("Pronto", { exact: true })).toBeVisible({ timeout: 10000 });
  await guest.reload(); await expect(guest.getByText("Pronto", { exact: true })).toBeVisible();
  const point = await api(page, "/api/pos/cash/points/create/", { label: "Historical E2E" });
  const old = await api(page, "/api/pos/cash/shifts/", { cash_point_id: point.id, opening_float_cents: 1000, idempotency_key: "history-old" });
  await api(page, `/api/pos/cash/shifts/${old.id}/count/start/`, {});
  await api(page, `/api/pos/cash/shifts/${old.id}/close/`, { counted_amount_cents: 900 });
  const active = await api(page, "/api/pos/cash/shifts/", { cash_point_id: point.id, opening_float_cents: 2000, idempotency_key: "history-new" });
  await page.goto("/cash"); await page.getByLabel("Ponto de caixa").selectOption(point.id);
  await expect(page.getByRole("heading", { name: "Caixa aberto" })).toBeVisible();
  await page.getByLabel("Selecionar turno atual ou fechamento antigo").selectOption(old.id);
  await expect(page.getByRole("heading", { name: "Turno fechado" })).toBeVisible();
  await page.getByLabel("Motivo da revisão").fill("Revisão histórica E2E");
  await page.getByRole("button", { name: "Revisar divergência" }).click();
  const reauth = page.getByLabel("Seu PIN");
  await expect(reauth).toBeVisible();
  await reauth.fill("2468"); await page.getByRole("button", { name: "Confirmar e continuar" }).click();
  await expect(page.getByText("Divergência revisada.")).toBeVisible();
  expect((await api(page, `/api/pos/cash/shifts/${active.id}/`)).status).toBe("OPEN");
  await page.goto("/reports"); await expect(page.getByRole("heading", { name: "Resumo financeiro" })).toBeVisible();
  await evidence(page, "reports");
  const calendar = await api(page, "/api/pos/management/calendar/");
  const report = await api(page, `/api/pos/management/reports/?start=${calendar.business_date}&end=${calendar.business_date}`);
  expect(report.products.some((row: { order_item__product_name_snapshot: string }) => row.order_item__product_name_snapshot === name)).toBe(true);
  const downloaded = page.waitForEvent("download"); await page.getByRole("button", { name: "Exportar CSV" }).click();
  const download = await downloaded; const csv = await readFile((await download.path())!, "utf8");
  expect(csv).toContain('"\'=Teste CSV real"'); expect(csv).toContain("valores monetários em centavos");
  await api(page, `/api/pos/hospitality/tables/${table.id}/release/`, {});
  await expect(guest.getByText("Esta visita terminou.", { exact: false })).toBeVisible({ timeout: 10000 });
  await expect(guest.getByText("1× =Teste CSV real", { exact: true })).toHaveCount(0);
  await guestContext.close();
});


test("parallel Web refresh preserves all operational screens and still enforces revocation", async ({ page, context }) => {
  await login(page);
  const original = await context.cookies();
  const oldCookie = original.map(c => `${c.name}=${c.value}`).join("; ");
  await context.clearCookies({ name: "rodada_staff_access" });
  const paths = ["/api/auth/me", "/api/pos/tabs/", "/api/pos/catalog/products/", "/api/pos/cash/points/"];
  const outcomes = await page.evaluate(async paths => Promise.all(paths.flatMap(path => [path, path]).map(async path => {
    const response = await fetch(path);
    const body = await response.json();
    return { path, status: response.status, code: body.code, leaked: "access_token" in body || "refresh_token" in body };
  })), paths);
  expect(outcomes.map(r => r.status)).toEqual(Array(8).fill(200));
  expect(outcomes.some(r => r.leaked)).toBe(false);
  const late = await page.request.get("/api/auth/me", { headers: { Cookie: oldCookie } });
  expect(late.status()).toBe(200);
  for (const route of ["/pos", "/bar", "/kitchen", "/cash"]) {
    await page.goto(route);
    await expect(page.locator(".notice[role=alert]")).toHaveCount(0);
    expect((await api(page, "/api/auth/me")).staff.display_name).toBe("test-manager");
  }
  const lock = await page.evaluate(async () => (await fetch("/api/auth/lock", { method: "POST" })).status);
  expect(lock).toBeLessThan(300);
  const revoked = await page.request.get("/api/auth/me", { headers: { Cookie: oldCookie } });
  expect(revoked.status()).toBe(401);
  expect((await revoked.json()).code).toBe("SESSION_REVOKED");
  expect((await context.cookies()).filter(c => ["rodada_staff_access", "rodada_staff_refresh"].includes(c.name))).toEqual([]);
});
