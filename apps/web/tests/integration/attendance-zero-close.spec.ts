import { test, expect, type Page } from "./fixtures";

async function setup(page: Page) {
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", {exact:true}).fill("test-manager");
  await page.getByLabel("PIN", {exact:true}).fill("2468");
  await page.getByRole("button", {name:"Entrar",exact:true}).click();
  await expect(page.getByRole("heading", {name:"Agora",exact:true})).toBeVisible();
  const tab = await page.evaluate(async () => {
    const response = await fetch("/api/attendance/tabs/", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({display_label:`Zero close ${crypto.randomUUID()}`})});
    if (!response.ok) throw new Error(`Fixture ${response.status}`);
    return response.json() as Promise<{id:string;display_label:string}>;
  });
  await page.reload();
  await page.getByRole("button", {name:"Mesas",exact:true}).click();
  await page.getByLabel("Buscar mesa ou comanda").fill(tab.display_label);
  await page.locator(`button[data-tab-id="${tab.id}"]`).click();
  await page.getByRole("button", {name:"Conferir / fechar conta",exact:true}).click();
  return tab;
}

for (const lostAck of [false,true]) test(`zero balance closes directly with canonical readback, lost ACK ${lostAck}`,async({page})=>{
  const tab=await setup(page);
  let closePosts=0,paymentPosts=0;
  page.on("request",request=>{if(request.method()==="POST"&&request.url().includes("/payments"))paymentPosts++;});
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/close/?$`),async route=>{
    closePosts++;
    const response=await route.fetch({url:route.request().url().replace(/\/$/,"")});
    expect(response.status()).toBe(200);
    if(lostAck) await route.abort(); else await route.fulfill({response});
  });
  await page.getByRole("button",{name:"Encerrar comanda",exact:true}).click();
  await expect(page.getByRole("dialog",{name:"Fechar comanda?",exact:true})).toHaveCount(0);
  await expect(page.getByRole("heading",{name:"Conta encerrada.",exact:true})).toBeVisible();
  const canonical=await page.evaluate(async id=>(await(await fetch(`/api/attendance/tabs/${id}/`)).json()),tab.id);
  expect(canonical).toMatchObject({id:tab.id,state:"CLOSED",exposure_cents:0});
  expect(canonical.payments).toHaveLength(0);expect(closePosts).toBe(1);expect(paymentPosts).toBe(0);
  await page.getByRole("button",{name:"Voltar à mesa ou às comandas",exact:true}).click();
  await expect(page.getByRole("button",{name:"Mesas",exact:true})).toBeVisible();
});

test("new canonical consumption blocks zero-balance close without collecting payment",async({page})=>{
  const tab=await setup(page);
  const writes:string[]=[];
  page.on("request",request=>{if(request.method()==="POST")writes.push(new URL(request.url()).pathname);});
  await page.evaluate(async id=>{
    const products=await(await fetch("/api/attendance/catalog/products/")).json();
    const response=await fetch(`/api/attendance/tabs/${id}/orders/confirm/`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({idempotency_key:crypto.randomUUID(),lines:[{product_id:products.results[0].id,quantity:1}]})});
    if(!response.ok)throw new Error(`Consumption ${response.status}`);
  },tab.id);
  await page.getByRole("button",{name:"Encerrar comanda",exact:true}).click();
  await expect(page.getByText("O saldo mudou. Confira a conta antes de encerrar.",{exact:true})).toBeVisible();
  const canonical=await page.evaluate(async id=>(await(await fetch(`/api/attendance/tabs/${id}/`)).json()),tab.id);
  expect(canonical.state).toBe("OPEN");expect(canonical.exposure_cents).toBeGreaterThan(0);expect(canonical.payments).toHaveLength(0);
  expect(writes.filter(path=>/\/(close|payments)\/?$/.test(path))).toEqual([]);
});

test("lost close and unavailable readback recover by reading the same Tab without another Close",async({page})=>{
  const tab=await setup(page);
  let closePosts=0,committed=false,blockRead=true;
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/close/?$`),async route=>{
    closePosts++;
    const response=await route.fetch({url:route.request().url().replace(/\/$/,"")});
    expect(response.status()).toBe(200);committed=true;await route.abort();
  });
  await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/?(?:\\?.*)?$`),route=>committed&&blockRead
    ?route.fulfill({status:503,json:{code:"UNAVAILABLE",message:"Readback unavailable"}}):route.continue());
  await page.getByRole("button",{name:"Encerrar comanda",exact:true}).click();
  await expect(page.getByText("Não foi possível conferir a comanda original.",{exact:true})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Conta encerrada.",exact:true})).toHaveCount(0);
  expect(closePosts).toBe(1);
  blockRead=false;
  await page.getByRole("button",{name:"Encerrar comanda",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Conta encerrada.",exact:true})).toBeVisible();
  expect(closePosts).toBe(1);
  const canonical=await page.evaluate(async id=>(await(await fetch(`/api/attendance/tabs/${id}/`)).json()),tab.id);
  expect(canonical).toMatchObject({state:"CLOSED",exposure_cents:0});expect(canonical.payments).toHaveLength(0);
});
