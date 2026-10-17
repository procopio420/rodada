import {expect,test} from "./fixtures";
import {execFileSync} from "node:child_process";
import {resolve} from "node:path";
for(const width of [360,390,430,1280]) test(`UX2 direct catalog order and reload canonical ${width}`,async({page})=>{
 await page.setViewportSize({width,height:844});
 const label=`UX2 Canonical ${width}`;
 execFileSync(process.env.RODADA_TEST_PYTHON!,["-c",`import os,sys
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django;django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
assert settings.DATABASES['default']['HOST']=='127.0.0.1'
from modules.venue.models import Venue
from modules.hospitality.models import Table,TableOccupancy,TabOccupancyAssignment
from modules.ordering.models import Tab
venue=Venue.objects.get(slug='web-e2e')
table=Table.objects.create(venue=venue,label=sys.argv[1],status='OCCUPIED')
occupancy=TableOccupancy.objects.create(table=table,generation=table.access_generation)
tab=Tab.objects.create(venue=venue,display_label=sys.argv[1],operating_limit_cents=20000)
TabOccupancyAssignment.objects.create(tab=tab,occupancy=occupancy)
`,label],{cwd:resolve("../api"),env:process.env});
 await page.goto("/attendance");await page.getByLabel("Estabelecimento").fill("web-e2e");await page.getByLabel("Operador",{exact:true}).fill("test-manager");await page.getByLabel("PIN",{exact:true}).fill("2468");await page.getByRole("button",{name:"Entrar",exact:true}).click();
 const open=async()=>{await page.getByRole("button",{name:"Mesas",exact:true}).click();await page.getByLabel("Buscar mesa ou comanda").fill(label);await page.getByRole("button",{name:new RegExp(`Mesa ${label}`)}).click();await page.getByRole("button",{name:new RegExp(`^${label} · Comanda`)}).click();};
 await open();const workspace=page.getByRole("region",{name:"Comanda selecionada",exact:true});await expect(workspace.getByRole("heading",{name:label,exact:true})).toBeVisible();
 await workspace.getByRole("button",{name:"＋ Adicionar itens",exact:true}).click();
 for(const product of ["Kitchen E2E item","Bar E2E item"]) await workspace.getByRole("button",{name:`Adicionar ${product}`,exact:true}).click();
 await workspace.getByRole("button",{name:"Ver resumo",exact:true}).click();await expect(workspace.getByText("1× Kitchen E2E item",{exact:true})).toBeVisible();await expect(workspace.getByText("1× Bar E2E item",{exact:true})).toBeVisible();
 await workspace.getByRole("button",{name:"← Continuar escolhendo itens",exact:true}).click();await workspace.getByRole("button",{name:/Enviar 2 itens/}).click();
 await expect(workspace.getByRole("region",{name:"Último pedido confirmado"})).toContainText("Cozinha · Na fila");await expect(workspace.getByRole("region",{name:"Último pedido confirmado"})).toContainText("Bar · Na fila");
 const reference=await workspace.getByRole("region",{name:"Último pedido confirmado"}).textContent();await page.screenshot({path:`test-results/integration/033-ux2-workspace-${width}.png`,fullPage:true});
 await page.reload();await open();await expect(workspace.getByRole("region",{name:"Último pedido confirmado"})).toHaveText(reference!);
 const detail=await page.evaluate(async label=>{const list=await(await fetch(`/api/attendance/tabs/?q=${encodeURIComponent(label)}`)).json();const tab=list.results.find((value:{display_label:string})=>value.display_label===label);return(await fetch(`/api/attendance/tabs/${tab.id}/`)).json();},label);
 expect(detail.orders).toHaveLength(1);expect(detail.orders[0].items).toHaveLength(2);expect(detail.exposure_cents).toBe(1500);expect(detail.payments).toHaveLength(0);
});

test("UX2 real committed order lost ACK reload reconciles one intent and ledger",async({page})=>{
 await page.goto("/attendance");await page.getByLabel("Estabelecimento").fill("web-e2e");await page.getByLabel("Operador",{exact:true}).fill("test-manager");await page.getByLabel("PIN",{exact:true}).fill("2468");await page.getByRole("button",{name:"Entrar",exact:true}).click();
 await expect(page.getByRole("button",{name:"Mesas",exact:true})).toBeVisible();
 const label="UX2 lost ACK original";
 const tab=await page.evaluate(async display_label=>{const response=await fetch("/api/attendance/tabs/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({display_label})});if(!response.ok)throw new Error(`Create fixture ${response.status}`);return response.json();},label);
 await page.reload();await page.getByRole("button",{name:"Mesas",exact:true}).click();
 await page.getByLabel("Buscar mesa ou comanda").fill(label);await page.locator(`button[data-tab-id="${tab.id}"]`).click();
 await page.getByRole("button",{name:"＋ Adicionar itens",exact:true}).click();for(const product of ["Kitchen E2E item","Bar E2E item"])await page.getByRole("button",{name:`Adicionar ${product}`,exact:true}).click();
 const attempts:string[]=[];let originalOrder="";
 await page.route(`**/api/attendance/tabs/${tab.id}/orders/confirm/`,async route=>{attempts.push(route.request().postData()!);const response=await route.fetch({url:route.request().url().replace(/\/$/,""),headers:await route.request().allHeaders()});expect(response.ok()).toBeTruthy();const body=await response.json();if(!originalOrder)originalOrder=body.id;else expect(body.id).toBe(originalOrder);if(attempts.length===1)await route.abort();else await route.fulfill({response});});
 await page.getByRole("button",{name:/Enviar 2 itens/}).click();await expect(page.getByText("Envio sem confirmação",{exact:true})).toBeVisible();
 const key="rodada.intent.staff-order.v1",saved=await page.evaluate(k=>sessionStorage.getItem(k),key);expect(saved).toBeTruthy();await page.reload();await expect(page.getByText("Envio sem confirmação",{exact:true})).toBeVisible();expect(attempts).toHaveLength(1);await page.getByRole("button",{name:"Verificar mesmo pedido",exact:true}).click();
 await expect(page.getByRole("region",{name:"Último pedido confirmado"})).toContainText(`#${originalOrder}`);expect(attempts).toHaveLength(2);expect(attempts[0]).toBe(attempts[1]);await expect.poll(()=>page.evaluate(k=>sessionStorage.getItem(k),key)).toBeNull();
 const canonical=await page.evaluate(async id=>(await fetch(`/api/attendance/tabs/${id}/`)).json(),tab.id);expect(canonical.orders).toHaveLength(1);expect(canonical.orders[0].id).toBe(originalOrder);expect(canonical.orders[0].items).toHaveLength(2);expect(canonical.exposure_cents).toBe(1500);expect(canonical.payments).toHaveLength(0);
});

test("UX2 real cleaning records both canonical lifecycle transitions",async({page})=>{
 const label="UX2 cleaning canonical";
 execFileSync(process.env.RODADA_TEST_PYTHON!,["-c",`import os,sys
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django;django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e' and settings.DATABASES['default']['HOST']=='127.0.0.1'
from modules.venue.models import Venue
from modules.hospitality.models import Table,TableOccupancy
from django.utils import timezone
table=Table.objects.create(venue=Venue.objects.get(slug='web-e2e'),label=sys.argv[1],status='DIRTY')
TableOccupancy.objects.create(table=table,generation=table.access_generation,released_at=timezone.now())
`,label],{cwd:resolve("../api"),env:process.env});
 await page.goto("/attendance");await page.getByLabel("Estabelecimento").fill("web-e2e");await page.getByLabel("Operador",{exact:true}).fill("test-manager");await page.getByLabel("PIN",{exact:true}).fill("2468");await page.getByRole("button",{name:"Entrar",exact:true}).click();await page.getByRole("button",{name:"Mesas",exact:true}).click();await page.getByLabel("Buscar mesa ou comanda").fill(label);await page.getByRole("button",{name:new RegExp(`Mesa ${label}`)}).click();
 const read=()=>page.evaluate(async label=>{const payload=await(await fetch('/api/attendance/hospitality/tables/')).json();return payload.results.find((t:{label:string})=>t.label===label);},label);
 expect((await read()).status).toBe("DIRTY");await expect(page.getByRole("button",{name:"Concluir limpeza",exact:true})).toHaveCount(0);await page.getByRole("button",{name:"Iniciar limpeza",exact:true}).click();await expect(page.getByRole("button",{name:"Concluir limpeza",exact:true})).toBeEnabled();expect((await read()).status).toBe("CLEANING");await page.getByRole("button",{name:"Concluir limpeza",exact:true}).click();await expect(page.getByRole("button",{name:new RegExp(`Mesa ${label} Disponível`)})).toBeVisible();expect((await read()).status).toBe("AVAILABLE");
 execFileSync(process.env.RODADA_TEST_PYTHON!,["-c",`import os,sys
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django;django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e' and settings.DATABASES['default']['HOST']=='127.0.0.1'
from modules.hospitality.models import TableOccupancy
occupancy=TableOccupancy.objects.get(table__venue__slug='web-e2e',table__label=sys.argv[1])
assert occupancy.released_at <= occupancy.cleaning_started_at <= occupancy.ready_at
assert occupancy.cleaning_started_by_id and occupancy.ready_by_id
`,label],{cwd:resolve("../api"),env:process.env});
});
