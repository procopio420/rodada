import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";

test("test-only partial cash on Compose Tab, residual close guard and audited drawer discrepancy", async ({ page }) => {
  test.setTimeout(120_000);
  const fixture = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  const native = JSON.parse(await readFile(process.env.RODADA_ANDROID_COMPOSE_PROOF!, "utf8"));
  expect(native.native_ui).toBe("production MainActivity Compose");
  expect(native.database).toBe("rodada_android_post_drop");
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("android-post-drop-ci");
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const read = (path: string) => page.evaluate(async path => {
    const r = await fetch(`/api/pos/${path}`);
    if (!r.ok) throw new Error(`${path}: ${r.status}`);
    return r.json();
  }, path);
  const before = await read(`tabs/${native.original_tab_id}/`);
  expect(before.payments_cents).toBe(0);
  expect(before.exposure_cents).toBeGreaterThan(300);
  await page.goto("/cash");
  await page.getByLabel("Ponto de caixa", { exact: true }).selectOption(fixture.cash_point_id);
  await page.getByLabel("Fundo inicial", { exact: true }).fill("100,00");
  await page.getByRole("button", { name: "Confirmar abertura", exact: true }).click();
  await expect(page.getByRole("button", { name: "Registrar suprimento", exact: true })).toBeVisible();
  const point = (await read("cash/points/")).results.find((p: { id: string }) => p.id === fixture.cash_point_id);
  expect(point.active_shift).toBeTruthy();
  const shiftId = point.active_shift.id;
  await page.getByLabel("Valor", { exact: true }).fill("20,00");
  await page.getByLabel("Motivo", { exact: true }).fill("Disposable #106 supply");
  await page.getByRole("button", { name: "Registrar suprimento", exact: true }).click();
  await expect.poll(async () => (await read(`cash/shifts/${shiftId}/`)).expected_cents).toBe(12000);
  await page.getByRole("button", { name: "Sangria", exact: true }).click();
  await page.getByLabel("Valor", { exact: true }).fill("10,00");
  await page.getByLabel("Motivo", { exact: true }).fill("Disposable #106 withdrawal");
  await page.getByRole("button", { name: "Registrar sangria", exact: true }).click();
  await expect.poll(async () => (await read(`cash/shifts/${shiftId}/`)).expected_cents).toBe(11000);
  await page.goto("/pos");
  await page.getByRole("button", { name: new RegExp(`^${native.tab_label} ·`) }).click();
  // Positive balance must never be closed; server rejection is visible in UI.
  const deniedClose = page.waitForResponse(r => new URL(r.url()).pathname.replace(/\/$/, "") === `/api/pos/tabs/${native.original_tab_id}/close` && r.request().method() === "POST" && r.status() >= 400);
  await page.getByRole("button", { name: "Fechar comanda", exact: true }).click();
  expect((await deniedClose).status()).toBe(409);
  expect((await read(`tabs/${native.original_tab_id}/`)).state).not.toBe("CLOSED");
  const paymentBodies: string[] = []; let firstPaymentId = "";
  const paymentRoute = new RegExp(`/api/pos/tabs/${native.original_tab_id}/payments/?$`);
  await page.route(paymentRoute, async route => {
    paymentBodies.push(route.request().postData()!);
    const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
    // A replay may return 201 again while reusing the same committed Payment.
    // The stable Payment ID, identical request body, and SQL cardinality prove idempotency.
    expect([200, 201]).toContain(response.status());
    if (paymentBodies.length === 1) expect(response.status()).toBe(201);
    const body = await response.json();
    if (!firstPaymentId) firstPaymentId = body.id; else expect(body.id).toBe(firstPaymentId);
    if (paymentBodies.length === 1) await route.abort(); else await route.fulfill({ response });
  });
  await page.getByLabel("Valor do pagamento", { exact: true }).fill("3,00");
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesmo recebimento", exact: true })).toBeEnabled();
  await page.reload();
  await page.getByRole("button", { name: "Verificar mesmo recebimento", exact: true }).dblclick();
  await expect(page.getByText("Recebimento confirmado. Saldo atualizado.", { exact: true })).toBeVisible();
  expect(paymentBodies).toHaveLength(2); expect(paymentBodies[1]).toBe(paymentBodies[0]);
  await page.unroute(paymentRoute);
  const partial = await read(`tabs/${native.original_tab_id}/`);
  expect(partial.exposure_cents).toBe(before.exposure_cents - 300);
  expect(partial.payments).toHaveLength(1);
  expect(partial.payments_cents).toBe(300);
  // Read-only: guest/Web consuming Tabs must not inherit this payment.
  const origins = JSON.parse(await readFile("../../artifacts/browser-origins.json", "utf8"));
  for (const id of origins.tab_ids) expect((await read(`tabs/${id}/`)).payments_cents).toBe(0);
  // Compensatory manual-test refund preserves the original payment and charge rows.
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption(native.original_tab_id);
  await page.getByLabel("PIN do gerente").fill("2468");
  await page.getByRole("button", { name: "Confirmar PIN", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("PIN confirmado");
  await page.getByLabel("Valor a estornar").fill("1,00");
  await page.getByLabel("Motivo do estorno").fill("Disposable #106 compensatory refund; retain original ledger");
  await page.getByRole("button", { name: "Confirmar estorno", exact: true }).click();
  await expect(page.getByText(/^Estorno confirmado\./)).toBeVisible();
  const refunded = await read(`tabs/${native.original_tab_id}/`);
  expect(refunded.refunds_cents).toBe(100);
  expect(refunded.payments[0].id).toBe(firstPaymentId);
  expect(refunded.payments[0].confirmed_at).toBe(partial.payments[0].confirmed_at);
  expect(refunded.payments[0].amount_cents).toBe(300);
  expect(refunded.exposure_cents).toBe(partial.exposure_cents + 100);
  const refundId = refunded.payments[0].refunds[0].id;
  await page.goto("/pos");
  await page.getByRole("button", { name: new RegExp(`^${native.tab_label} ·`) }).click();
  await page.getByLabel("Valor do pagamento", { exact: true }).fill((refunded.exposure_cents / 100).toFixed(2).replace(".", ","));
  await page.getByRole("button", { name: "Receber em dinheiro", exact: true }).click();
  await expect.poll(async () => (await read(`tabs/${native.original_tab_id}/`)).exposure_cents).toBe(0);
  const paid = await read(`tabs/${native.original_tab_id}/`);
  expect(paid.payments).toHaveLength(2);
  expect(paid.payments_cents).toBe(before.exposure_cents + 100);
  await page.getByRole("button", { name: "Fechar comanda", exact: true }).click();
  await expect.poll(async () => (await read(`tabs/${native.original_tab_id}/`)).state).toBe("CLOSED");
  await page.goto("/cash");
  await page.getByLabel("Ponto de caixa", { exact: true }).selectOption(fixture.cash_point_id);
  await page.getByRole("button", { name: "Conferir caixa", exact: true }).click();
  const expected = 11000 + before.exposure_cents;
  await page.getByLabel("Contado", { exact: true }).fill(((expected - 1000) / 100).toFixed(2).replace(".", ","));
  await page.getByRole("button", { name: "Confirmar fechamento", exact: true }).click();
  await expect.poll(async () => (await read(`cash/shifts/${shiftId}/`)).status).toBe("CLOSED");
  const closed = await read(`cash/shifts/${shiftId}/`);
  expect(closed.discrepancy_cents).toBe(-1000);
  expect(closed.review_status).toBe("PENDING");
  await page.getByLabel("Motivo da revisão", { exact: true }).fill("Disposable #106 recorded mismatch; preserve original snapshot");
  await page.getByRole("button", { name: "Revisar divergência", exact: true }).click();
  const pin = page.getByLabel("Seu PIN", { exact: true });
  await expect.poll(async () => (await pin.isVisible()) || (await read(`cash/shifts/${shiftId}/`)).review_status === "REVIEWED").toBe(true);
  if (await pin.isVisible()) {
    await pin.fill("2468");
    await page.getByRole("button", { name: "Confirmar e continuar", exact: true }).click();
  }
  await expect.poll(async () => (await read(`cash/shifts/${shiftId}/`)).review_status).toBe("REVIEWED");
  const reviewed = await read(`cash/shifts/${shiftId}/`);
  expect(reviewed.expected_at_close_cents).toBe(closed.expected_at_close_cents);
  expect(reviewed.discrepancy_cents).toBe(closed.discrepancy_cents);
  await page.goto("/manage");
  await expect(page.getByRole("heading", { name: "O que precisa de atenção", exact: true })).toBeVisible();
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "Relatórios operacionais", exact: true })).toBeVisible();
  await page.getByLabel("De", { exact: true }).fill(closed.business_date);
  await page.getByLabel("Até", { exact: true }).fill(closed.business_date);
  await page.getByRole("button", { name: "Aplicar período", exact: true }).click();
  await expect(page.getByRole("button", { name: "Exportar CSV", exact: true })).toBeEnabled();
  const report = await read(`management/reports/?start=${closed.business_date}&end=${closed.business_date}`);
  expect(report.totals.paid_cents).toBe(before.exposure_cents + 100);
  expect(report.totals.refunds_cents).toBe(100);
  await writeFile("../../artifacts/financial-browser.json", JSON.stringify({
    sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(), status: "PASS", test_only: true,
    cash_response_loss_replays: paymentBodies.length, first_payment_id: firstPaymentId,
    tab_id: native.original_tab_id, payment_ids: paid.payments.map((p: { id: string }) => p.id), shift_id: shiftId,
    business_date: closed.business_date, report_totals: report.totals, paid_cents: before.exposure_cents + 100, refund_cents: 100, refund_id: refundId, expected_cents: expected, discrepancy_cents: -1000,
  }, null, 2));
});
