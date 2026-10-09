import { expect, test } from "@playwright/test";

test("real API alert policy, acknowledgement and canonical resolution", async ({ page }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  async function call(path: string, method = "GET", body?: unknown) {
    const result = await page.evaluate(async ({ path, method, body }) => {
      const response = await fetch(path, { method, headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
      return { status: response.status, body: await response.json() };
    }, { path, method, body });
    expect(result.status, JSON.stringify(result.body)).toBeLessThan(300);
    return result.body;
  }
  const { product } = await call("/api/pos/catalog/resolve-or-create/", "POST", {
    name: "Strategic real alert E2E", price_cents: 1000, fulfillment_station: "BAR",
  });
  await page.goto("/manage/alerts/settings");
  await expect(page.getByLabel("Produção: atenção após (segundos)")).toHaveValue("600");
  await page.getByLabel("Confirme seu PIN").fill("2468");
  await page.getByRole("button", { name: "Salvar política" }).click();
  await expect(page.getByText("Política confirmada pelo servidor. Em vigor agora para avaliação de alertas.")).toBeVisible();
  const policy = await call("/api/pos/management/alert-policy/");
  await call("/api/pos/management/alert-policy/", "PATCH", {
    expected_version: policy.version,
    fulfillment_warning_seconds: policy.fulfillment_warning_seconds,
    fulfillment_danger_seconds: policy.fulfillment_danger_seconds,
    payment_pending_seconds: policy.payment_pending_seconds,
    strategic_product_ids: [product.id], reason: "Release integration evidence",
  });
  await call(`/api/pos/catalog/products/${product.id}/availability/`, "POST", { state: "UNAVAILABLE" });
  const alerts = await call("/api/pos/management/alerts/");
  const alert = alerts.results.find((value: { source: { id: string } }) => value.source.id === product.id);
  expect(alert.status).toBe("ACTIVE");
  await page.goto("/manage");
  await page.getByRole("button", { name: "Registrar ciência" }).click();
  await expect(page.getByText("Ciência registrada · condição continua ativa")).toBeVisible();
  await call(`/api/pos/catalog/products/${product.id}/availability/`, "POST", { state: "AVAILABLE" });
  await page.goto(`/manage/alerts/${alert.id}`);
  await expect(page.getByText("Resolvido pela condição canônica. Este alerta permanece no histórico.")).toBeVisible();
  await expect(page.getByText(`Contexto: Produto · ${product.id}`)).toBeVisible();
  const detail = await call(`/api/pos/management/alerts/${alert.id}/`);
  expect(detail.history.map((event: { kind: string }) => event.kind)).toEqual(["ACTIVATED", "ACKNOWLEDGED", "RESOLVED"]);
});
