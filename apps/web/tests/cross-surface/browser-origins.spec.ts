import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";

test("Guest and Attendance Web orders share occupancy, survive response loss and recover disconnected Kitchen", async ({ page, browser }) => {
  test.setTimeout(120_000);
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("android-post-drop-ci");
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const r = await fetch(`/api/pos/${path}`, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${path}: ${r.status}`);
    return r.json();
  }, { path, body });
  const products = ["Android Post Drop Test Soda", "Android Compose Test Meal"];
  const label = `Browser-origins-${Date.now()}`;
  const table = await api("hospitality/tables/", { label, guest_ordering_mode: "DIRECT" });
  const guestContext = await browser.newContext({ baseURL: "http://127.0.0.1:3110" });
  const kitchenContext = await browser.newContext({ storageState: await page.context().storageState(), baseURL: "http://127.0.0.1:3110" });
  try {
    const kitchen = await kitchenContext.newPage();
    await kitchen.goto("/kitchen");
    await kitchenContext.setOffline(true);
    const guest = await guestContext.newPage();
    await guest.goto(`/guest/${table.public_token}`);
    await guest.getByText("Adicionar nome ou apelido (opcional)", { exact: true }).click();
    await guest.getByLabel("Seu nome ou apelido (opcional)").fill(`${label}-guest`);
    await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    for (const product of products) await guest.getByRole("button", { name: new RegExp(`^${product}`) }).click();
    const attempts: string[] = [];
    let guestTabId = "", guestOrderId = "";
    await guest.route("**/api/guest/orders/confirm/", async route => {
      attempts.push(route.request().postData()!);
      // Fault injection discards a REAL backend commit response; no synthetic success.
      const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
      expect(response.status()).toBe(attempts.length === 1 ? 201 : 200);
      const body = await response.json();
      if (!guestOrderId) { guestOrderId = body.id; guestTabId = body.tab_id; }
      else expect(body.id).toBe(guestOrderId);
      if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
    });
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    await expect(guest.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
    await guest.reload();
    await guest.getByRole("button", { name: "Verificar mesmo pedido" }).dblclick();
    await expect(guest.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(2);
    expect(attempts[1]).toBe(attempts[0]);
    await guest.unroute("**/api/guest/orders/confirm/");
    const changedPayload = JSON.parse(attempts[0]);
    changedPayload.lines[0].quantity += 1;
    const conflict = await guest.evaluate(async ({ payload, selector }) => {
      const r = await fetch("/api/guest/orders/confirm/", { method: "POST", headers: {
        "Content-Type": "application/json", "X-Guest-Session": selector,
      }, body: JSON.stringify(payload) });
      return { status: r.status, body: await r.json() };
    }, { payload: changedPayload, selector: table.public_token });
    expect(conflict.status).toBe(409);
    expect(conflict.body.code).toBe("IDEMPOTENCY_CONFLICT");
    await page.goto("/attendance");
    await page.getByRole("button", { name: new RegExp(`^Mesa ${label}`) }).click();
    await page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
    await page.getByRole("dialog").getByRole("textbox").fill(`${label}-web`);
    await page.getByRole("dialog").getByRole("button", { name: /Abrir/ }).click();
    const dialog = page.locator(".attendanceOrderDialog");
    for (const product of products) await dialog.getByRole("button", { name: new RegExp(`^${product}`) }).click();
    await dialog.getByRole("button", { name: /Pedido atual/ }).click();
    await dialog.getByRole("button", { name: /^Confirmar pedido/ }).click();
    await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
    const snapshot = (await api("hospitality/tables/")).results.find((t: { id: string }) => t.id === table.id);
    expect(snapshot.active_occupancy.tabs).toHaveLength(2);
    const webTab = snapshot.active_occupancy.tabs.find((t: { id: string }) => t.id !== guestTabId);
    const details = await Promise.all([guestTabId, webTab.id].map(id => api(`tabs/${id}/`)));
    expect(details[0].orders[0].id).toBe(guestOrderId);
    for (const detail of details) {
      expect(detail.orders).toHaveLength(1);
      expect(detail.orders[0].items).toHaveLength(2);
      expect(detail.orders[0].items.every((i: { state: string }) => i.state === "NEW")).toBe(true);
      expect(detail.exposure_cents).toBe(1700);
      expect(detail.payments_cents).toBe(0);
    }
    // Kitchen was disconnected during both commits. Reconnect and canonical reload recover NEW.
    await kitchenContext.setOffline(false);
    await kitchen.reload();
    for (const station of ["BAR", "KITCHEN"]) {
      const stationPage = station === "KITCHEN" ? kitchen : page;
      await stationPage.goto(station === "BAR" ? "/bar" : "/kitchen");
      for (const detail of details) {
        const item = detail.orders[0].items.find((i: { product_name: string }) => i.product_name === (station === "BAR" ? products[0] : products[1]));
        const start = stationPage.getByRole("button", { name: new RegExp(`^Iniciar preparo:.*${detail.display_label}$`) });
        await expect(start).toBeVisible();
        await start.click();
        await expect.poll(async () => (await api(`tabs/${detail.id}/`)).orders[0].items.find((i: { id: string }) => i.id === item.id).state).toBe("PREPARING");
        await stationPage.getByRole("button", { name: new RegExp(`^Pronto:.*${detail.display_label}$`) }).click();
        await expect.poll(async () => (await api(`tabs/${detail.id}/`)).orders[0].items.find((i: { id: string }) => i.id === item.id).state).toBe("READY");
      }
    }
    await mkdir("../../artifacts", { recursive: true });
    await writeFile("../../artifacts/browser-origins.json", JSON.stringify({
      sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
      table_id: table.id, occupancy_id: snapshot.active_occupancy.id, tab_ids: details.map(d => d.id),
      order_ids: details.map(d => d.orders[0].id), guest_replays: attempts.length,
      kitchen_reconnected: true, changed_payload_status: conflict.status,
      original_key_sha256: createHash("sha256").update(JSON.parse(attempts[0]).idempotency_key).digest("hex"), status: "PASS",
    }, null, 2));
  } finally { await guestContext.close(); await kitchenContext.close(); }
});
