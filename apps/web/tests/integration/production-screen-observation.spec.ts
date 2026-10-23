import { expect, test } from "./fixtures";

for (const station of ["BAR", "KITCHEN"] as const) {
  test(`${station} first visible canonical ticket is observed without a staff tap or duplicate metric`, async ({ page }) => {
    await page.goto("/staff");
    await page.getByLabel("Estabelecimento").fill("web-e2e");
    await page.getByLabel("Operador", { exact: true }).fill("test-manager");
    await page.getByLabel("PIN", { exact: true }).fill("2468");
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();

    const api = (path: string, body: object) => page.evaluate(async ({ path, body }) => {
      const response = await fetch(`/api/pos/${path}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`);
      return response.json();
    }, { path, body });
    const label = `Screen visible ${station} ${crypto.randomUUID()}`;
    const { product } = await api("catalog/resolve-or-create/", {
      name: label, price_cents: 100, fulfillment_station: station,
    });
    const tab = await api("tabs/", { display_label: label });
    const confirmed = await api(`tabs/${tab.id}/orders/confirm/`, {
      idempotency_key: crypto.randomUUID(),
      lines: [{ product_id: product.id, quantity: 1 }],
    });
    const received: { station: string; order_ids: string[] }[] = [];
    await page.route("**/api/production-screen-observation", async route => {
      received.push(JSON.parse(route.request().postData()!) as { station: string; order_ids: string[] });
      await route.continue();
    });

    await page.goto(station === "BAR" ? "/bar" : "/kitchen");
    const ticket = page.locator(`[data-production-order-id="${confirmed.id}"]`).first();
    await expect(ticket).toBeVisible();
    await ticket.scrollIntoViewIfNeeded();
    await expect.poll(() => received.some(batch =>
      batch.station === station && batch.order_ids.includes(confirmed.id))).toBe(true);

    const date = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    const report = async () => page.evaluate(async date => {
      const result = await fetch(`/api/pos/management/attendance-metrics/?start=${date}&end=${date}`);
      if (!result.ok) throw new Error(`report status ${result.status}`);
      return (await result.json()).production_screen as Record<string, {
        eligible: number; observed: number; latency_missing: number;
      }>;
    }, date);
    await expect.poll(async () => (await report())[station].observed).toBeGreaterThanOrEqual(1);
    const first = (await report())[station].observed;

    // A second canonical snapshot/browser mount can resend; DB records only first view.
    await page.reload();
    const again = page.locator(`[data-production-order-id="${confirmed.id}"]`).first();
    await expect(again).toBeVisible();
    await again.scrollIntoViewIfNeeded();
    await expect.poll(async () => (await report())[station].observed).toBe(first);
    expect((await report())[station].latency_missing).toBeGreaterThanOrEqual(1);
  });
}
