import { expect, test, type Page } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

function database(code: string) {
  return execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os,json
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from django.core.serializers.json import DjangoJSONEncoder
from modules.venue.models import Venue
from modules.ordering.models import Tab,Order
from modules.ledger.models import Charge,Payment,Refund,LedgerAdjustment
from modules.hospitality.models import Table,TableOccupancy,TabOccupancyAssignment
from modules.tab_operations.models import TabOperation,TabTransferLine
from modules.audit.models import AuditEvent
v=Venue.objects.get(slug='web-e2e')
${code}`], { cwd: resolve("../api"), env: process.env }).toString().trim();
}
async function api(page: Page, path: string, payload?: object, root="pos") {
  return page.evaluate(async ({path,payload,root}) => {
    const response=await fetch(`/api/${root}/${path}`,payload===undefined ? undefined : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const body=await response.json(); if(!response.ok) throw new Error(JSON.stringify(body)); return body;
  },{path,payload,root});
}
const financialSnapshot=()=>database("print(json.dumps([list(model.objects.order_by('id').values()) for model in (Order,Charge,Payment,Refund,LedgerAdjustment)],cls=DjangoJSONEncoder,sort_keys=True))");

test("real location movement preserves finance and recovers without duplicate effects at mobile widths", async ({page}) => {
  test.setTimeout(120000);
  database(`assert not Tab.objects.filter(venue=v).exists()
for width in (360,390,430):
 tab=Tab.objects.create(venue=v,display_label=f'Web move {width}')
 for side in ('A','B'):
  table=Table.objects.create(venue=v,label=f'{side}-{width}',status='OCCUPIED')
  occ=TableOccupancy.objects.create(table=table,generation=1)
  if side=='A': TabOccupancyAssignment.objects.create(tab=tab,occupancy=occ)
Table.objects.create(venue=v,label='Available move destination')`);
  await page.goto("/attendance"); await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador",{exact:true}).fill("test-manager"); await page.getByLabel("PIN",{exact:true}).fill("2468"); await page.getByRole("button",{name:"Entrar",exact:true}).click();
  await expect(page.getByRole("button",{name:"Mesas",exact:true})).toBeEnabled();
  const tabs=(await api(page,"tabs/")).results, tables=(await api(page,"hospitality/tables/",undefined,"attendance")).results;
  const product=(await api(page,"catalog/products/")).results.find((p:{name:string})=>p.name==="Kitchen E2E item");
  for(const width of [360,390,430]) {
    await page.setViewportSize({width,height:900}); const tab=tabs.find((t:{display_label:string})=>t.display_label===`Web move ${width}`);
    const origin=tables.find((t:{label:string})=>t.label===`A-${width}`), destination=tables.find((t:{label:string})=>t.label===`B-${width}`);
    await api(page,`tabs/${tab.id}/orders/confirm/`,{idempotency_key:`move-order-${width}`,lines:[{product_id:product.id,quantity:1}]});
    if(width!==360) await api(page,`tabs/${tab.id}/payments/`,{idempotency_key:`move-payment-${width}`,amount_cents:100,method:"EXTERNAL_TERMINAL"});
    const before=await api(page,`tabs/${tab.id}/`), snapshot=financialSnapshot();
    const base={kind:"MOVE_LOCATION",expected_version:before.version,occupancy_id:destination.active_occupancy.id,reason:"Mudança de lugar",idempotency_key:`disabled-${width}`};
    const disabled=await page.evaluate(async ({id,base})=> {
      const cases=[...['SPLIT','MERGE','MOVE_ITEMS','CANCEL_EMPTY','REOPEN'].map(kind=>({...base,kind})),...['lines','destination_tab_id','service_point_id','amount_cents'].map(key=>({...base,[key]:"forbidden"})),null,{...base,occupancy_id:"invalid"}];
      return Promise.all(cases.map(async body=>(await fetch(`/api/attendance/tabs/${id}/operations`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})).status));
    },{id:tab.id,base}); expect(disabled.every((s:number)=>s===403)).toBe(true);
    await page.getByRole("button",{name:"Mesas",exact:true}).click();
    const originCard = page.locator("article").filter({has:page.getByRole("button",{name:new RegExp(`Mesa A-${width} Ocupada`)})});
    await originCard.getByRole("button",{name:new RegExp(`Mesa A-${width} Ocupada`)}).click();
    await expect(originCard.locator(`button[data-tab-id="${tab.id}"]`)).toBeVisible();
    await originCard.getByRole("button",{name:"Mover comanda",exact:true}).click();
    await expect(page.getByLabel("Mesa de destino")).toBeEnabled();
    expect(await page.getByLabel("Mesa de destino").locator("option").allTextContents()).not.toContain("Mesa Available move destination");
    await page.getByLabel("Mesa de destino").selectOption(destination.active_occupancy.id); await page.getByLabel("Motivo (opcional)").fill("Mudança de lugar");
    const requests:string[]=[]; let operation="", failReadback=false;
    const endpoint=new RegExp(`/api/attendance/tabs/${tab.id}/operations/$`);
    await page.route(endpoint,async route=> {
      requests.push(route.request().postData()!);
      const response=await route.fetch({url:route.request().url().replace(/\/$/,""),headers:await route.request().allHeaders()});
      expect(response.status()).toBe(200); const result=await response.json(); if(!operation) operation=result.operation_id; else expect(result.operation_id).toBe(operation);
      if(width!==360 && requests.length===1) await route.abort(); else await route.fulfill({response});
    });
    await page.route(new RegExp(`/api/attendance/tabs/${tab.id}/$`),route=> failReadback ? route.fulfill({status:503,json:{code:"UNAVAILABLE",message:"Leitura indisponível"}}) : route.continue());
    await page.getByRole("button",{name:"Confirmar movimento",exact:true}).click();
    if(width!==360) {
      await expect(page.getByRole("button",{name:"Verificar mesmo movimento",exact:true})).toBeEnabled();
      await expect(page.getByRole("button",{name:"Sair",exact:true})).toBeDisabled(); await page.reload();
      await expect(page.getByRole("button",{name:"Verificar mesmo movimento",exact:true})).toBeEnabled(); expect(requests).toHaveLength(1);
      if(width===430) {
        failReadback=true; await page.getByRole("button",{name:"Verificar mesmo movimento",exact:true}).click(); await expect(page.getByText(/Resultado ainda não confirmado/)).toBeVisible(); failReadback=false;
      }
      await page.getByRole("button",{name:"Verificar mesmo movimento",exact:true}).click();
    }
    await expect(page.getByText(`Movimento confirmado. Local atual: mesa B-${width}.`,{exact:true})).toBeVisible();
    expect(new Set(requests).size).toBe(1); expect(requests).toHaveLength(width===360 ? 1 : width===390 ? 2 : 3);
    expect(financialSnapshot()).toBe(snapshot); const after=await api(page,`tabs/${tab.id}/`);
    expect(after.exposure_cents).toBe(before.exposure_cents); expect(after.payments).toEqual(before.payments); expect(after.orders).toEqual(before.orders);
    expect(await page.evaluate(()=>sessionStorage.getItem("rodada.intent.tab-location.v1"))).toBeNull();
    const facts=JSON.parse(database(`tab=Tab.objects.get(pk='${tab.id}')
assignments=list(TabOccupancyAssignment.objects.filter(tab=tab).order_by('assigned_at').values('occupancy_id','released_at'))
event=AuditEvent.objects.get(entity_id=str(tab.id),event_type='tab.location_changed')
print(json.dumps({'assignments':assignments,'reason':event.reason,'actor':str(event.actor_staff_id),'events':AuditEvent.objects.filter(entity_id=str(tab.id),event_type='tab.location_changed').count(),'operations':TabOperation.objects.filter(source_tab=tab).count(),'transfers':TabTransferLine.objects.count(),'origin_released':TableOccupancy.objects.get(pk='${origin.active_occupancy.id}').released_at},cls=DjangoJSONEncoder))`));
    expect(facts.operations).toBe(1); expect(facts.events).toBe(1); expect(facts.transfers).toBe(0); expect(facts.reason).toBe("Mudança de lugar"); expect(facts.actor).not.toBe("None"); expect(facts.origin_released).toBeNull();
    expect(facts.assignments).toHaveLength(2); expect(facts.assignments[0].released_at).not.toBeNull(); expect(facts.assignments[1]).toEqual({occupancy_id:destination.active_occupancy.id,released_at:null});
    await page.getByRole("button",{name:"Mesas",exact:true}).click();
    await expect(page.getByRole("button",{name:new RegExp(`Mesa A-${width} Ocupada`)})).toBeVisible();
    await expect(page.getByRole("button", {name:new RegExp(`Mesa A-${width} Ocupada · 0 comandas abertas`)})).toBeVisible();
    await page.getByRole("button", {name:new RegExp(`Mesa B-${width} Ocupada`)}).click();
    await expect(page.locator(`button[data-tab-id="${tab.id}"]`)).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    await page.unroute(endpoint);
  }
});
