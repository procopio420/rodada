import { expect, test } from "./fixtures";

for (const scenario of [360, 390, 430, "blocked"] as const) test(`Guest repeat real visit ${scenario}`, async ({ page, browser }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }, { path, body });
  const table = await api("hospitality/tables/", { label: `Guest repeat ${scenario}`, guest_ordering_mode: "DIRECT" });
  await api(`hospitality/tables/${table.id}/occupy/`, {});
  const context = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}`,
    viewport: { width: typeof scenario === "number" ? scenario : 390, height: 900 } });
  try {
    const guest = await context.newPage();
    let resolves = 0;
    guest.on("request", request => { if (request.url().includes("/api/guest/qr/resolve")) resolves++; });
    await guest.goto(`/guest/${table.public_token}`);
    await guest.getByText("Adicionar nome ou apelido (opcional)", { exact: true }).click();
    await guest.getByLabel("Seu nome ou apelido (opcional)").fill(`Guest repeat ${scenario}`);
    await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    await guest.getByRole("button", { name: /^Kitchen E2E item/ }).click();
    const firstRequest = guest.waitForRequest(r => r.url().includes("/api/guest/orders/confirm") && r.method() === "POST");
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    const originalKey = (await firstRequest).postDataJSON().idempotency_key;
    await expect(guest.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
    const initialResolves = resolves;
    const tabs = await api("tabs/");
    const tab = tabs.results.find((t: { display_label: string }) => t.display_label === `Guest repeat ${scenario}`);
    const before = await api(`tabs/${tab.id}/`);
    const tokenKey = `rodada.guest.session.${table.public_token}`;
    const originalToken = await guest.evaluate(k => sessionStorage.getItem(k), tokenKey);
    expect(originalToken).toBeNull();
    const guestCookies = await context.cookies();
    expect(guestCookies.some(cookie => cookie.name.startsWith("rodada_guest_") && cookie.httpOnly)).toBe(true);
    await guest.getByRole("button", { name: /^Bar E2E item/ }).click();
    const repeat = guest.getByRole("button", { name: "Repetir rodada 1", exact: true });
    await repeat.click();
    const dialog = guest.getByRole("dialog", { name: "Conferir rodada" });
    await expect(dialog).toBeVisible();
    if (scenario === "blocked") {
      await api(`hospitality/tables/${table.id}/guest-ordering/`, { blocked: true });
      // The already-open review may still show the previous guest policy.
      // Either realtime disables Add, or an attempted Add re-reads the policy
      // and refuses the repeat. Never assume a stale dialog is disabled.
      const addButton = dialog.getByRole("button", { name: "Adicionar ao carrinho" });
      if (await addButton.isEnabled()) {
        await addButton.click({ timeout: 5000 }).catch(async error => {
          // Realtime can disable the button between isEnabled and click.
          if (await addButton.isEnabled()) throw error;
        });
      }
      await expect(addButton).toBeDisabled();
      // This branch must not add a second Order or alter the confirmed round.
      expect((await api(`tabs/${tab.id}/`)).orders).toEqual(before.orders);
      await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
      await expect(guest.getByText("1× Bar E2E item", { exact: true })).toBeVisible();
      expect((await api(`tabs/${tab.id}/`)).orders).toEqual(before.orders);
    } else {
      await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
      await expect(guest.getByText("1× Bar E2E item", { exact: true })).toBeVisible();
      await repeat.click();
      await dialog.getByRole("button", { name: "Adicionar ao carrinho" }).dblclick();
      await expect(dialog).toHaveCount(0);
      expect((await api(`tabs/${tab.id}/`)).orders).toEqual(before.orders);
      await guest.screenshot({ path: `test-results/guest-repeat-real-${scenario}.png`, fullPage: true });
      const attempts: string[] = [];
      await guest.route("**/api/guest/orders/confirm/", async route => {
        attempts.push(route.request().postData()!);
        const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
        expect(response.status()).toBe(attempts.length === 1 ? 201 : 200);
        if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
      });
      await guest.getByRole("button", { name: /^Enviar ·/ }).click();
      await expect(guest.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
      await expect(repeat).toBeDisabled();
      await guest.getByRole("button", { name: "Verificar mesmo pedido" }).dblclick();
      await expect(guest.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
      expect(attempts).toHaveLength(2); expect(attempts[1]).toBe(attempts[0]);
      expect(JSON.parse(attempts[0]).idempotency_key).not.toBe(originalKey);
      const after = await api(`tabs/${tab.id}/`);
      expect(after.orders).toHaveLength(2); expect(after.exposure_cents).toBe(2500);
      expect(after.orders.find((o: { id: string }) => o.id === before.orders[0].id)).toEqual(before.orders[0]);
      expect(after.payments).toEqual(before.payments);
    }
    expect(resolves).toBe(initialResolves);
    expect(await guest.evaluate(k => sessionStorage.getItem(k), tokenKey)).toBe(originalToken);
  } finally { await context.close(); }
});
