import {expect,test} from '@playwright/test';
import {fixture} from './fixtures';
import {mkdir} from 'node:fs/promises';
for(const width of [360,390,430,1280]) test(`UX2 comparison captures ${width}`,async({page})=>{
 await page.setViewportSize({width,height:844});await fixture(page,'normal',true);
 const names=['Chopp Pilsen','Água sem gás','Refrigerante lata','Suco de laranja','Batata frita','Polenta frita','Pastel de queijo','Hambúrguer da casa'];
 const prices=[1400,600,800,1200,2800,2600,1600,3400];
 const products=names.map((name,i)=>({id:`p${i+1}`,name,price_cents:prices[i],category:i<4?'Bebidas':i<7?'Porções':'Lanches',active:true,availability:'AVAILABLE',variants:[],modifier_groups:[]}));
 const tab={id:'tab-parity',display_label:'Marina',table_label:'08',state:'OPEN',version:1,exposure_cents:5600,effective_limit_cents:20000,remaining_capacity_cents:14400,relationship_snapshot:'REGULAR',orders:[],payments:[]};
 await page.route('**/api/attendance/catalog/products/',r=>r.fulfill({json:{results:products}}));
 await page.route('**/api/attendance/hospitality/tables/',r=>r.fulfill({json:{table_service_enabled:true,results:[{id:'table-parity',label:'08',status:'OCCUPIED',active_occupancy:{id:'visit',generation:1,tabs:[tab]}}]}}));
 await page.route(/\/api\/attendance\/tabs\/tab-parity\/(\?.*)?$/,r=>r.fulfill({json:tab}));
 await page.goto('/attendance');await page.getByRole('button',{name:'Mesas',exact:true}).click();await page.getByRole('button',{name:/Mesa 08 Ocupada/}).click();await page.locator('button[data-tab-id="tab-parity"]').click();
 const w=page.getByRole('region',{name:'Comanda selecionada',exact:true});await expect(w.getByRole('heading',{name:'Marina',exact:true})).toBeVisible();
 const out='../../docs/development/evidence/spec033-parity-comparison';await mkdir(out,{recursive:true});
 await page.screenshot({path:`${out}/web-tab-${width}.png`,fullPage:true});
 await w.getByRole('button',{name:'＋ Adicionar itens',exact:true}).click();await w.getByRole('button',{name:'Adicionar Chopp Pilsen',exact:true}).click();
 await page.screenshot({path:`${out}/web-catalog-${width}.png`,fullPage:true});await w.getByRole('button',{name:'Ver resumo',exact:true}).click();await page.screenshot({path:`${out}/web-review-${width}.png`,fullPage:true});
});
