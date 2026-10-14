import { expect, test, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { fixture, layoutAndA11y, products } from "./fixtures";

const source = JSON.parse(execFileSync(process.env.RODADA_REFERENCE_PYTHON ?? "python3", ["-c", "import csv,json,sys; print(json.dumps(list(csv.DictReader(open(sys.argv[1],encoding='utf-8'))),ensure_ascii=True))",
  resolve("../api/modules/catalog/data/aderlan-menu-2026-10-09.csv")]).toString()) as { name: string; category: string; price_brl: string; station: string }[];
const menu = source.map((row, index) => ({ id: `menu-test-${index}`, name: row.name, category: row.category,
  price_cents: Number(row.price_brl.replace(/\D/g, "")), fulfillment_station: row.station, available: true }));

async function setup(page: Page, empty = false) {
  await fixture(page, "normal", true);
  const catalog = empty ? [] : [...menu.map(product => ({ ...product })), ...products.map(product => ({ ...product }))];
  const context = { session_scope: { venue_id: "venue-test", session_id: "catalog-session", table_id: "table-test", occupancy_id: "visit-test", generation: 1 },
    table: { label: "24" }, occupancy_active: true, can_start_occupancy: false, guest_session_token: "catalog-test-token",
    guest_policy: { emergency_blocked: false, table_ordering_enabled: true },
    tab: { id: "tab-test", display_label: "Minha comanda", state: "OPEN", exposure_cents: 0, charges_cents: 0, payments_cents: 0,
      consumption_blocked: false, remaining_capacity_cents: 1000000, orders: [] } };
  const attempts: string[] = []; let revoked = false;
  await page.route("**/api/guest/qr/resolve/", route => route.fulfill({ json: context }));
  await page.route("**/api/guest/context/", route => route.fulfill({ status: revoked ? 403 : 200, json: revoked ? { code: "GUEST_SESSION_REVOKED" } : context }));
  await page.route("**/api/guest/catalog/", route => route.fulfill({ json: { results: catalog } }));
  await page.route("**/api/guest/orders/confirm/", route => { attempts.push(route.request().postData()!); return route.abort(); });
  await page.goto("/guest/test-qr");
  return { context, catalog, attempts, revoke: () => { revoked = true; } };
}
for (const width of [360, 390, 430]) test(`Guest discovery with 146 products preserves draft and pending intent ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); const state = await setup(page);
  expect(source).toHaveLength(143); expect(state.catalog).toHaveLength(146);
  await expect(page.locator(".guestProduct")).toHaveCount(146);
  const categories = page.getByRole("navigation", { name: "Categorias do cardápio" });
  await categories.getByRole("button", { name: /^Cervejas \(/ }).click();
  const count = await page.locator(".guestProduct").count(); expect(count).toBeGreaterThan(0); expect(count).toBeLessThan(146);
  const search = page.getByLabel("Buscar item no cardápio"); await search.fill("  CAMARAO COM CATUPIRY  ");
  await expect(page.locator(".guestProduct")).toHaveCount(1);
  await expect(page.getByText("Busca em todas as categorias · 1 itens", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /^Camarão com Catupiry/ }).click();
  await search.fill("FRITAS"); await page.getByRole("button", { name: /^Fritas / }).dblclick();
  const draft = page.getByRole("region", { name: "Pedido atual" }); await expect(draft.getByText("2× Fritas", { exact: true })).toBeVisible();
  await draft.getByRole("button", { name: "Editar" }).last().click();
  await page.getByLabel("Pedido especial (opcional)").fill("Sem sal"); await page.getByRole("button", { name: /^Adicionar ·/ }).click();
  await search.fill("not-found-test"); await expect(page.getByText(/^Nenhum item encontrado/)).toBeVisible();
  await search.fill(""); await expect(page.locator(".guestProduct")).toHaveCount(count);
  await categories.getByRole("button", { name: /^Todos \(/ }).click(); await expect(page.locator(".guestProduct")).toHaveCount(146);
  await search.fill("FRITAS");
  await page.getByRole("button", { name: /^Pedido atual · 3 itens/ }).click(); await expect(draft).toBeFocused();
  await expect(draft.getByText("Observação: Sem sal")).toBeVisible(); expect(state.attempts).toHaveLength(0);
  await layoutAndA11y(page); await page.screenshot({ path: `test-results/guest-catalog-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: /^Enviar ·/ }).click(); await expect.poll(() => state.attempts.length).toBe(1);
  await search.fill("omelete"); await expect(page.getByRole("button", { name: /^Omelete / })).toBeDisabled();
  await page.getByRole("button", { name: "Verificar mesmo pedido" }).click(); await expect.poll(() => state.attempts.length).toBe(2);
  expect(state.attempts[1]).toBe(state.attempts[0]); expect(JSON.parse(state.attempts[0]).lines).toHaveLength(2);
});

for (const mode of ["unavailable", "table", "emergency", "revoked"]) test(`Guest filtered catalog respects ${mode}`, async ({ page }) => {
  const state = await setup(page); const search = page.getByLabel("Buscar item no cardápio");
  await search.fill("fritas"); await page.getByRole("button", { name: /^Fritas / }).click();
  if (mode === "unavailable") state.catalog.find(p => p.id === "fries")!.available = false;
  if (mode === "table") state.context.guest_policy.table_ordering_enabled = false;
  if (mode === "emergency") state.context.guest_policy.emergency_blocked = true;
  if (mode === "revoked") state.revoke();
  await page.getByRole("button", { name: "Atualizar comanda" }).click();
  if (mode === "revoked") await expect(page.getByRole("heading", { name: "Não foi possível abrir o pedido" })).toBeVisible();
  else {
    await expect(page.getByRole("button", { name: /^Fritas / })).toBeDisabled();
    await expect(page.getByRole("button", { name: /^Enviar ·/ })).toBeDisabled();
    await expect(page.getByRole("region", { name: "Pedido atual" }).getByText("1× Fritas", { exact: true })).toBeVisible();
  }
  expect(state.attempts).toHaveLength(0);
});

test("Guest category removed on refresh falls back to Todos and empty catalog stays explicit", async ({ page }) => {
  const state = await setup(page);
  await page.getByRole("navigation", { name: "Categorias do cardápio" }).getByRole("button", { name: /^Cervejas \(/ }).click();
  state.catalog.splice(0, state.catalog.length, ...products);
  await page.getByRole("button", { name: "Atualizar comanda" }).click();
  await expect(page.getByRole("button", { name: "Todos (3)", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".guestProduct")).toHaveCount(3);
  state.catalog.splice(0); await page.getByRole("button", { name: "Atualizar comanda" }).click();
  await expect(page.getByText("Cardápio vazio. Peça ajuda à equipe.", { exact: true })).toBeVisible();
  await expect(page.locator(".guestProduct")).toHaveCount(0);
});
