import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

test.beforeEach(async({page})=>{await page.addInitScript(()=>{for(const key of Object.keys(localStorage))if(key.startsWith("rodada:order-draft:"))localStorage.removeItem(key);});});

type Position = {effective_limit_cents:number;exposure_cents:number;remaining_capacity_cents:number;relationship_snapshot?:string};
async function showCredit(page:Page,position:Position|null,compact=true) {
 await fixture(page,"normal",true);
 const tab={id:"credit-tab",display_label:"Perfil real",state:"OPEN",version:1,exposure_cents:position?.exposure_cents??0,orders:[],payments:[],...(position??{})};
 await page.route("**/api/attendance/hospitality/tables/",r=>r.fulfill({json:{table_service_enabled:true,results:[{id:"credit-table",label:"08",status:"OCCUPIED",active_occupancy:{id:"visit",generation:1,tabs:[tab]}}]}}));
 await page.route(/\/api\/attendance\/tabs\/credit-tab\/(\?.*)?$/,r=>r.fulfill({json:tab}));
 await page.route("**/api/attendance/catalog/products/",r=>r.fulfill({json:{results:[{id:"draft-credit",name:"Projeção",price_cents:500,active:true,availability:"AVAILABLE",fulfillment_station:"BAR"}]}}));
 await page.goto("/attendance");await page.getByRole("button",{name:"Mesas",exact:true}).click();await page.getByRole("button",{name:/Mesa 08 Ocupada/}).click();await page.locator('button[data-tab-id="credit-tab"]').click();
 if(!compact){await page.getByRole("button",{name:"＋ Adicionar itens",exact:true}).click();await page.getByRole("button",{name:"Adicionar Projeção",exact:true}).click();}
 return page.getByRole("region",{name:"Referência de consumo da comanda",exact:true});
}
for(const width of [360,390,430,1280])for(const scale of [1,2])test(`credit projection ${width}px font ${scale}x`,async({page})=>{
 await page.setViewportSize({width,height:1000});
 for(const percent of [0,79,80,99,100,120])for(const compact of [false,true]){
  const panel=await showCredit(page,{effective_limit_cents:10000,exposure_cents:percent*100,remaining_capacity_cents:Math.max(0,10000-percent*100),relationship_snapshot:"REGULAR"},compact);
  if(scale===2)await panel.evaluate(root=>{for(const e of root.querySelectorAll<HTMLElement>("*"))e.dataset.fontSize=getComputedStyle(e).fontSize;for(const e of root.querySelectorAll<HTMLElement>("*"))e.style.fontSize=`${parseFloat(e.dataset.fontSize!)*2}px`;});
  await expect(panel.getByRole("progressbar")).toHaveCount(1);
  await expect(panel).toHaveAttribute("data-level",percent>=100 || (!compact && percent+5>100)?"exceeded":percent+(!compact?5:0)>=80?"warning":"ok");
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  if(percent===120 && !compact)await expect(panel.getByText(/120% utilizado/)).toBeVisible();
  await panel.screenshot({path:`test-results/credit-bar/credit-${width}-${scale}x-${percent}-${compact}.png`});
 }
 const zero=await showCredit(page,{effective_limit_cents:0,exposure_cents:0,remaining_capacity_cents:0},false);await expect(zero.getByText("Limite zero",{exact:true})).toBeVisible();
});
test("canonical capacity is not recalculated and invalid financial DTO is explicit",async({page})=>{
 const position={effective_limit_cents:10000,exposure_cents:7900,remaining_capacity_cents:1234,relationship_snapshot:"HOUSE"};
 const panel=await showCredit(page,position);await expect(panel.getByText(/12,34 disponíveis/)).toBeVisible();await expect(panel.getByRole("progressbar")).toHaveAttribute("aria-valuenow","79");const details=panel.getByRole("button",{name:"Detalhes ›"});await details.focus();await expect(details).toBeFocused();await layoutAndA11y(page);
 for(const invalid of [null,{...position,effective_limit_cents:-1},{...position,exposure_cents:0.5}]){const invalidPanel=await showCredit(page,invalid);await expect(invalidPanel.getByText(/indisponível/)).toBeVisible();await expect(invalidPanel.getByRole("progressbar")).toHaveCount(0);}
});
