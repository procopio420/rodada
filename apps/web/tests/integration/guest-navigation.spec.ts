import { expect, test } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`Spec004 Guest multiple orders and persistent regions ${width}`, async ({ page, browser }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }, { path, body });
  const table = await api("hospitality/tables/", { label: `Navigation ${width}`, guest_ordering_mode: "DIRECT" });
  const context = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}`, viewport: { width, height: 900 } });
  try {
    const guest = await context.newPage(); await guest.goto(`/guest/${table.public_token}`);
    await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    const nav = guest.getByRole("navigation", { name: "Navegação do cliente" });
    for (const round of [1, 2]) {
      await nav.getByRole("button", { name: "Cardápio", exact: true }).click();
      await expect(guest.getByRole("region", { name: "Cardápio", exact: true })).toBeFocused();
      await guest.getByRole("button", { name: /^Bar E2E item/ }).click();
      await guest.getByRole("button", { name: /^Enviar ·/ }).click();
      await expect(guest.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
      await nav.getByRole("button", { name: "Pedidos", exact: true }).click();
      const orders = guest.getByRole("region", { name: "Pedidos", exact: true });
      await expect(orders).toBeFocused();
      await expect(orders.getByRole("heading", { name: /^Rodada / })).toHaveCount(round);
      await expect(orders.locator(".statusBadge").filter({ hasText: /^Recebido$/ })).toHaveCount(round);
      await expect(nav).toBeInViewport();
      await nav.getByRole("button", { name: "Conta", exact: true }).click();
      await expect(guest.getByRole("region", { name: "Conta", exact: true })).toBeFocused();
    }
    const inventory = await api("hospitality/tables/");
    const current = inventory.results.find((row: { id: string }) => row.id === table.id);
    expect(current.active_occupancy.tabs).toHaveLength(1);
    const tab = await api(`tabs/${current.active_occupancy.tabs[0].id}/`);
    expect(tab.orders).toHaveLength(2); expect(new Set(tab.orders.map((o: { id: string }) => o.id)).size).toBe(2);
    expect(tab.charges_cents).toBe(1000); expect(tab.payments).toHaveLength(0);
    await guest.screenshot({ path: `test-results/spec004-guest-real-${width}.png`, fullPage: true });
  } finally { await context.close(); }
});
