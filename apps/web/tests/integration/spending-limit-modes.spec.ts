import { test, expect, type Page } from "./fixtures";

async function login(page: Page) {
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Agora", exact: true })).toBeVisible();
  await page.goto("/manage/spending-policy");
  await expect(page.getByRole("region", { name: "Política de consumo atual" })).toContainText("Bloquear pedidos");
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
