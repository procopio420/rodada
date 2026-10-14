import { expect, test } from "./fixtures";

for (const scenario of [360, 390, 430, "revoked"] as const) test(`Guest committed order recovery ${scenario}`, async ({ page, browser }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }, { path, body });
  const table = await api("hospitality/tables/", { label: `Guest recovery ${scenario}`, guest_ordering_mode: "DIRECT" });
  await api(`hospitality/tables/${table.id}/occupy/`, {});
  const guestContext = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}`,
    viewport: { width: typeof scenario === "number" ? scenario : 390, height: 900 } });
  try {
    const guest = await guestContext.newPage();
    await guest.goto(`/guest/${table.public_token}`);
    await guest.getByText("Adicionar nome ou apelido (opcional)", { exact: true }).click();
    await guest.getByLabel("Seu nome ou apelido (opcional)").fill(`Guest recovery ${scenario}`);
    await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    await expect(guest.getByRole("heading", { name: `Mesa Guest recovery ${scenario}`, exact: true })).toBeVisible();
    await guest.getByRole("button", { name: /^Kitchen E2E item/ }).click();
    const attempts: string[] = []; let orderId = "", tabId = "";
    await guest.route("**/api/guest/orders/confirm/", async route => {
      attempts.push(route.request().postData()!);
      const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
      expect(response.status()).toBe(attempts.length === 1 ? 201 : 200);
      const body = await response.json();
      if (!orderId) { orderId = body.id; tabId = body.tab_id; } else expect(body.id).toBe(orderId);
      if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
    });
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    await expect(guest.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
    const storageKey = `rodada.intent.guest-order.v1.${table.public_token}`;
    const saved = await guest.evaluate(k => sessionStorage.getItem(k), storageKey); expect(saved).toBeTruthy();
    if (scenario === "revoked") await api(`hospitality/tables/${table.id}/release/`, {});
    await guest.reload();
    const verify = guest.getByRole("button", { name: "Verificar mesmo pedido" }); await expect(verify).toBeEnabled();
    expect(attempts).toHaveLength(1);
    await verify.dblclick();
    if (scenario === "revoked") {
      await expect(guest.getByText("Não foi possível validar esta visita. O pedido pendente foi preservado; peça ajuda à equipe.", { exact: true })).toBeVisible();
      expect(attempts).toHaveLength(1); expect(await guest.evaluate(k => sessionStorage.getItem(k), storageKey)).toBe(saved);
    } else {
      await expect(guest.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
      expect(attempts).toHaveLength(2); expect(attempts[1]).toBe(attempts[0]);
      expect(await guest.evaluate(k => sessionStorage.getItem(k), storageKey)).toBeNull();
    }
    const detail = await api(`tabs/${tabId}/`);
    expect(detail.orders).toHaveLength(1); expect(detail.orders[0].id).toBe(orderId);
    expect(detail.exposure_cents).toBe(1000); expect(detail.payments).toHaveLength(0);
  } finally { await guestContext.close(); }
});
