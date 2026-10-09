import { test, expect, type Page } from "@playwright/test";
async function api(page: Page, path: string, body?: unknown) {
  const result = await page.evaluate(async ({ path, body }) => {
    const response = await fetch(path, { method: body === undefined ? "GET" : "POST", headers: body === undefined ? {} : { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
    return { status: response.status, data: await response.json() };
  }, { path, body });
  expect(result.status, JSON.stringify(result.data)).toBeLessThan(300);
  return result.data;
}
test("manager configures real persisted customization; guest prices and kitchen snapshot survive unavailability", async ({ page, browser }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const { product } = await api(page, "/api/pos/catalog/resolve-or-create/", { name: "Hambúrguer configurável", price_cents: 1000, fulfillment_station: "KITCHEN" });
  await page.goto("/manage/catalog");
  await page.getByLabel("Produto", { exact: true }).selectOption(product.id);
  async function save() {
    await page.getByRole("button", { name: "Salvar configuração", exact: true }).click();
    await expect(page.getByLabel("Nome", { exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Criar grupo", exact: true })).toBeEnabled();
  }
  for (const [name, cents] of [["Simples", "1000"], ["Duplo", "2000"]]) {
    await page.getByRole("button", { name: "Criar variação", exact: true }).click();
    await page.getByLabel("Nome", { exact: true }).fill(name);
    await page.getByLabel("Preço em centavos").fill(cents); await save();
  }
  await page.getByRole("button", { name: "Criar grupo", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Ponto");
  await page.getByLabel("Mínimo (1 ou mais = obrigatório)").fill("1"); await save();
  await page.getByRole("button", { name: "Criar opção em Ponto", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Ao ponto"); await save();
  await page.getByRole("button", { name: "Criar grupo", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Adicionais");
  await page.getByLabel("Seleção", { exact: true }).selectOption("MULTI");
  await page.getByLabel("Máximo", { exact: true }).fill("2"); await save();
  for (const [name, cents] of [["Bacon", "500"], ["Queijo", "300"]]) {
    await page.getByRole("button", { name: "Criar opção em Adicionais", exact: true }).click();
    await page.getByLabel("Nome", { exact: true }).fill(name);
    await page.getByLabel("Adicional em centavos").fill(cents);
    await page.getByLabel("Tipo de opção").selectOption("ADD"); await save();
  }
  const schema = (await api(page, "/api/pos/catalog/products/")).results.find((p: { id: string }) => p.id === product.id);
  const variant = schema.variants.find((v: { name: string }) => v.name === "Duplo");
  const selected = schema.modifier_groups.flatMap((g: { options: { id: string }[] }) => g.options.map(o => o.id));
  const tab = await api(page, "/api/pos/tabs/", { display_label: "Customized waiter" });
  const line = { product_id: product.id, quantity: 1, variant_id: variant.id, modifier_option_ids: selected, special_instructions: "Molho separado" };
  const payload = { idempotency_key: "custom-web-staff", lines: [line] };
  const first = await api(page, `/api/pos/tabs/${tab.id}/orders/confirm/`, payload);
  expect(first.items[0].unit_price_cents).toBe(2800);
  expect((await api(page, `/api/pos/tabs/${tab.id}/orders/confirm/`, payload)).id).toBe(first.id);
  const table = await api(page, "/api/pos/hospitality/tables/", { label: "Custom guest table", guest_ordering_mode: "DIRECT" });
  const guestContext = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}` });
  const guest = await guestContext.newPage();
  await guest.goto(`/guest/${table.public_token}`);
  await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
  await guest.getByRole("button", { name: /Hambúrguer configurável/ }).click();
  await expect(guest.getByRole("button", { name: /^Adicionar ·/ })).toBeDisabled();
  await guest.getByLabel(/Duplo/).check(); await guest.getByLabel("Ao ponto").check();
  await guest.getByLabel(/Bacon/).check(); await guest.getByLabel(/Queijo/).check();
  await guest.getByLabel("Pedido especial (opcional)").fill("Molho separado");
  await expect(guest.getByRole("button", { name: /^Adicionar ·/ })).toContainText("28,00");
  await guest.getByRole("button", { name: /^Adicionar ·/ }).click();
  await guest.getByRole("button", { name: /^Enviar ·/ }).click();
  await expect(guest.getByText("Confirmado", { exact: true })).toBeVisible();
  await page.goto("/kitchen");
  await expect(page.getByText("+ Bacon", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Observação: Molho separado").first()).toBeVisible();
  await page.getByRole("button", { name: "Indisponibilizar Bacon", exact: true }).click();
  await expect(page.getByRole("button", { name: "Reativar Bacon", exact: true })).toBeVisible();
  await guest.getByRole("button", { name: /Hambúrguer configurável/ }).click();
  await expect(guest.getByLabel(/Bacon/)).toBeDisabled({ timeout: 10000 });
  expect((await api(page, `/api/pos/tabs/${tab.id}/`)).orders[0].items[0].customization_snapshot).toEqual(first.items[0].customization_snapshot);
  await guestContext.close();
});
