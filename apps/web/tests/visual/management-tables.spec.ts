import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const width of [360,390,430,1280]) test(`Management table inventory at ${width}`, async ({page})=>{
 await fixture(page,"normal",true); await page.setViewportSize({width,height:900});
 let tables = [
  {id:"occupied",label:"Mesa 01",status:"OCCUPIED",active_occupancy:{id:"visit",tabs:[{id:"one",display_label:"Conta A",state:"OPEN"},{id:"two",display_label:"Conta B",state:"SETTLING"},{id:"closed",display_label:"Encerrada",state:"CLOSED"}]}},
  {id:"free",label:"Mesa 02",status:"AVAILABLE",active_occupancy:null},
  {id:"retired",label:"Mesa 03",status:"OUT_OF_SERVICE",active_occupancy:null},
 ];
 await page.route("**/api/pos/hospitality/tables/",route=>route.fulfill({json:{results:tables}}));
 const bodies: object[] = [];
 await page.route("**/api/pos/hospitality/tables/count/",route=>{const body=route.request().postDataJSON();bodies.push(body);tables=tables.map(t=>t.id==="free"?{...t,status:"OUT_OF_SERVICE"}:t);return route.fulfill({json:{confirmed:true}});});
 await page.route("**/api/pos/hospitality/tables/free/inventory/",route=>{tables=tables.map(t=>t.id==="free"?{...t,status:"AVAILABLE"}:t);return route.fulfill({json:tables[1]});});
 await page.goto("/manage/tables");
 await expect(page.getByRole("region",{name:"Resumo das mesas"})).toContainText("Comandas abertas nas mesas2");
 const occupied=page.locator(".tableInventoryRow").filter({hasText:"Mesa 01"});
 await expect(occupied.getByRole("button",{name:"Retirar de uso"})).toBeDisabled();
 await occupied.getByText("Ver comandas de Mesa 01").click(); await expect(occupied.getByText("Conta A",{exact:true})).toBeVisible(); await expect(occupied.getByText("Encerrada",{exact:true})).toHaveCount(0);
 await page.getByLabel("Quantidade de mesas para trabalhar").fill("1"); await page.getByLabel("Mesa 02",{exact:true}).check();
 await page.getByRole("button",{name:"Revisar quantidade"}).click(); await page.getByRole("dialog").getByRole("button",{name:"Confirmar",exact:true}).click();
 await expect(page.getByText("Alteração confirmada. Lista reconsultada.")).toBeVisible(); expect(bodies).toEqual([{target_count:1,expected_count:2,retire_ids:["free"]}]);
 const free=page.locator(".tableInventoryRow").filter({hasText:"Mesa 02"});
 await free.getByRole("button",{name:"Voltar a usar"}).click(); await page.getByRole("dialog").getByRole("button",{name:"Confirmar",exact:true}).click();
 await expect(free.getByText("Disponível",{exact:true})).toBeVisible();
 await layoutAndA11y(page); await page.screenshot({path:`test-results/management-tables-${width}.png`,fullPage:true});
});
test("Lost create response requires readback and explicit review",async({page})=>{
 await fixture(page,"normal",true);
 const tables: object[]=[];
 await page.route("**/api/pos/hospitality/tables/",route=>{
  if(route.request().method()==="POST"){tables.push({id:"new",label:"Terraço",status:"AVAILABLE",active_occupancy:null});return route.abort();}
  return route.fulfill({json:{results:tables}});
 });
 await page.goto("/manage/tables"); await page.getByLabel("Nome ou número da mesa").fill("Terraço"); await page.getByRole("button",{name:"Adicionar mesa",exact:true}).click(); await page.getByRole("dialog").getByRole("button",{name:"Confirmar",exact:true}).click();
 await expect(page.locator(".tableInventoryRow").getByText("Terraço")).toBeVisible(); await expect(page.getByRole("button",{name:"Adicionar mesa",exact:true})).toBeDisabled(); await expect(page.getByRole("button",{name:"Conferi as mesas"})).toBeVisible();
});
test("Failed initial read never displays fabricated zero inventory",async({page})=>{
 await fixture(page,"normal",true); await page.route("**/api/pos/hospitality/tables/",route=>route.abort()); await page.goto("/manage/tables"); await expect(page.getByRole("alert")).toBeVisible(); await expect(page.getByRole("region",{name:"Resumo das mesas"})).toHaveCount(0); await expect(page.getByRole("button",{name:"Revisar quantidade"})).toBeDisabled();
});
