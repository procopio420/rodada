import { test, expect, type Page } from './fixtures';
async function api(page: Page, path: string, body?: object) {
 return page.evaluate(async ({path,body})=>{
  const r=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});
  return {status:r.status,body:await r.json()};
 },{path,body});
}
for(const replacement of [false,true]) test(`release fences the originally confirmed occupancy, replacement ${replacement}`,async({page})=>{
 await page.goto('/attendance');await page.getByLabel('Estabelecimento').fill('web-e2e');await page.getByLabel('Operador',{exact:true}).fill('test-manager');await page.getByLabel('PIN',{exact:true}).fill('2468');await page.getByRole('button',{name:'Entrar',exact:true}).click();await expect(page.getByRole('heading',{name:'Agora',exact:true})).toBeVisible();
 const created=await api(page,'/api/pos/hospitality/tables/',{label:`Release fence ${crypto.randomUUID()}`,guest_ordering_mode:'DIRECT'});expect(created.status).toBe(201);const table=created.body;
 const occupied=await api(page,`/api/pos/hospitality/tables/${table.id}/occupy/`,{});expect(occupied.status).toBe(201);const original=occupied.body;
 const captured={expected_occupancy_id:original.id,expected_generation:original.generation};
 await page.reload();await page.getByRole('button',{name:'Mesas',exact:true}).click();await page.getByRole('button',{name:new RegExp(`^Mesa ${table.label}`)}).click();await page.getByRole('button',{name:'Grupo saiu · Liberar mesa',exact:true}).click();
 let replacementId:string|null=null;let posts=0;let status=0;
 await page.route(new RegExp(`/api/attendance/hospitality/tables/${table.id}/release/?$`),async route=>{
  posts++;expect(route.request().postDataJSON()).toEqual(captured);
  if(replacement){
   expect((await api(page,`/api/pos/hospitality/tables/${table.id}/release/`,captured)).status).toBe(200);
   for(const action of ['cleaning/start','cleaning/complete'])expect((await api(page,`/api/pos/hospitality/tables/${table.id}/${action}/`,{})).status).toBe(200);
   const next=await api(page,`/api/pos/hospitality/tables/${table.id}/occupy/`,{});expect(next.status).toBe(201);replacementId=next.body.id;
  }
  const response=await route.fetch();status=response.status();await route.fulfill({response});
 });
 await page.getByRole('button',{name:'Confirmar liberação',exact:true}).click();
 await expect.poll(()=>status).toBe(replacement?409:200);expect(posts).toBe(1);
 const current=(await api(page,'/api/attendance/hospitality/tables/')).body.results.find((row:{id:string})=>row.id===table.id);
 if(replacement){expect(current.status).toBe('OCCUPIED');expect(current.active_occupancy.id).toBe(replacementId);await expect(page.getByRole('dialog',{name:`Liberar mesa ${table.label}?`,exact:true})).toContainText('A ocupação mudou. Confira a mesa novamente.');}
 else {expect(current.status).toBe('DIRTY');expect(current.active_occupancy).toBeNull();}
});
