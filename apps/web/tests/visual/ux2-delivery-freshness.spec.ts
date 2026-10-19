import {test,expect,type Page} from '@playwright/test';
import {fixture} from './fixtures';
import fs from 'node:fs/promises';
async function setup(page:Page,initialFail=false){
 await fixture(page,'normal',true);
 await page.route('**/api/auth/me',r=>r.fulfill({json:{staff:{id:'operator-test',display_name:'Operador'},venue:{id:'venue-test',name:'Teste'},session:{id:'session-test'},capabilities:['table.manage','tab.open']}}));
 let failing=initialFail;let coreFail=false;
 const tab={id:'closed-tab',display_label:'Rafael',state:'CLOSED',exposure_cents:0,orders:[],payments:[],version:2};
 const table={id:'table-08',label:'08',status:'OCCUPIED',active_occupancy:{id:'occupancy-08',generation:1,tabs:[tab]}};
 await page.route('**/api/attendance/hospitality/tables/',r=>coreFail?r.fulfill({status:503,json:{message:'Core unavailable'}}):r.fulfill({json:{table_service_enabled:true,results:[table]}}));
 await page.route('**/api/attendance/tabs/closed-tab/**',r=>r.fulfill({json:tab}));
 await page.route('**/api/attendance/dispatch/delivery/',r=>failing?r.fulfill({status:503,json:{message:'Dispatch unavailable'}}):r.fulfill({json:{results:[{id:'delivery-one',task_type:'DELIVERY',state:'OPEN',product_name:'Chopp Pilsen',quantity:2,tab_label:'Rafael',destination_label:'Mesa08',age_seconds:60}]}}));
 await page.goto('/attendance');await expect(page.getByRole('heading',{name:'Agora',exact:true})).toBeVisible();await page.getByRole('button',{name:/Entregas/}).click();
 return {fail:()=>{failing=true;},recover:()=>{failing=false;},failCore:()=>{coreFail=true;}};
}
for(const width of [360,390,430,1280])test(`dispatch outage preserves queue and core navigation ${width}`,async({page})=>{
 await page.setViewportSize({width,height:844});const state=await setup(page);await expect(page.getByRole('button',{name:'Entregas 1',exact:true})).toBeVisible();state.fail();await page.clock.runFor(16000);
 await expect(page.getByText('Entregas desatualizadas.',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Entregas —',exact:true})).toBeVisible();await expect(page.getByText('2× Chopp Pilsen',{exact:true})).toBeVisible();await expect(page.getByText('Desatualizado · verifique a conexão',{exact:true})).toHaveCount(0);
 await fs.mkdir('visual-artifacts/033/delivery-freshness',{recursive:true});await page.screenshot({path:`visual-artifacts/033/delivery-freshness/dispatch-stale-${width}.png`,fullPage:true});
 await page.getByRole('button',{name:'Mesas',exact:true}).click();await expect(page.getByRole('button',{name:/Mesa 08 Ocupada/})).toBeEnabled();await page.getByRole('button',{name:/Mesa 08 Ocupada/}).click();await expect(page.getByText('Entregas não verificadas.',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Grupo saiu · Liberar mesa',exact:true})).toHaveCount(0);
 state.recover();await page.getByRole('button',{name:'Atualizar entregas',exact:true}).click();await expect(page.getByRole('button',{name:'Grupo saiu · Liberar mesa',exact:true})).toBeEnabled();
});
test('initial Dispatch failure is unknown rather than an empty queue',async({page})=>{await setup(page,true);await expect(page.getByText('Entregas desatualizadas.',{exact:true})).toBeVisible();await expect(page.getByText('Nenhuma tarefa nesta fila. Selecione a outra categoria para conferir.',{exact:true})).toHaveCount(0);await page.getByRole('button',{name:'Mesas',exact:true}).click();await expect(page.getByRole('button',{name:/Mesa 08 Ocupada/})).toBeEnabled();});
test('core outage blocks mutations even when Dispatch is fresh',async({page})=>{const state=await setup(page);state.failCore();await page.clock.runFor(16000);await expect(page.getByText('Desatualizado · verifique a conexão',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Mesas',exact:true}).click();await page.getByRole('button',{name:/Mesa 08 Ocupada/}).click();await expect(page.getByRole('button',{name:'＋ Abrir nova comanda',exact:true})).toBeDisabled();});
