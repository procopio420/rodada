import {test,expect,type Page} from './fixtures';
import fs from 'node:fs/promises';
async function api(page:Page,path:string,body?:unknown){return page.evaluate(async({path,body})=>{const r=await fetch(`/api/pos/${path}`,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const result=await r.json();if(!r.ok)throw new Error(`${r.status} ${JSON.stringify(result)}`);return result;},{path,body});}
for(const width of [360,390,430,1280])test(`closed financial Tab retains real READY delivery and lost ACK recovery ${width}`,async({page})=>{
 await page.setViewportSize({width,height:844});await page.goto('/attendance');await page.getByLabel('Estabelecimento').fill('web-e2e');await page.getByLabel('Operador',{exact:true}).fill('test-manager');await page.getByLabel('PIN',{exact:true}).fill('2468');await page.getByRole('button',{name:'Entrar',exact:true}).click();await expect(page.getByRole('heading',{name:'Agora',exact:true})).toBeVisible();
 const point=(await api(page,'cash/points/')).results[0];if(!point.active_shift)await api(page,'cash/shifts/',{cash_point_id:point.id,opening_float_cents:0,business_date:'2026-10-18',idempotency_key:crypto.randomUUID()});
 const tab=await api(page,'tabs/',{display_label:`Delivery closed ${width}`});const product=(await api(page,'catalog/products/')).results.find((p:{name:string})=>p.name==='Bar E2E item');
 await api(page,`tabs/${tab.id}/orders/confirm/`,{idempotency_key:crypto.randomUUID(),lines:[{product_id:product.id,quantity:2}]});let bill=await api(page,`tabs/${tab.id}/`);const item=bill.orders[0].items[0];
 for(const state of ['ACCEPTED','PREPARING','READY'])await api(page,`order-items/${item.id}/transition/`,{state});
 await api(page,`tabs/${tab.id}/payments/`,{amount_cents:bill.exposure_cents,expected_version:bill.version,method:'CASH',cash_point_id:point.id,idempotency_key:crypto.randomUUID()});bill=await api(page,`tabs/${tab.id}/`);await api(page,`tabs/${tab.id}/close/`,{expected_version:bill.version});
 const closed=await api(page,`tabs/${tab.id}/`);expect(closed.state).toBe('CLOSED');expect(closed.exposure_cents).toBe(0);expect(closed.payments).toHaveLength(1);
 const ready=(await api(page,'dispatch/delivery/')).results.find((t:{order_item_id:string})=>t.order_item_id===item.id);expect(ready).toMatchObject({state:'OPEN',item_state:'READY',quantity:2});
 let posts=0;await page.route(new RegExp(`/api/attendance/dispatch/delivery/${ready.id}/complete/?$`),async route=>{posts++;const response=await route.fetch({url:route.request().url().replace(/\/$/,'')});expect(response.status()).toBe(200);await route.abort();});
 await page.reload();await page.getByRole('button',{name:/^Entregas /}).click();await page.locator('.ux2QueueItem').filter({hasText:`Delivery closed ${width}`}).getByRole('button',{name:'Ver entrega ›',exact:true}).click();
 const region=page.getByRole('region',{name:'Levar pedido.',exact:true});await expect(region.getByText('2× Bar E2E item',{exact:true})).toBeVisible();expect((await api(page,`dispatch/tasks/${ready.id}/`)).state).toBe('OPEN');expect(posts).toBe(0);
 await region.getByRole('button',{name:'Voltar sem entregar',exact:true}).click();expect((await api(page,`dispatch/tasks/${ready.id}/`)).state).toBe('OPEN');
 await page.locator('.ux2QueueItem').filter({hasText:`Delivery closed ${width}`}).getByRole('button',{name:'Ver entrega ›',exact:true}).click();
 await region.getByRole('button',{name:'Confirmar entrega',exact:true}).click();await expect(region.getByText('Entrega concluída',{exact:true})).toBeVisible();
 const completed=await api(page,`dispatch/tasks/${ready.id}/`);expect(completed).toMatchObject({id:ready.id,order_item_id:item.id,state:'DONE',item_state:'DELIVERED',completion_source:'MANUAL'});expect(posts).toBe(1);
 const after=await api(page,`tabs/${tab.id}/`);expect(after.payments).toEqual(closed.payments);expect(after.exposure_cents).toBe(0);expect(after.state).toBe('CLOSED');
 await fs.mkdir('visual-artifacts/033/delivery',{recursive:true});await page.screenshot({path:`visual-artifacts/033/delivery/real-closed-delivered-${width}.png`,fullPage:true});
});
