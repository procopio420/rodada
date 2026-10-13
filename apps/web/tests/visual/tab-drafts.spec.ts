import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, products } from "./fixtures";

async function setup(page: Page) {
  await fixture(page, "normal", true);
  const tabs = ["A", "B"].map(name => ({ id: `tab-${name}`, display_label: `Comanda ${name}`, state: "OPEN", version: 1,
    exposure_cents: 0, payable_cents: 0, charges_cents: 0, payments_cents: 0, orders: [] as { id: string; items: unknown[] }[], payments: [], refund_required_corrections: [] }));
  await page.route(/\/api\/(attendance|pos)\/tabs\/(\?.*)?$/, route => {
    if (route.request().method() === "POST") {
      const created = { ...tabs[0], id: "tab-C", display_label: "Comanda C" }; tabs.push(created);
      return route.fulfill({ status: 201, json: created });
    }
    return route.fulfill({ json: { results: tabs, next_offset: null } });
  });
  await page.route(/\/api\/(attendance|pos)\/tabs\/tab-[ABC]\/$/, route => route.fulfill({ json: tabs.find(t => route.request().url().includes(t.id)) }));
  await page.route(/\/api\/pos\/tabs\/tab-[ABC]\/pricing\/$/, route => route.fulfill({ json: { version: 1, policy: { service_basis_points: 0 }, history: [], charges: [] } }));
  return tabs;
}
async function open(page: Page, surface: "attendance" | "pos") {
  await page.goto(`/${surface}`);
  if (surface === "attendance") await page.getByRole("button", { name: "Contas", exact: true }).click();
  await page.getByRole("button", { name: /^Comanda A ·/ }).click();
}

for (const surface of ["attendance", "pos"] as const) for (const width of [360, 390, 430]) test(`${surface} drafts A B A new tab and deliberate discard at ${width}`, async ({ page }) => {
  const tabs = await setup(page); await page.setViewportSize({ width, height: 900 }); await open(page, surface);
  const product = page.getByRole("button", { name: /^Fritas/ });
  await product.click();
  await page.getByRole("button", { name: /^Comanda B ·/ }).click();
  await expect(page.getByText("1× Fritas", { exact: true })).toHaveCount(0);
  await product.click();
  await page.getByRole("button", { name: /^Comanda A ·/ }).click();
  await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
  const heading = page.getByRole("heading", { name: "Comanda A", exact: true });
  await expect(heading).toBeFocused();
  await page.getByRole("button", { name: /^Comanda A ·/ }).click();
  await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Fechar comanda", exact: true })).toBeDisabled();
  await page.getByLabel("Apelido da comanda (opcional)").fill("Comanda C");
  await page.getByRole("button", { name: "Abrir", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Comanda C", exact: true })).toBeVisible();
  await expect(page.getByText("1× Fritas", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: /^Comanda A ·/ }).click();
  await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
  const discard = page.getByRole("button", { name: "Descartar rascunho", exact: true });
  await discard.click(); const dialog = page.getByRole("dialog", { name: "Descartar rascunho?" });
  await expect(dialog).toContainText("Comanda A"); await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/t04-discard-${surface}-${width}.png`, fullPage: true });
  await dialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(discard).toBeFocused(); await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
  await discard.click(); await dialog.getByRole("button", { name: "Confirmar descarte", exact: true }).click();
  await expect(page.getByText("1× Fritas", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: /^Comanda B ·/ }).click();
  await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible(); await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/t04-draft-${surface}-${width}.png`, fullPage: true });
});

const custom = { ...products[0], price_cents: 1000,
  variants: ["Pequena", "Grande"].map((name, index) => ({ id: `variant-${index}`, name, price_cents: 1000 + index * 500, is_default: index === 0, active: true, availability: "AVAILABLE", version: 1 })),
  modifier_groups: [{ id: "extras", name: "Extras", selection_mode: "MULTI", min_selections: 0, max_selections: 1, active: true, version: 1,
    options: [{ id: "extra", name: "Molho extra", price_delta_cents: 200, active: true, availability: "AVAILABLE", semantic_kind: "ADD", default_selected: false, version: 1 }] }] };

for (const width of [360, 390, 430]) test(`Distinct configurations retain quantities and confirm only the original destination at ${width}`, async ({ page }) => {
  const tabs = await setup(page); await page.setViewportSize({ width, height: 900 });
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [custom] } }));
  await open(page, "attendance");
  for (const large of [false, true]) {
    await page.getByRole("button", { name: /^Fritas/ }).click();
    const dialog = page.getByRole("dialog", { name: "Personalizar Fritas" });
    if (large) { await dialog.getByLabel(/Grande/).check(); await dialog.getByLabel(/Molho extra/).check(); }
    await dialog.getByLabel("Pedido especial (opcional)").fill(large ? "Molho separado" : "Sem sal");
    await dialog.getByRole("button", { name: /^Adicionar ·/ }).click();
  }
  const draft = page.getByRole("region", { name: "Pedido atual" });
  await draft.locator("article").first().getByRole("button", { name: /^Aumentar/ }).click();
  await page.getByRole("button", { name: /^Comanda B ·/ }).click();
  await expect(draft.locator("article")).toHaveCount(0);
  await page.getByRole("button", { name: /^Fritas/ }).click();
  await page.getByRole("dialog").getByLabel("Pedido especial (opcional)").fill("Rascunho B");
  await page.getByRole("dialog").getByRole("button", { name: /^Adicionar ·/ }).click();
  await page.getByRole("button", { name: /^Comanda A ·/ }).click();
  await expect(draft.locator("article")).toHaveCount(2);
  await expect(draft.getByText("Observação: Sem sal")).toBeVisible();
  await expect(draft.getByText("Observação: Molho separado")).toBeVisible();
  const attempts: { lines: unknown[] }[] = [];
  await page.route("**/api/attendance/tabs/tab-A/orders/confirm/", route => {
    attempts.push(route.request().postDataJSON()); tabs[0].orders = [{ id: "order-A", items: [] }]; return route.fulfill({ status: 201, json: { id: "order-A", tab_id: "tab-A" } });
  });
  await draft.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(attempts[0].lines).toEqual([
    { product_id: custom.id, quantity: 2, variant_id: "variant-0", modifier_option_ids: [], special_instructions: "Sem sal" },
    { product_id: custom.id, quantity: 1, variant_id: "variant-1", modifier_option_ids: ["extra"], special_instructions: "Molho separado" },
  ]);
  await expect(draft.locator("article")).toHaveCount(0);
  await page.getByRole("button", { name: /^Comanda B ·/ }).click();
  await expect(draft.getByText("Observação: Rascunho B")).toBeVisible();
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [{ ...custom, availability: "UNAVAILABLE" }] } }));
  await page.clock.runFor(15000);
  await expect(draft.getByText("Item indisponível. Retire ou revise o pedido.")).toBeVisible();
  await expect(draft.getByRole("button", { name: /^Confirmar pedido/ })).toBeDisabled();
});

test("Failed tab read preserves A and selection in flight cannot mutate or switch", async ({ page }) => {
  const tabs = await setup(page); await open(page, "attendance"); await page.getByRole("button", { name: /^Fritas/ }).click();
  let release!: () => void; const held = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/attendance/tabs/tab-B/", async route => { await held; await route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Comanda indisponível" } }); });
  await page.getByRole("button", { name: /^Comanda B ·/ }).click();
  await expect(page.getByRole("button", { name: /^Comanda A ·/ })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Descartar rascunho", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: /^Confirmar pedido/ })).toBeDisabled();
  release(); await expect(page.getByText("Comanda indisponível", { exact: true })).toBeVisible();
  await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Comanda A", exact: true })).toBeVisible();
});

test("Ambiguous order cannot switch, collapse or discard its original draft", async ({ page }) => {
  const tabs = await setup(page); await open(page, "attendance"); await page.getByRole("button", { name: /^Fritas/ }).click();
  const bodies: string[] = [];
  await page.route("**/api/attendance/tabs/tab-A/orders/confirm/", route => { bodies.push(route.request().postData()!); tabs[0].orders = [{ id: "same-order", items: [] }]; return bodies.length === 1 ? route.abort() : route.fulfill({ status: 200, json: { id: "same-order", tab_id: "tab-A" } }); });
  await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
  const verify = page.getByRole("button", { name: "Verificar mesmo pedido" }); await expect(verify).toBeEnabled();
  await expect(page.getByRole("button", { name: /^Comanda B ·/ })).toBeDisabled();
  await expect(page.getByRole("button", { name: /Comanda selecionada Comanda A/ })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Descartar rascunho", exact: true })).toBeDisabled();
  await verify.click(); await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  expect(bodies[1]).toBe(bodies[0]);
});
