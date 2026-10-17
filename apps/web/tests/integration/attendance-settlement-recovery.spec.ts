import { test, expect, type Page } from "./fixtures";

// Independent regression authorship: review_e04_final, base 3fc2ac55.
// Domain effects use real Attendance BFF/Django/PostgreSQL; routes inject transport faults only.
const key = "rodada.intent.pos-cash.v1";
type Tab = { id: string; state: string; exposure_cents: number; version: number; payments: { id: string }[] };
type Product = { id: string; name: string; price_cents: number };
async function api<T = Tab>(page: Page, path: string, body?: unknown): Promise<T> {
  return page.evaluate(async ({path, body}) => {
    const r = await fetch(`/api/attendance/${path}`, body === undefined ? {} : {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
    const data = await r.json(); if (!r.ok) throw new Error(`${r.status} ${JSON.stringify(data)}`); return data as T;
  }, {path, body});
}
async function setup(page: Page) {
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", {exact:true}).fill("test-manager");
  await page.getByLabel("PIN", {exact:true}).fill("2468");
  await page.getByRole("button", {name:"Entrar", exact:true}).click();
  await expect(page.getByRole("button", {name:"Mesas", exact:true})).toBeVisible();
  const point = (await api<{results: {id: string; active_shift: unknown}[]}>(page,"cash/points/")).results[0];
  if (!point.active_shift) await page.evaluate(async id => {
    const r = await fetch("/api/pos/cash/shifts/", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({cash_point_id:id,opening_float_cents:0,business_date:"2026-10-17",idempotency_key:crypto.randomUUID()})});
    if(!r.ok) throw new Error(`shift ${r.status}`);
  },point.id);
  const product = (await api<{results: Product[]}>(page,"catalog/products/")).results.find(p=>p.name==="Kitchen E2E item");
  if (!product) throw new Error("Canonical fixture product missing");
  const tab = await api(page,"tabs/",{display_label:`Independent recovery ${crypto.randomUUID()}`});
  await api(page,`tabs/${tab.id}/orders/confirm/`,{idempotency_key:crypto.randomUUID(),lines:[{product_id:product.id,quantity:1}]});
  const bill = await api(page,`tabs/${tab.id}/`);
  const auth = await page.evaluate(async ()=>(await fetch("/api/auth/me")).json());
  const intent = {schema:2,api_root:"/api/attendance",phase:"PAYMENT_PENDING",payment_id:null as string|null,close_requested:true,
    venue:auth.venue.id,staff:auth.staff.id,session:auth.session.id,tab:tab.id,captured_at:new Date().toISOString(),
    payload:{amount_cents:bill.exposure_cents,expected_version:bill.version,method:"CASH",cash_point_id:point.id,idempotency_key:crypto.randomUUID(),originating_session_id:auth.session.id}};
  return {tab,product,intent};
}
async function mountRecovery(page: Page, intent: unknown) {
  await page.evaluate(({key,intent})=>sessionStorage.setItem(key,JSON.stringify(intent)),{key,intent});
  // No Tab has been selected. Recovery must be reachable from the mounted shell.
  await page.reload();
  await expect(page.getByRole("button",{name:"Verificar mesmo recebimento"})).toBeEnabled();
}

test("Attendance pending Payment survives lost ACK and close 503/ACK loss across reload with no selection", async ({page})=>{
  const {tab,intent}=await setup(page); const bodies:string[]=[]; let closes=0;
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/payments/?$`),async route=>{
    bodies.push(route.request().postData()!);
    const r=await route.fetch({url:route.request().url().replace(/\/$/,""),headers:await route.request().allHeaders()});
    expect(r.status()).toBe(201); if(bodies.length===1) await route.abort(); else await route.fulfill({response:r});
  });
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/close/?$`),async route=>{
    closes++; if(closes===1) return route.fulfill({status:503,json:{code:"UNAVAILABLE",message:"Injected close unavailable"}});
    const r=await route.fetch({url:route.request().url().replace(/\/$/,""),headers:await route.request().allHeaders()}); expect(r.status()).toBe(200); await route.abort();
  });
  await mountRecovery(page,intent);
  const verify=page.getByRole("button",{name:"Verificar mesmo recebimento"});
  await verify.click(); await expect(page.getByText(/Resultado ainda não confirmado/)).toBeVisible();
  await page.reload(); await verify.click(); await expect(page.getByText(/Injected close unavailable/)).toBeVisible();
  expect(bodies).toHaveLength(2); expect(bodies[0]).toBe(bodies[1]);
  const saved=await page.evaluate(key=>JSON.parse(sessionStorage.getItem(key)!),key);
  expect(saved.phase).toBe("PAYMENT_CONFIRMED"); expect(saved.payment_id).toBeTruthy();
  await page.reload(); await verify.click(); await expect(verify).toBeEnabled();
  expect((await api(page,`tabs/${tab.id}/`)).state).toBe("CLOSED");
  await page.reload(); await verify.click();
  await expect.poll(()=>page.evaluate(key=>sessionStorage.getItem(key),key)).toBeNull();
  const bill=await api(page,`tabs/${tab.id}/`); expect(bill.payments).toHaveLength(1); expect(bill.payments[0].id).toBe(saved.payment_id); expect(bill.exposure_cents).toBe(0);
  expect(bodies).toHaveLength(2); expect(closes).toBe(2);
});

test("Attendance confirmed Payment permits keep open after concurrent consumption and failed canonical callback",async({page})=>{
  const {tab,product,intent}=await setup(page);
  const payment=await api(page,`tabs/${tab.id}/payments/`,intent.payload);
  await api(page,`tabs/${tab.id}/orders/confirm/`,{idempotency_key:crypto.randomUUID(),lines:[{product_id:product.id,quantity:1}]});
  let mutations=0, reads=0;
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/(payments|close)/?$`),route=>{mutations++;return route.abort();});
  await mountRecovery(page,{...intent,phase:"PAYMENT_CONFIRMED",payment_id:payment.id});
  await page.getByRole("button",{name:"Verificar mesmo recebimento"}).click();
  await expect(page.getByText(/O saldo mudou/)).toBeVisible();
  // keepOpen readback succeeds; the following workspace callback readback fails.
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/?$`),async route=>{
    reads++; if(reads===2)return route.fulfill({status:503,json:{code:"UNAVAILABLE",message:"callback unavailable"}}); await route.continue();
  });
  await page.getByRole("button",{name:"Manter comanda aberta",exact:true}).click();
  await expect(page.getByText(/Recebimento registrado; verificação/)).toBeVisible();
  const saved=await page.evaluate(key=>JSON.parse(sessionStorage.getItem(key)!),key);
  expect(saved.close_requested).toBe(false); expect(saved.payment_id).toBe(payment.id);
  await page.reload(); await page.getByRole("button",{name:"Verificar mesmo recebimento"}).click();
  await expect.poll(()=>page.evaluate(key=>sessionStorage.getItem(key),key)).toBeNull();
  expect(mutations).toBe(0); const bill=await api(page,`tabs/${tab.id}/`);
  expect(bill.state).toBe("OPEN");expect(bill.exposure_cents).toBe(product.price_cents);expect(bill.payments).toHaveLength(1);
  await page.getByRole("region",{name:"Recebimento em dinheiro",exact:true}).getByRole("button",{name:/^Receber R/}).click();
  await expect(page.getByLabel("Valor recebido (R$)",{exact:true})).toBeEnabled();
});

test("Attendance preserves original pending identity when confirmed phase cannot be persisted",async({page})=>{
  const {tab,intent}=await setup(page); const bodies:string[]=[];
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/payments/?$`),async route=>{
    bodies.push(route.request().postData()!);await route.continue();
  });
  await mountRecovery(page,intent);
  await page.evaluate(key=>{
    const original=Storage.prototype.setItem;
    Storage.prototype.setItem=function(k,v){
      if(k===key && JSON.parse(v).phase==="PAYMENT_CONFIRMED")throw new DOMException("Injected storage quota", "QuotaExceededError");
      return original.call(this,k,v);
    };
  },key);
  await page.getByRole("button",{name:"Verificar mesmo recebimento"}).click();
  await expect(page.getByText(/Resultado ainda não confirmado/)).toBeVisible();
  const pending=await page.evaluate(key=>JSON.parse(sessionStorage.getItem(key)!),key);
  expect(pending).toEqual(intent);expect((await api(page,`tabs/${tab.id}/`)).payments).toHaveLength(1);
  await page.reload();await page.getByRole("button",{name:"Verificar mesmo recebimento"}).click();
  await expect.poll(()=>page.evaluate(key=>sessionStorage.getItem(key),key)).toBeNull();
  expect(bodies).toHaveLength(2);expect(bodies[0]).toBe(bodies[1]);
  const bill=await api(page,`tabs/${tab.id}/`);expect(bill.payments).toHaveLength(1);expect(bill.state).toBe("CLOSED");
});
