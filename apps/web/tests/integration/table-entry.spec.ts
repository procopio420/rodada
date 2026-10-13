import { expect, test } from "./test";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

async function read(page: import("@playwright/test").Page, path: string) {
 return page.evaluate(async path => { const r = await fetch(`/api/attendance/${path}`); if (!r.ok) throw new Error(String(r.status)); return r.json(); }, path);
}
test("real table entry opens an older Tab and confirms only its draft at mobile widths", async ({ page }) => {
 test.setTimeout(120000);
 const python = process.env.RODADA_TEST_PYTHON!;
 execFileSync(python, ["-c", `import os
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.ordering.models import Tab
from modules.hospitality.models import Table,TableOccupancy,TabOccupancyAssignment
from modules.venue.models import Venue
v=Venue.objects.get(slug='web-e2e')
assert not Tab.objects.filter(venue=v).exists()
a=Tab.objects.create(venue=v,display_label='Table entry A')
b=Tab.objects.create(venue=v,display_label='Table entry B')
Tab.objects.bulk_create([Tab(venue=v,display_label=f'Unrelated entry {i}') for i in range(201)])
t=Table.objects.create(venue=v,label='Pátio 24',status='OCCUPIED')
o=TableOccupancy.objects.create(table=t,generation=1)
TabOccupancyAssignment.objects.create(occupancy=o,tab=a)
TabOccupancyAssignment.objects.create(occupancy=o,tab=b)
`], { cwd: resolve("../api"), env: process.env });
 await page.goto("/attendance"); await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
 await page.getByRole("button", { name: "Entrar", exact: true }).click(); await page.getByRole("button", { name: "Mesas", exact: true }).click();
 const table = (await read(page,"hospitality/tables/")).results[0], tabs = table.active_occupancy.tabs;
 const a = tabs.find((t: {display_label:string}) => t.display_label === "Table entry A"), b = tabs.find((t: {display_label:string}) => t.display_label === "Table entry B");
 const firstPage = (await read(page,"tabs/")).results; expect(firstPage.some((t: {id:string}) => t.id === a.id || t.id === b.id)).toBe(false);
 await page.getByLabel("Buscar mesa").fill("mesa patio 24");
 for (const [index,width] of [360,390,430].entries()) {
  await page.setViewportSize({width,height:900});
  await page.getByRole("button", { name: `Abrir comanda Table entry A · ID ${a.id}`, exact:true }).click();
  await expect(page.getByRole("heading", {name:"Table entry A",exact:true})).toBeFocused();
  await page.getByLabel("Buscar item no cardápio").fill("Kitchen E2E item"); await page.getByRole("button", {name:/^Kitchen E2E item/}).click();
  await page.getByRole("button", {name:"Voltar à mesa Pátio 24",exact:true}).click();
  await expect(page.getByRole("heading", {name:"Mesa Pátio 24",exact:true})).toBeFocused(); await expect(page.getByLabel("Buscar mesa")).toHaveValue("mesa patio 24");
  await page.getByRole("button", {name:`Abrir comanda Table entry B · ID ${b.id}`,exact:true}).click();
  await expect(page.getByText(`${index+1}× Kitchen E2E item`, {exact:true})).toHaveCount(0);
  await page.getByRole("button", {name:"Voltar à mesa Pátio 24",exact:true}).click();
  await expect(page.getByRole("button", {name:`Abrir comanda Table entry A · ID ${a.id}`,exact:true})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
 }
 await page.getByRole("button", {name:`Abrir comanda Table entry A · ID ${a.id}`,exact:true}).click();
 const before = await read(page,`tabs/${a.id}/`); expect(before.orders).toHaveLength(0); expect(before.payments).toHaveLength(0); expect(before.version).toBe(1);
 await expect(page.getByText("3× Kitchen E2E item", {exact:true})).toBeVisible(); const confirmation = page.waitForResponse(response => new URL(response.url()).pathname.replace(/\/$/, "") === `/api/attendance/tabs/${a.id}/orders/confirm` && (response.status() < 300 || response.status() >= 400) && response.request().method() === "POST");
 let readbackStart = Infinity;
 const readback = page.waitForResponse(response => new URL(response.url()).pathname.replace(/\/$/, "") === `/api/attendance/tabs/${a.id}` && (response.status() < 300 || response.status() >= 400) && response.request().method() === "GET").then(response => { readbackStart = response.request().timing().startTime; return response; });
 const listRefresh = page.waitForResponse(response => new URL(response.url()).pathname.replace(/\/$/, "") === "/api/attendance/tabs" && response.request().timing().startTime >= readbackStart && (response.status() < 300 || response.status() >= 400) && response.request().method() === "GET");
 await page.getByRole("button", {name:/^Confirmar pedido/}).click();
 expect((await confirmation).status()).toBe(201); expect((await readback).status()).toBe(200); expect((await listRefresh).status()).toBe(200);
 await expect(page.getByText("Pedido confirmado.",{exact:true})).toBeVisible();
 const after = await read(page,`tabs/${a.id}/`), untouched = await read(page,`tabs/${b.id}/`);
 expect(after.orders).toHaveLength(1); expect(after.orders[0].items[0].quantity).toBe(3); expect(after.charges_cents).toBe(3000); expect(after.payments).toHaveLength(0);
 expect(untouched.orders).toHaveLength(0); expect(untouched.exposure_cents).toBe(0); expect(untouched.payments).toHaveLength(0);
 const finalTable = (await read(page,"hospitality/tables/")).results[0]; expect(finalTable.active_occupancy.id).toBe(table.active_occupancy.id); expect(finalTable.access_generation).toBe(table.access_generation); expect(finalTable.active_occupancy.tabs).toEqual(table.active_occupancy.tabs);
});
