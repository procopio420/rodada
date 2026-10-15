import { expect, test, type Page } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

async function login(page: Page, foreign = false) {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill(foreign ? "android-post-drop-foreign-ci" : "android-post-drop-ci");
  await page.getByLabel("Operador", { exact: true }).fill(foreign ? "android-post-drop-foreign-operator" : "android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
}
async function api(page: Page, path: string, body?: unknown) {
  return page.evaluate(async ({ path, body }) => {
    const r = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return { status: r.status, body: await r.json() };
  }, { path, body });
}
const sha = () => execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();

test("Venue A/B canonical Tab reads and mutations stay isolated through real BFF", async ({ page, browser }) => {
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  await login(page);
  const tab = await api(page, "tabs/", { display_label: `Isolation A ${Date.now()}` });
  expect(tab.status).toBe(201);
  const foreignContext = await browser.newContext({ baseURL: "http://127.0.0.1:3110" });
  try {
    const foreign = await foreignContext.newPage(); await login(foreign, true);
    const ownA = await api(page, `tabs/${tab.body.id}/`);
    const ownB = await api(foreign, `tabs/${f.foreign_tab_id}/`);
    expect(ownA.status).toBe(200); expect(ownB.status).toBe(200);
    const denied = [];
    for (const [client, target, product] of [[page, f.foreign_tab_id, f.foreign_product_id], [foreign, tab.body.id, f.product_id]] as const) {
      const read = await api(client, `tabs/${target}/`);
      const mutation = await api(client, `tabs/${target}/orders/confirm/`, { idempotency_key: crypto.randomUUID(), lines: [{ product_id: product, quantity: 1 }] });
      expect(read.status).toBe(404); expect(mutation.status).toBe(404);
      denied.push({ tab_id: target, get: read.status, post: mutation.status });
    }
    expect((await api(page, `tabs/${tab.body.id}/`)).body).toEqual(ownA.body);
    expect((await api(foreign, `tabs/${f.foreign_tab_id}/`)).body).toEqual(ownB.body);
    await writeFile("../../artifacts/isolation-browser.json", JSON.stringify({ sha: sha(), database_instance_id: f.database_instance_id, venue_ids: [f.venue_id, f.foreign_venue_id], tab_ids: [tab.body.id, f.foreign_tab_id], status: "PASS", denied, scope: "localhost BFF session/IDs; external Host ingress and native/Guest crossings unproven" }, null, 2));
  } finally { await foreignContext.close(); }
});

test("revoked Web session cannot replay captured UI intent and new login requires review", async ({ page, browser }) => {
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  await login(page);
  const table = (await api(page, "hospitality/tables/", { label: `Revocation ${Date.now()}`, guest_ordering_mode: "DIRECT" })).body;
  await page.goto("/attendance");
  await page.getByRole("button", { name: new RegExp(`^Mesa ${table.label}`) }).click();
  await page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
  await page.getByRole("dialog").getByRole("textbox").fill(table.label);
  await page.getByRole("dialog").getByRole("button", { name: /Abrir/ }).click();
  const dialog = page.locator(".attendanceOrderDialog");
  await dialog.getByRole("button", { name: /^Android Post Drop Test Soda/ }).click();
  await dialog.getByRole("button", { name: /Pedido atual/ }).click();
  let payload = "", target = "";
  await page.route(/\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/, async route => {
    payload = route.request().postData()!; target = route.request().url();
    await route.abort(); // Real connectivity failure BEFORE server receives the captured UI command.
  });
  await dialog.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  const saved = await page.evaluate(() => sessionStorage.getItem("rodada.intent.staff-order.v1"));
  expect(saved).toBeTruthy();
  const intent = JSON.parse(saved!);
  const oldContext = await browser.newContext({ storageState: await page.context().storageState(), baseURL: "http://127.0.0.1:3110" });
  try {
    expect(await page.evaluate(async () => (await fetch("/api/auth/logout", { method: "POST" })).status)).toBe(204);
    const old = await oldContext.newPage(); await old.goto("/staff");
    const denied = await old.evaluate(async ({ target, payload }) => {
      const read = await fetch("/api/auth/me");
      const post = await fetch(target, { method: "POST", headers: { "Content-Type": "application/json" }, body: payload });
      return { get: read.status, post: post.status };
    }, { target, payload });
    expect([401, 403]).toContain(denied.get); expect([401, 403]).toContain(denied.post);
    await page.unroute(/\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/);
    await login(page); await page.goto("/attendance");
    await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
    await expect(page.getByText("Este pedido pertence à sessão original. Solicite revisão à gerência; ele não será enviado nesta sessão.", { exact: true })).toBeVisible();
    expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.staff-order.v1"))).toBe(saved);
    const detail = await api(page, `tabs/${intent.tab}/`);
    expect(detail.body.orders).toHaveLength(0); expect(detail.body.exposure_cents).toBe(0); expect(detail.body.payments).toHaveLength(0);
    await writeFile("../../artifacts/revocation-browser.json", JSON.stringify({ sha: sha(), database_instance_id: f.database_instance_id, venue_id: f.venue_id, tab_id: intent.tab, session_id: intent.session, request_key_hash: createHash("sha256").update(intent.payload.idempotency_key).digest("hex"), status: "PASS", denied, intent_preserved: true, scope: "Web logout revokes original session; captured before-commit intent; native expiry/refresh/SSE unproven" }, null, 2));
  } finally { await oldContext.close(); }
});

test("Guest A/B sessions reject foreign selectors and product IDs without ledger effects", async ({ page, browser }) => {
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  await login(page);
  const foreignContext = await browser.newContext({ baseURL: "http://127.0.0.1:3110" });
  const guestContexts = await Promise.all([0, 1].map(() => browser.newContext({ baseURL: "http://127.0.0.1:3110" })));
  try {
    const foreign = await foreignContext.newPage(); await login(foreign, true);
    const tables = [];
    for (const [index, staff] of [page, foreign].entries()) {
      const result = await api(staff, "hospitality/tables/", { label: `Guest isolation ${index} ${Date.now()}`, guest_ordering_mode: "DIRECT" });
      expect(result.status).toBe(201); tables.push(result.body);
    }
    const tabs: string[] = [], denials = [];
    for (const index of [0, 1]) {
      const guest = await guestContexts[index].newPage();
      await guest.goto(`/guest/${tables[index].public_token}`);
      await guest.getByRole("button", { name: "Abrir minha comanda", exact: true }).click();
      const proof = await guest.evaluate(async ({ selector, foreignSelector, foreignProduct }) => {
        const get = async (s: string) => {
          const r = await fetch("/api/guest/context/", { headers: { "X-Guest-Session": s } });
          return { status: r.status, body: await r.json() };
        };
        const own = await get(selector), deniedRead = await get(foreignSelector);
        const r = await fetch("/api/guest/orders/confirm/", { method: "POST", headers: { "Content-Type": "application/json", "X-Guest-Session": selector }, body: JSON.stringify({ idempotency_key: crypto.randomUUID(), lines: [{ product_id: foreignProduct, quantity: 1 }] }) });
        return { own, deniedRead, deniedPost: { status: r.status, body: await r.json() } };
      }, { selector: tables[index].public_token, foreignSelector: tables[1-index].public_token, foreignProduct: index === 0 ? f.foreign_product_id : f.product_id });
      expect(proof.own.status).toBe(200); expect([401,403]).toContain(proof.deniedRead.status);
      expect(proof.deniedPost.status).toBe(409); expect(proof.deniedPost.body.code).toBe("PRODUCTS_NOT_CONFIRMABLE");
      tabs.push(proof.own.body.tab.id); denials.push({ get: proof.deniedRead.status, post: proof.deniedPost.status });
    }
    await writeFile("../../artifacts/guest-isolation-browser.json", JSON.stringify({ sha: sha(), database_instance_id: f.database_instance_id, venue_ids: [f.venue_id, f.foreign_venue_id], tab_ids: tabs, status: "PASS", denials, scope: "local Guest/BFF selectors and product identities; external Host/HMAC routing remains separate #130 gate" }, null, 2));
  } finally { await Promise.all([...guestContexts, foreignContext].map(context => context.close())); }
});
