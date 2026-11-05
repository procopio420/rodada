import { expect, test, type Page } from '@playwright/test';
import { fixture } from './fixtures';
import fs from 'node:fs/promises';
const initial = {id:'delivery-one',task_type:'DELIVERY',state:'OPEN',order_item_id:'item-one',order_id:'e19abc12-order',item_state:'READY',claimed_by_id:null as string|null,quantity:2,product_name:'Chopp Pilsen',fulfillment_station:'BAR',destination_label:'Mesa 08',tab_display_label:'Rafael',tab_display_reference:'#1049',tab_label:'Rafael',age_seconds:120,target_version:1,target:{kind:'TAB',tab_id:'closed-tab',table_id:'table-08',occupancy_id:'occupancy-08',generation:1}};
async function setup(page:Page,opts:{rival?:boolean;lostAck?:boolean;unknown?:boolean;moved?:boolean}={}) {
 await fixture(page,'normal',true);let task={...initial,claimed_by_id:opts.rival?'rival':null};let reads=0,posts=0;const writes:string[]=[];
 page.on('request',r=>{if(r.url().includes('/api/attendance/')&&r.method()!=='GET')writes.push(r.url());});
 await page.route('**/api/attendance/dispatch/delivery/',r=>r.fulfill({json:{results:task.state==='DONE'?[]:[task]}}));
 await page.route('**/api/attendance/dispatch/tasks/delivery-one/',r=>{reads++;if(opts.unknown&&posts)return r.abort();if(opts.moved&&reads>1)task={...task,destination_label:'Mesa 12'};return r.fulfill({json:task});});
 await page.route('**/api/attendance/dispatch/delivery/delivery-one/complete/',r=>{posts++;task={...task,state:'DONE',item_state:'DELIVERED'};return opts.lostAck||opts.unknown?r.abort():r.fulfill({json:task});});
 await page.goto('/attendance');await page.getByRole('button',{name:/Entregas/}).click();await page.getByRole('button',{name:'Registrar entrega',exact:true}).click();await expect(page.getByRole('heading',{name:'Registrar entrega',exact:true})).toBeVisible();
 return {writes,getPosts:()=>posts,restore:()=>{opts.unknown=false;}};
}
for(const width of [360,390,430,1280])test(`delivery confirmation stays over the queue ${width}`,async({page})=>{
 await page.setViewportSize({width,height:844});const state=await setup(page);
 const dialog=page.getByRole('dialog',{name:'Registrar entrega'});
 await expect(page.getByText('Prontos para levar',{exact:true})).toBeVisible();
 await expect(dialog.getByText('Mesa 08 · Rafael · #1049',{exact:true})).toBeVisible();
 await expect(dialog.getByText('2× Chopp Pilsen',{exact:true})).toBeVisible();
 await expect(dialog.getByText('· Bar',{exact:true})).toBeVisible();
 await expect(dialog.getByRole('button',{name:'Confirmar entrega',exact:true})).toBeEnabled();
 expect(state.writes).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await fs.mkdir('visual-artifacts/033/delivery',{recursive:true});await page.screenshot({path:`visual-artifacts/033/delivery/web-delivery-${width}.png`,fullPage:true});
 await dialog.getByRole('button',{name:'Voltar',exact:true}).click();await expect(page.getByRole('button',{name:'Registrar entrega',exact:true})).toBeFocused();expect(state.writes).toEqual([]);
});
test('lost ACK confirmed by same-task readback without replay',async({page})=>{const s=await setup(page,{lostAck:true});await page.getByRole('button',{name:'Confirmar entrega',exact:true}).click();await expect(page.getByText('Entrega concluída',{exact:true})).toBeVisible();await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.getByRole('button',{name:'Registrar entrega',exact:true})).toHaveCount(0);expect(s.getPosts()).toBe(1);});
test('rival prevents completion',async({page})=>{const s=await setup(page,{rival:true});await expect(page.getByRole('button',{name:'Confirmar entrega',exact:true})).toBeDisabled();expect(s.writes).toEqual([]);});
test('destination change stops mutation',async({page})=>{const s=await setup(page,{moved:true});await page.getByRole('button',{name:'Confirmar entrega',exact:true}).click();await expect(page.getByRole('dialog', { name: 'Registrar entrega',exact:true}).getByRole('alert')).toContainText('O destino mudou.');await expect(page.getByText('Mesa 12 · Rafael · #1049',{exact:true})).toBeVisible();expect(s.writes).toEqual([]);});
test('unknown response verified without resubmitting',async({page})=>{const s=await setup(page,{unknown:true});await page.getByRole('button',{name:'Confirmar entrega',exact:true}).click();await expect(page.getByText('Resultado desconhecido. Confira a mesma tarefa antes de repetir.',{exact:true})).toBeVisible();s.restore();await page.getByRole('button',{name:'Verificar entrega',exact:true}).click();await expect(page.getByText('Entrega concluída',{exact:true})).toBeVisible();expect(s.getPosts()).toBe(1);});

for (const mode of ["partial", "all", "moved"] as const) test(`delivery groups by comanda and supports ${mode}`, async ({ page }) => {
 await fixture(page, "normal", true);
 const second = { ...initial, id: "delivery-two", order_item_id: "item-two", product_name: "Suco" };
 const other = { ...initial, id: "delivery-other", order_item_id: "item-other", target: { ...initial.target, tab_id: "other-tab" } };
 const tasks = [initial, second, other];
 const writes: string[] = [];
 await page.route("**/api/attendance/dispatch/delivery/", route => route.fulfill({ json: { results: tasks.filter(task => !writes.includes(task.id)) } }));
 await page.route("**/api/attendance/dispatch/tasks/*/", route => {
  const task = tasks.find(value => route.request().url().endsWith(`/${value.id}/`))!;
  const value = writes.includes(task.id) ? { ...task, state: "DONE", item_state: "DELIVERED" }
   : mode === "moved" && task.id === second.id ? { ...task, destination_label: "Mesa 12" } : task;
  return route.fulfill({ json: value });
 });
 await page.route("**/api/attendance/dispatch/delivery/*/complete/", route => {
  writes.push(route.request().url().split("/").at(-3)!);
  return route.fulfill({ json: {} });
 });
 await page.goto("/attendance");
 await page.getByRole("button", { name: "Entregas 3" }).click();
 const group = page.locator(".ux2DeliveryRow").filter({ hasText: "2 itens prontos" });
 await expect(page.locator(".ux2DeliveryRow")).toHaveCount(2);
 await expect(group).toContainText("2× Chopp Pilsen · 2× Suco");
 if (mode === "partial") {
  await group.getByRole("button", { name: /Rafael/ }).click();
  const dialog = page.getByRole("dialog", { name: "Entregas de Rafael" });
  await expect(dialog.getByRole("checkbox")).toHaveCount(2);
  await dialog.getByRole("checkbox", { name: /Suco/ }).check();
  await dialog.getByRole("button", { name: "Confirmar 1 selecionado(s)" }).click();
  await expect(page.getByText("1 item(ns) com entrega confirmada.")).toBeVisible();
  expect(writes).toEqual([second.id]);
 } else {
  await group.getByRole("button", { name: "Confirmar entrega", exact: true }).click();
  if (mode === "moved") {
   await expect(page.getByRole("alert").filter({ hasText: "O destino ou a quantidade mudou." })).toBeVisible();
   expect(writes).toEqual([initial.id]);
  } else {
   await expect(page.getByText("2 item(ns) com entrega confirmada.")).toBeVisible();
   expect(writes).toEqual([initial.id, second.id]);
  }
 }
});
