import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
const ids = ["11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"];
async function setup(page: Page) {
 await fixture(page, "normal", true);
 const tabs = ids.map(id => ({ id, display_label: "Mesmo apelido", state: "OPEN", version: 1, exposure_cents: 0, payable_cents: 0, charges_cents: 0, payments_cents: 0, payments: [], orders: [], refund_required_corrections: [] }));
 await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { results: [
  { id: "table-context", label: "Pátio 24", status: "OCCUPIED", active_occupancy: { id: "occupancy-context", tabs } }, { id: "other-table", label: "25", status: "AVAILABLE" }
 ] } }));
 // The target Tabs are deliberately absent from the first page of Contas.
 await page.goto("/attendance"); await page.getByRole("button", { name: "Mesas", exact: true }).click();
 await stable(page); await page.getByLabel("Buscar mesa").fill("mesa patio 24"); await expect(page.getByRole("heading", { name: "Mesa 25", exact: true })).toHaveCount(0);
 return tabs;
}
for (const width of [360,390,430]) test(`table entry and return preserve isolated drafts and focus at ${width}`, async ({ page }) => {
 await page.setViewportSize({ width, height: 900 }); const tabs = await setup(page);
 const contexts: URLSearchParams[] = [];
 await page.route(/\/api\/attendance\/tabs\/[0-9a-f-]+\/(\?.*)?$/, route => {
  const url = new URL(route.request().url()); contexts.push(url.searchParams);
  return route.fulfill({ json: tabs.find(tab => url.pathname.includes(tab.id)) });
 });
 const open = (id: string) => page.getByRole("button", { name: `Abrir comanda Mesmo apelido · ID ${id}`, exact: true });
 await layoutAndA11y(page); await open(ids[0]).click();
 await expect(page.getByRole("heading", { name: "Mesmo apelido", exact: true })).toBeFocused();
 await page.getByRole("button", { name: /^Fritas/ }).click();
 await page.getByRole("button", { name: "Voltar à mesa Pátio 24", exact: true }).click();
 await expect(page.getByRole("heading", { name: "Mesa Pátio 24", exact: true })).toBeFocused(); await expect(page.getByLabel("Buscar mesa")).toHaveValue("mesa patio 24");
 await open(ids[1]).click(); await expect(page.getByText("1× Fritas", { exact: true })).toHaveCount(0);
 await page.getByRole("button", { name: "Voltar à mesa Pátio 24", exact: true }).click(); await open(ids[0]).click();
 await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
 expect(contexts).toHaveLength(3); for (const params of contexts) { expect(params.get("occupancy_id")).toBe("occupancy-context"); expect(params.get("table_id")).toBe("table-context"); }
 await layoutAndA11y(page);
});
for (const width of [360,390,430]) test(`table conflict does not replace the existing destination at ${width}`, async ({ page }) => {
 await page.setViewportSize({ width, height: 900 }); const tabs = await setup(page); let fail = false;
 await page.route(/\/api\/attendance\/tabs\/[0-9a-f-]+\/(\?.*)?$/, route => fail ? route.fulfill({ status: 409, json: { code: "TABLE_CONTEXT_CHANGED", message: "O vínculo da comanda com a mesa mudou. Atualize as mesas." } }) : route.fulfill({ json: tabs[0] }));
 const open = page.getByRole("button", { name: `Abrir comanda Mesmo apelido · ID ${ids[0]}`, exact: true });
 await open.click(); await page.getByRole("button", { name: /^Fritas/ }).click(); await page.getByRole("button", { name: "Voltar à mesa Pátio 24", exact: true }).click();
 fail = true; await open.click(); await expect(page.getByRole("alert").filter({ hasText: "O vínculo" })).toBeVisible();
 await expect(page.getByLabel("Buscar mesa")).toBeVisible(); await page.getByRole("button", { name: "Contas", exact: true }).click();
 await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible(); await expect(page.getByRole("heading", { name: "Mesmo apelido", exact: true })).toBeVisible();
});
test("ambiguous order blocks return to the originating table", async ({ page }) => {
 const tabs = await setup(page);
 await page.route(/\/api\/attendance\/tabs\/[0-9a-f-]+\/(\?.*)?$/, route => route.fulfill({ json: tabs[0] }));
 await page.route(`**/api/attendance/tabs/${ids[0]}/orders/confirm/`, route => route.abort());
 await page.getByRole("button", { name: `Abrir comanda Mesmo apelido · ID ${ids[0]}`, exact: true }).click(); await page.getByRole("button", { name: /^Fritas/ }).click();
 await page.getByRole("button", { name: /^Confirmar pedido/ }).click();
 await expect(page.getByRole("button", { name: "Voltar à mesa Pátio 24", exact: true })).toBeDisabled(); await expect(page.getByRole("button", { name: "Mesas", exact: true })).toBeDisabled();
});

test("table entry is serialized and blocks navigation while reading", async ({ page }) => {
 const tabs = await setup(page); let reads = 0; let release: (() => void) | undefined;
 await page.route(/\/api\/attendance\/tabs\/[0-9a-f-]+\/(\?.*)?$/, async route => {
  reads++; await new Promise<void>(resolve => { release = resolve; }); await route.fulfill({json:tabs[0]});
 });
 await page.getByRole("button", {name:`Abrir comanda Mesmo apelido · ID ${ids[0]}`,exact:true}).evaluate(button => { (button as HTMLButtonElement).click(); (button as HTMLButtonElement).click(); });
 await expect.poll(() => reads).toBe(1);
 await expect(page.getByRole("button", {name:"Contas",exact:true})).toBeDisabled(); await expect(page.getByRole("button", {name:"Sair",exact:true})).toBeDisabled();
 await expect(page.getByRole("button", {name:`Abrir comanda Mesmo apelido · ID ${ids[1]}`,exact:true})).toBeDisabled();
 release!(); await expect(page.getByRole("heading", {name:"Mesmo apelido",exact:true})).toBeFocused(); expect(reads).toBe(1);
});
