import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";

test("SSE-only interruption leaves real HTTP order usable and station polling recovers NEW", async ({ page, browser }) => {
  test.setTimeout(100_000);
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill(f.venue_slug);
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const r = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(`${path}: ${r.status}`); return r.json();
  }, { path, body });
  const label = `SSE-only-${Date.now()}`;
  const table = await api("hospitality/tables/", { label, guest_ordering_mode: "DIRECT" });
  const context = await browser.newContext({ baseURL: "http://127.0.0.1:3110", storageState: await page.context().storageState() });
  try {
    let cuts = 0; const cursors: string[] = [];
    await context.route("**/api/realtime/stream/**", async route => {
      cuts++; const cursor = new URL(route.request().url()).searchParams.get("cursor"); if (cursor) cursors.push(cursor);
      await route.abort();
    });
    const station = await context.newPage(); await station.goto("/kitchen");
    await expect.poll(() => cuts).toBeGreaterThan(0);
    await page.goto("/attendance");
    await page.getByRole("button", { name: new RegExp(`^Mesa ${label}`) }).click();
    await page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
    await page.getByRole("dialog").getByRole("textbox").fill(label);
    await page.getByRole("dialog").getByRole("button", { name: /Abrir/ }).click();
    const dialog = page.locator(".attendanceOrderDialog");
    await dialog.getByRole("button", { name: /^Android Compose Test Meal/ }).click();
    await dialog.getByRole("button", { name: /Pedido atual/ }).click();
    await dialog.getByRole("button", { name: /^Confirmar pedido/ }).click();
    await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
    // No station reload: production HTTP fallback must discover the committed order.
    const action = station.getByRole("button", { name: new RegExp(`^Iniciar preparo:.*${label}$`) });
    await expect(action).toBeVisible({ timeout: 35_000 });
    await expect(station.getByRole("status").filter({ hasText: /Dados possivelmente desatualizados/ })).toBeVisible({ timeout: 45_000 });
    const snapshot = (await api("hospitality/tables/")).results.find((t: { id: string }) => t.id === table.id);
    const tab = await api(`tabs/${snapshot.active_occupancy.tabs[0].id}/`);
    expect(tab.orders).toHaveLength(1); expect(tab.orders[0].items[0].state).toBe("NEW");
    const previous = cursors[0]; expect(previous).toBeTruthy();
    let resumedCursor = "";
    station.on("request", request => { const u = new URL(request.url()); if (u.pathname === "/api/realtime/stream/") resumedCursor = u.searchParams.get("cursor") ?? ""; });
    await context.unroute("**/api/realtime/stream/**");
    await station.evaluate(() => window.dispatchEvent(new Event("online")));
    await expect(station.getByRole("status").filter({ hasText: "Ao vivo" })).toBeVisible({ timeout: 40_000 });
    expect(resumedCursor).toBe(previous);
    await expect(action).toBeVisible();
    await writeFile("../../artifacts/sse-browser.json", JSON.stringify({ sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(), database_instance_id: f.database_instance_id, venue_id: f.venue_id, tab_id: tab.id, order_id: tab.orders[0].id, item_id: tab.orders[0].items[0].id, cuts, cursor_before: previous, cursor_resumed: resumedCursor, status: "PASS", state: "NEW", scope: "real Web UI command; only station SSE transport aborted; HTTP polling; no native outage proof" }, null, 2));
  } finally { await context.close(); }
});
