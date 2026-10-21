import { openAttendanceTable } from "./attendance-actions";
import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

async function setup(page: Page) {
  await fixture(page, "normal", true);
  let failed = false;
  const orders = [{ id: "order-actual-uuid", status: "CONFIRMED", confirmed_at: "2026-10-16T19:00:00Z", items: [
    { id: "historical-bar", product_id: "fries", product_name: "Fritas", quantity: 2, state: "NEW", fulfillment_station_snapshot: "BAR" },
    { id: "historical-kitchen", product_id: "omelette", product_name: "Omelete", quantity: 1, state: "PREPARING", fulfillment_station_snapshot: "KITCHEN" },
  ] }];
  const tab = { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 2400, version: 2, orders, payments: [] };
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { table_service_enabled: true, results: [
    { id: "table-test", label: "08", status: "OCCUPIED", active_occupancy: { id: "visit", generation: 1, tabs: [tab] } },
  ] } }));
  await page.route(/\/api\/attendance\/tabs\/tab-test\/(\?.*)?$/, route => route.fulfill(failed
    ? { status: 503, json: { code: "READ_FAILED", message: "Leitura indisponível" } }
    : { json: tab }));
  const open = async () => {
    await openAttendanceTable(page, "table-test");
    await page.locator('button[data-tab-id="tab-test"]').click();
    await expect(page.getByRole("region", { name: "Comanda selecionada", exact: true })).toBeVisible();
  };
  await page.goto("/attendance"); await open();
  return { orders, open, fail: () => { failed = true; }, recover: () => { failed = false; } };
}

for (const width of [360, 390, 430, 1280]) test(`canonical order confirmation persists across reload at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  const { open } = await setup(page);
  const status = page.getByRole("region", { name: "Último pedido confirmado" });
  await expect(status.getByText("Pedido #order-actual-uuid confirmado", { exact: true })).toBeVisible();
  await expect(status.getByText("2× Fritas · 1× Omelete", { exact: true })).toBeVisible();
  await expect(status.getByText("Bar · Na fila", { exact: true })).toBeVisible();
  await expect(status.getByText("Cozinha · Em preparo", { exact: true })).toBeVisible();
  await expect(status.getByText(/Pronto/)).toHaveCount(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `visual-artifacts/033/order-status-${width}.png`, fullPage: true });
  await page.reload(); await open();
  await expect(status).toContainText("#order-actual-uuid");
});

test("canonical refresh updates production, failed read stays explicitly stale", async ({ page }) => {
  const state = await setup(page);
  const status = page.getByRole("region", { name: "Último pedido confirmado" });
  state.orders[0].items[0].state = "READY";
  await page.clock.runFor(15000);
  await expect(status.getByText("Bar · Pronto", { exact: true })).toBeVisible();
  state.fail(); await page.clock.runFor(15000);
  await expect(status.getByText(/Estado desatualizado/)).toBeVisible();
  await expect(status).toContainText("#order-actual-uuid");
  state.recover();
  state.orders[0].items[0].fulfillment_station_snapshot = "";
  state.orders[0].items[0].state = "FUTURE_STATE";
  await page.clock.runFor(15000);
  await expect(status.getByText("Destino não informado · Estado não informado", { exact: true })).toBeVisible();
  await expect(status.getByText(/Estado desatualizado/)).toHaveCount(0);
});

test("unconfirmed read models never show canonical order confirmation", async ({ page }) => {
  const { orders } = await setup(page);
  orders[0].status = "PENDING";
  await page.clock.runFor(15000);
  await expect(page.getByRole("region", { name: "Último pedido confirmado" })).toHaveCount(0);
});

test('old A poll cannot replace new A after A-B-A',async({page})=>{
 await fixture(page,'normal',true);
 const order=(name:string,state:string)=>({id:name,status:'CONFIRMED',confirmed_at:'2026-10-16T00:00:00Z',items:[{id:name,product_name:name,quantity:1,state,fulfillment_station_snapshot:'BAR'}]});
 const a={id:'tab-a',display_label:'Alpha',state:'OPEN',exposure_cents:100,version:1,orders:[order('alpha','NEW')],payments:[]};
 const b={...a,id:'tab-b',display_label:'Bravo',orders:[order('bravo','NEW')]};
 const table={id:'table-test',label:'08',status:'OCCUPIED',active_occupancy:{id:'visit',generation:1,tabs:[a,b]}};
 await page.route('**/api/attendance/hospitality/tables/',r=>r.fulfill({json:{table_service_enabled:true,results:[table]}}));
 let hold=false,held: import('@playwright/test').Route; let signal:()=>void; const captured=new Promise<void>(r=>signal=r);
 await page.route(/\/api\/attendance\/tabs\/tab-a\/(\?.*)?$/,async r=>{ if(hold&&!r.request().url().includes('?')){hold=false;held=r;signal();}else await r.fulfill({json:a}); });
 await page.route(/\/api\/attendance\/tabs\/tab-b\/(\?.*)?$/,r=>r.fulfill({json:b}));
 await page.goto('/attendance');
 await openAttendanceTable(page, "table-test");
 await page.locator('button[data-tab-id="tab-a"]').click();
 await expect(page.getByRole('region',{name:'Último pedido confirmado'})).toContainText('Bar · Na fila');
 hold=true;await page.clock.runFor(15000);await captured;
 const old=structuredClone(a);
 await page.keyboard.press('Escape');
 await page.locator('button[data-tab-id="tab-b"]').click();
 await expect(page.getByRole('region',{name:'Último pedido confirmado'})).toContainText('#bravo');
 await page.keyboard.press('Escape');
 a.orders[0].items[0].state='READY';a.version=2;
 await page.locator('button[data-tab-id="tab-a"]').click();
 const status=page.getByRole('region',{name:'Último pedido confirmado'});
 await expect(status).toContainText('Bar · Pronto');
 await held!.fulfill({json:old});
 await page.clock.runFor(100);
 await expect(status).toContainText('Bar · Pronto');
});

test('poll started during same A selection cannot override canonical selection',async({page})=>{
 await fixture(page,'normal',true);
 const a={id:'tab-a',display_label:'Alpha',state:'OPEN',exposure_cents:100,version:1,orders:[{id:'alpha',status:'CONFIRMED',confirmed_at:'2026-10-16T00:00:00Z',items:[{id:'alpha',product_name:'alpha',quantity:1,state:'NEW',fulfillment_station_snapshot:'BAR'}]}],payments:[]};
 const table={id:'table-test',label:'08',status:'OCCUPIED',active_occupancy:{id:'visit',generation:1,tabs:[a]}};
 await page.route('**/api/attendance/hospitality/tables/',r=>r.fulfill({json:{table_service_enabled:true,results:[table]}}));
 let holdSelection=false,selection: import('@playwright/test').Route,poll: import('@playwright/test').Route;let selSignal:()=>void,pollSignal:()=>void;
 const selCaptured=new Promise<void>(r=>selSignal=r),pollCaptured=new Promise<void>(r=>pollSignal=r);
 await page.route(/\/api\/attendance\/tabs\/tab-a\/(\?.*)?$/,async r=>{
  if(holdSelection&&r.request().url().includes('?')){selection=r;selSignal();}
  else if(holdSelection&&!r.request().url().includes('?')){poll=r;pollSignal();}
  else await r.fulfill({json:a});
 });
 await page.goto('/attendance');await openAttendanceTable(page, "table-test");await page.locator('button[data-tab-id="tab-a"]').click();
 const status=page.getByRole('region',{name:'Último pedido confirmado'});await expect(status).toContainText('Bar · Na fila');
 await page.keyboard.press('Escape');holdSelection=true;
 await page.locator('button[data-tab-id="tab-a"]').click();await selCaptured;
 await page.clock.runFor(15000);await pollCaptured;
 const old=structuredClone(a);a.orders[0].items[0].state='READY';a.version=2;
 await selection!.fulfill({json:a});await expect(status).toContainText('Bar · Pronto');
 holdSelection=false;await poll!.fulfill({json:old});await page.clock.runFor(100);
 await expect(status).toContainText('Bar · Pronto');
});
