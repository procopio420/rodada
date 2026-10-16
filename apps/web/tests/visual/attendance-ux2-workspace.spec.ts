import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const width of [360,390,430,1280]) test(`UX2 pages preserve destination and direct send ${width}`, async ({page}) => {
 await page.setViewportSize({width,height:844}); await fixture(page,"normal",true);
 const tab={id:"tab-test",display_label:"Marina",table_label:"08",state:"OPEN",version:1,exposure_cents:5600,effective_limit_cents:20000,remaining_capacity_cents:14400,relationship_snapshot:"REGULAR",orders:[] as unknown[],payments:[]};
 await page.route("**/api/attendance/hospitality/tables/",route=>route.fulfill({json:{table_service_enabled:true,results:[{id:"table-test",label:"08",status:"OCCUPIED",active_occupancy:{id:"visit",generation:1,tabs:[tab]}}]}}));
 await page.route(/\/api\/attendance\/tabs\/tab-test\/(\?.*)?$/,route=>route.fulfill({json:tab}));
 const attempts:unknown[]=[];
 await page.route("**/api/attendance/tabs/tab-test/orders/confirm/",route=>{
  const body=route.request().postDataJSON();attempts.push(body);
  tab.orders=[{id:"canonical-order-033",status:"CONFIRMED",confirmed_at:"2026-10-16T20:00:00Z",items:[{id:"confirmed",product_name:"Fritas",quantity:1,state:"NEW",fulfillment_station_snapshot:"KITCHEN"}]}];
  return route.fulfill({json:{id:"canonical-order-033",tab_id:tab.id}});
 });
 await page.goto("/attendance");await page.getByRole("button",{name:"Mesas",exact:true}).click();
 await page.getByRole("button",{name:/Mesa 08 Ocupada/}).click();await page.locator('button[data-tab-id="tab-test"]').click();
 const workspace=page.getByRole("region",{name:"Comanda selecionada",exact:true});
 await expect(workspace.getByRole("heading",{name:"Marina",exact:true})).toBeVisible();
 await expect(page.locator(".attendanceOrderDialog")).toHaveCount(0);
 await page.screenshot({path:`visual-artifacts/033/ux2-tab-${width}.png`,fullPage:true});
 await workspace.getByRole("button",{name:"＋ Adicionar itens",exact:true}).click();
 await workspace.getByRole("button",{name:"Adicionar Fritas",exact:true}).click();
 await expect(workspace.getByRole("button",{name:/Enviar 1 item/})).toBeEnabled();
 await workspace.getByRole("button",{name:"Ver resumo",exact:true}).click();
 await expect(workspace.getByText("1× Fritas",{exact:true})).toBeVisible();
 await workspace.getByRole("button",{name:"← Continuar escolhendo itens",exact:true}).click();
 await workspace.getByLabel("Buscar produto").fill("nenhum");
 await expect(workspace.getByText(/Nenhum produto corresponde/)).toBeVisible();
 await expect(workspace.getByRole("button",{name:/Enviar 1 item/})).toBeEnabled();
 await layoutAndA11y(page);
 await page.screenshot({path:`visual-artifacts/033/ux2-catalog-${width}.png`,fullPage:true});
 await workspace.getByRole("button",{name:/Enviar 1 item/}).click();
 await expect(workspace.getByText("Pedido #canonical-order-033 confirmado",{exact:true})).toBeVisible();
 await expect(workspace.getByText("Cozinha · Na fila",{exact:true})).toBeVisible();
 await expect(workspace.getByRole("button",{name:"＋ Adicionar itens",exact:true})).toBeVisible();
 expect(attempts).toHaveLength(1);
 await page.screenshot({path:`visual-artifacts/033/ux2-confirmed-${width}.png`,fullPage:true});
});

for(const kind of ["TAB","TABLE"] as const) test(`UX2 called task retains explicit actions for ${kind} target`,async({page})=>{
 await fixture(page,"normal",true);
 const tab={id:"tab-test",display_label:"Marina",table_label:"08",state:"OPEN",version:1,exposure_cents:0,effective_limit_cents:20000,remaining_capacity_cents:20000,relationship_snapshot:"REGULAR",orders:[],payments:[]};
 const table={id:"table-test",label:"08",status:"OCCUPIED",active_occupancy:{id:"visit",generation:1,tabs:[tab]}};
 let task={id:"call-exact",task_type:"BILL_REQUEST",state:"OPEN",destination_label:"Mesa08",claimed_by_id:null as string|null,target_version:1,target:{kind,tab_id:kind==="TAB"?tab.id:null,table_id:table.id,occupancy_id:"visit",generation:1}};
 const mutations:string[]=[];
 await page.route("**/api/attendance/hospitality/tables/",r=>r.fulfill({json:{table_service_enabled:true,results:[table]}}));
 await page.route(/\/api\/attendance\/tabs\/tab-test\/(\?.*)?$/,r=>r.fulfill({json:tab}));
 await page.route("**/api/attendance/dispatch/requests/",r=>r.fulfill({json:{results:task.state==="DONE"?[]:[task]}}));
 await page.route("**/api/attendance/dispatch/tasks/call-exact/",r=>r.fulfill({json:task}));
 await page.route("**/api/attendance/dispatch/requests/call-exact/complete/",r=>{mutations.push(r.request().url());task={...task,state:"DONE"};return r.fulfill({json:task});});
 await page.goto("/attendance");await page.getByRole("button",{name:/Mesa08.*Abrir conta/}).click();
 const context=page.getByRole("complementary",{name:"Chamado de origem"});await expect(context).toBeVisible();expect(mutations).toHaveLength(0);
 if(kind==="TABLE") await page.locator('button[data-tab-id="tab-test"]').click();
 await expect(page.getByRole("heading",{name:"Fechar a conta.",exact:true})).toBeVisible();
 await context.getByRole("button",{name:"Apenas concluir pedido de conta",exact:true}).click();await expect(context.getByText("Chamada concluída no servidor.")).toBeVisible();expect(mutations).toHaveLength(1);
 await context.getByRole("button",{name:"Voltar à fila →",exact:true}).click();await expect(page.getByRole("heading",{name:"Agora",exact:true})).toBeVisible();
 await page.getByRole("button",{name:"Mesas",exact:true}).click();await page.getByRole("button",{name:/Mesa08|Mesa 08/}).click();await page.locator('button[data-tab-id="tab-test"]').click();await expect(page.getByRole("heading",{name:"Marina",exact:true})).toBeVisible();
});

test("UX2 task readback identity mismatch cannot navigate",async({page})=>{
 await fixture(page,"normal",true);
 await page.route("**/api/attendance/dispatch/tasks/service-test/",r=>r.fulfill({json:{id:"another-task",task_type:"SERVICE_REQUEST",state:"OPEN",target_version:1,target:{kind:"TAB",tab_id:"tab-test",table_id:null,occupancy_id:null,generation:null}}}));
 await page.goto("/attendance");await page.getByRole("button",{name:/Mesa 24.*Atender cliente/}).click();await expect(page.getByRole("alert").filter({hasText:"Identidade da tarefa divergente"})).toBeVisible();await expect(page.getByRole("region",{name:"Comanda selecionada",exact:true})).toHaveCount(0);
});
