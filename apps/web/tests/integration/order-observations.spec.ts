import { addCatalogItem } from "../visual/category-actions";
import { expect, test } from "./fixtures";
import { selectExistingAttendanceTab } from "./attendance-helpers";

for (const unavailable of [false, true]) test(`Passive order observations preserve immutable recovery; unavailable=${unavailable}`, async ({ page }) => {
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Opções do atendimento", exact: true, includeHidden: true })).toBeAttached();
  const label = `Passive recovery ${unavailable}`;
  const created = await page.evaluate(async display_label => {
    const response = await fetch("/api/attendance/tabs/", { method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ display_label }) });
    return response.status;
  }, label);
  expect(created).toBe(201);
  await selectExistingAttendanceTab(page, label);
  await page.getByRole("region", { name: "Comanda selecionada", exact: true }).getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  const observations: Array<Record<string, unknown>> = [];
  const observationStatuses: number[] = [];
  await page.route("**/api/attendance-observations", async route => {
    const body = route.request().postDataJSON();
    observations.push(...body.events);
    if (unavailable) { await route.abort(); return; }
    const response = await route.fetch();
    observationStatuses.push(response.status());
    await route.fulfill({ response });
  });
  const attempts: string[] = [];
  let tabId = "";
  await page.route(/\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/, async route => {
    attempts.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, "") });
    expect(response.status()).toBe(attempts.length === 1 ? 201 : 200);
    tabId = (await response.json()).tab_id;
    if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.getByLabel("Buscar produto").fill("Kitchen E2E item");
  await addCatalogItem(page, "Kitchen E2E item");
  await page.getByRole("region", { name: "Comanda selecionada", exact: true }).getByRole("button", { name: "Ver resumo", exact: true }).click();
  await page.getByRole("button", { name: /^Enviar 1 item/ }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
  await expect.poll(() => observations.filter(e => e.kind === "ATTEMPT_FINISHED").length).toBe(1);
  expect(observations.find(e => e.kind === "ATTEMPT_FINISHED")?.outcome).toBe("UNKNOWN");
  const saved = await page.evaluate(() => sessionStorage.getItem("rodada.intent.staff-order.v1"));
  await page.reload();
  if (!unavailable) await page.route(/\/api\/attendance\/tabs\/[^/]+\/$/, async route => {
    const response = await route.fetch();
    if (attempts.length === 2) {
      const body = await response.json();
      await route.fulfill({ response, json: { ...body, orders: [] } });
    } else await route.fulfill({ response });
  });
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  if (!unavailable) {
    await expect.poll(() => observations.filter(e => e.kind === "ATTEMPT_FINISHED").length).toBe(2);
    expect(observations.filter(e => e.kind === "ATTEMPT_FINISHED")[1].outcome).toBe("UNKNOWN");
    expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.staff-order.v1"))).toBe(saved);
    await page.getByRole("button", { name: "Verificar mesmo pedido" }).click();
  }
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  await expect.poll(() => observations.filter(e => e.kind === "ATTEMPT_FINISHED").length).toBe(unavailable ? 2 : 3);
  const finished = observations.filter(e => e.kind === "ATTEMPT_FINISHED");
  expect(finished.map(e => [e.outcome, e.recovery])).toEqual(unavailable ? [["UNKNOWN", false], ["CONFIRMED", true]] : [["UNKNOWN", false], ["UNKNOWN", true], ["CONFIRMED", true]]);
  expect(new Set(observations.map(e => e.intent_ref)).size).toBe(1);
  expect(new Set(finished.map(e => e.attempt_id)).size).toBe(unavailable ? 2 : 3);
  expect(observations.filter(e => e.kind === "INTENT_SAVED")).toHaveLength(1);
  expect(observations.every(e => /^[a-f0-9]{64}$/.test(String(e.intent_ref)))).toBe(true);
  expect(attempts).toHaveLength(unavailable ? 2 : 3); expect(new Set(attempts).size).toBe(1);
  const key = JSON.parse(attempts[0]).idempotency_key;
  expect(JSON.stringify(observations)).not.toContain(key);
  expect(observations.every(e => !["lines", "tab", "product_id", "message"].some(k => k in e))).toBe(true);
  if (!unavailable) await expect.poll(() => observationStatuses).toEqual([204, 204, 204, 204]);
  const detail = await page.evaluate(async id => (await fetch(`/api/pos/tabs/${id}/`)).json(), tabId);
  expect(detail.orders).toHaveLength(1); expect(detail.exposure_cents).toBe(1000); expect(detail.payments).toHaveLength(0);
  expect(await page.evaluate(() => sessionStorage.getItem("rodada.intent.staff-order.v1"))).toBeNull();
});

test("Passive BFF preserves cookies and never refreshes an expired/missing access token", async ({ request }) => {
  const path = "/api/attendance-observations";
  for (const cookie of ["rodada_staff_refresh=invalid-refresh", "rodada_staff_access=expired-access; rodada_staff_refresh=invalid-refresh"]) {
    const response = await request.post(path, { headers: { cookie }, data: {} });
    expect(response.status()).toBe(401);
    expect(response.headers()["set-cookie"]).toBeUndefined();
  }
  const crossOrigin = await request.post(path, { headers: { origin: "https://other.invalid" }, data: {} });
  expect(crossOrigin.status()).toBe(403);
  expect(crossOrigin.headers()["set-cookie"]).toBeUndefined();
  expect((await request.post(path, { data: "x".repeat(8193) })).status()).toBe(413);
});
