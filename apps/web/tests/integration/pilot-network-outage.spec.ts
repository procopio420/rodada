import { expect, test, type Page } from "./fixtures";
import { addCatalogItem } from "../visual/category-actions";
import { openNamedAttendanceTab } from "./attendance-helpers";
import { writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";

// Spec014 duplicate submit/reconnect and Spec033 AC-05/13/21. Only transport
// is fault-injected; canonical mutations reach the real BFF/API/PostgreSQL.
const outageMs = 90_000;
async function api(page: Page, path: string, data?: unknown) {
  return page.evaluate(async ({ path, data }) => {
    const response = await fetch(`/api/pos/${path}`, data === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`Test API ${response.status}: ${path}`);
    return response.json();
  }, { path, data });
}

for (const kind of ["order", "cash"] as const) test(`90s browser network outage after ${kind} commit preserves one effect`, async ({ page, browser }, info) => {
  test.setTimeout(150_000);
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  let tabId = "", shiftId = "", beforeCash = 0;
  if (kind === "order") {
    await page.goto("/attendance");
    await openNamedAttendanceTab(page, "Network outage order");
    await addCatalogItem(page, "Kitchen E2E item", 2);
    await page.getByRole("region", { name: "Comanda selecionada", exact: true }).getByRole("button", { name: "Ver resumo", exact: true }).click();
  } else {
    const point = (await api(page, "cash/points/")).results[0];
    const shift = point.active_shift ?? await api(page, "cash/shifts/", {
      cash_point_id: point.id, opening_float_cents: 0, business_date: "2026-11-03", idempotency_key: "network-cash-shift",
    });
    shiftId = shift.id;
    beforeCash = (await api(page, `cash/shifts/${shiftId}/`)).expected_cents;
    const product = (await api(page, "catalog/products/")).results.find((p: { name: string }) => p.name === "Kitchen E2E item");
    const tab = await api(page, "tabs/", { display_label: "Network outage cash" });
    tabId = tab.id;
    await api(page, `tabs/${tab.id}/orders/confirm/`, { idempotency_key: "network-cash-order", lines: [{ product_id: product.id, quantity: 2 }] });
    await page.goto("/pos");
    await page.getByRole("button", { name: /Network outage cash ·/ }).click();
    await page.getByLabel("Valor do pagamento").fill("10,00");
  }
  const observerContext = await browser.newContext({ baseURL: info.project.use.baseURL, storageState: await page.context().storageState() });
  try {
    const observer = await observerContext.newPage();
    await observer.goto("/staff");
    const attempts: string[] = [];
    let canonicalId = "";
    let offlineStarted = 0;
    const pattern = kind === "order" ? /\/api\/attendance\/tabs\/[^/]+\/orders\/confirm\/$/ : new RegExp(`/api/pos/tabs/${tabId}/payments/?$`);
    await page.route(pattern, async route => {
      attempts.push(route.request().postData()!);
      const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
      expect(response.status()).toBe(kind === "order" && attempts.length > 1 ? 200 : 201);
      const body = await response.json();
      if (!canonicalId) {
        canonicalId = body.id;
        if (kind === "order") tabId = body.tab_id;
        await page.context().setOffline(true);
        offlineStarted = performance.now();
        await route.abort();
      } else {
        expect(body.id).toBe(canonicalId);
        await route.fulfill({ response });
      }
    });
    if (kind === "order") await page.getByRole("button", { name: /^Enviar 2 itens/ }).click();
    else await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
    const verify = page.getByRole("button", { name: kind === "order" ? "Verificar mesmo pedido" : "Verificar mesmo recebimento", exact: true });
    await expect(verify).toBeVisible();
    await expect.poll(() => page.evaluate(() => navigator.onLine)).toBe(false);
    expect(await page.evaluate(async () => {
      try { await fetch("/api/auth/me"); return "unexpected-network-success"; }
      catch { return "unreachable"; }
    })).toBe("unreachable");
    const key = kind === "order" ? "rodada.intent.staff-order.v1" : "rodada.intent.pos-cash.v1";
    const originalIntent = await page.evaluate(k => sessionStorage.getItem(k), key);
    expect(originalIntent).toBeTruthy();
    const checkpoints: { elapsed_ms: number; exposure_cents: number; orders: number; payments: number }[] = [];
    async function checkCanonical() {
      const detail = await api(observer, `tabs/${tabId}/`);
      expect(detail.orders).toHaveLength(1);
      expect(detail.exposure_cents).toBe(kind === "order" ? 2000 : 1000);
      expect(detail.state).toBe("OPEN");
      if (kind === "order") {
        expect(detail.orders[0].id).toBe(canonicalId);
        expect(detail.payments).toHaveLength(0);
      } else {
        expect(detail.payments).toHaveLength(1);
        expect(detail.payments[0].id).toBe(canonicalId);
        const shift = await api(observer, `cash/shifts/${shiftId}/`);
        expect(shift.expected_cents - beforeCash).toBe(1000);
        expect(shift.movements.filter((m: { payment_id: string }) => m.payment_id === canonicalId)).toHaveLength(1);
      }
      checkpoints.push({ elapsed_ms: Math.round(performance.now() - offlineStarted), exposure_cents: detail.exposure_cents, orders: detail.orders.length, payments: detail.payments.length });
    }
    await checkCanonical();
    while (performance.now() - offlineStarted < outageMs) {
      await page.waitForTimeout(Math.min(15_000, outageMs - (performance.now() - offlineStarted)));
      expect(await page.evaluate(() => navigator.onLine)).toBe(false);
      expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(originalIntent);
      await expect(verify).toBeVisible();
      await expect(page.getByText(kind === "order" ? "Pedido confirmado." : "Recebimento confirmado. Saldo atualizado.", { exact: true })).toHaveCount(0);
      await checkCanonical();
    }
    const offlineElapsed = Math.round(performance.now() - offlineStarted);
    expect(offlineElapsed).toBeGreaterThanOrEqual(outageMs);
    expect(attempts).toHaveLength(1);
    await page.screenshot({ path: info.outputPath(`${kind}-offline.png`), fullPage: true });
    await page.context().setOffline(false);
    await page.reload();
    await expect(verify).toBeEnabled();
    expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBe(originalIntent);
    expect(attempts).toHaveLength(1);
    await verify.dblclick();
    await expect(page.getByText(kind === "order" ? "Pedido confirmado." : "Recebimento confirmado. Saldo atualizado.", { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(2);
    expect(attempts[1]).toBe(attempts[0]);
    await expect.poll(() => page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
    await checkCanonical();
    await page.screenshot({ path: info.outputPath(`${kind}-recovered.png`), fullPage: true });
    const record = { kind, product_sha: "67972d09200d43357b5b88dc0f64218967e4c24b", fault: "Chromium BrowserContext offline after real backend commit; first response dropped", requested_outage_ms: outageMs, measured_outage_ms: offlineElapsed,
      tab_id: tabId, canonical_id: canonicalId, shift_id: shiftId || null,
      backend_mutation_attempts: attempts.length, same_payload: attempts[0] === attempts[1],
      payload_sha256: createHash("sha256").update(attempts[0]).digest("hex"), checkpoints,
      result: "PASS", limitation: "browser-wide network emulation; not physical Wi-Fi, backend outage or offline first-time acceptance" };
    await writeFile(info.outputPath(`${kind}-outage.json`), JSON.stringify(record, null, 2));
    await info.attach(`${kind}-outage`, { path: info.outputPath(`${kind}-outage.json`), contentType: "application/json" });
  } finally {
    await page.context().setOffline(false);
    await observerContext.close();
  }
});
