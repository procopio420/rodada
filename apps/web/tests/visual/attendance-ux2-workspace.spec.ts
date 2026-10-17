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
 await page.goto("/attendance");await page.getByRole("button",{name:kind === "TABLE" ? /Mesa08.*Escolher comanda/ : /Mesa08.*Abrir conta/}).click();
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

test("UX2 preserves table search without hiding a task destination or leaking task to next Tab",async({page})=>{
 await fixture(page,"normal",true);
 const makeTab=(id:string,name:string,table:string)=>({id,display_label:name,table_label:table,state:"OPEN",version:1,exposure_cents:0,effective_limit_cents:20000,remaining_capacity_cents:20000,relationship_snapshot:"REGULAR",orders:[],payments:[]});
 const a=makeTab("tab-a","Marina","08"),b=makeTab("tab-b","João","12");
 const tables=[{id:"table-a",label:"08",status:"OCCUPIED",active_occupancy:{id:"visit-a",generation:1,tabs:[a]}},{id:"table-b",label:"12",status:"OCCUPIED",active_occupancy:{id:"visit-b",generation:1,tabs:[b]}}];
 const task={id:"call-table-b",task_type:"SERVICE_REQUEST",state:"OPEN",destination_label:"Mesa12",claimed_by_id:null,target_version:1,target:{kind:"TABLE",tab_id:null,table_id:"table-b",occupancy_id:"visit-b",generation:1}};
 let mutations=0;
 await page.route("**/api/attendance/hospitality/tables/",r=>r.fulfill({json:{table_service_enabled:true,results:tables}}));
 await page.route(/\/api\/attendance\/tabs\/(tab-a|tab-b)\/(\?.*)?$/,r=>r.fulfill({json:r.request().url().includes("tab-a")?a:b}));
 await page.route("**/api/attendance/dispatch/requests/",r=>r.fulfill({json:{results:[task]}}));
 await page.route("**/api/attendance/dispatch/tasks/call-table-b/",r=>r.fulfill({json:task}));
 await page.route("**/api/attendance/dispatch/requests/call-table-b/*/",r=>{mutations++;return r.abort();});
 await page.goto("/attendance");await page.getByRole("button",{name:"Mesas",exact:true}).click();await page.getByLabel("Buscar mesa ou comanda").fill("08");
 await page.getByRole("button",{name:"Agora",exact:true}).click();await page.getByRole("button",{name:/Mesa12.*Escolher comanda/}).click();
 await expect(page.getByRole("heading",{name:"Mesa 12",exact:true})).toBeVisible();await page.locator('button[data-tab-id="tab-b"]').click();await expect(page.getByRole("heading",{name:"João",exact:true})).toBeVisible();
 await page.getByRole("complementary",{name:"Chamado de origem"}).getByRole("button",{name:"Voltar à fila →",exact:true}).click();await expect(page.getByRole("heading",{name:"Agora",exact:true})).toBeVisible();
 await page.getByRole("button",{name:"Pedir",exact:true}).click();await page.getByRole("button",{name:"Escolher mesa ou comanda",exact:true}).click();await expect(page.getByLabel("Buscar mesa ou comanda")).toHaveValue("08");await page.getByRole("button",{name:/Mesa 08 Ocupada/}).click();await page.locator('button[data-tab-id="tab-a"]').click();
 await expect(page.getByRole("heading",{name:"Adicionar itens.",exact:true})).toBeVisible();await expect(page.getByRole("complementary",{name:"Chamado de origem"})).toHaveCount(0);expect(mutations).toBe(0);
});

test("UX2 unknown order reload verifies the original payload without duplicate or false success",async({page})=>{
 await fixture(page,"normal",true);
 const tab={id:"tab-test",display_label:"Marina",table_label:"08",state:"OPEN",version:1,exposure_cents:0,effective_limit_cents:20000,remaining_capacity_cents:20000,relationship_snapshot:"REGULAR",orders:[] as unknown[],payments:[]};
 const attempts:string[]=[];let readbackFail=false;
 await page.route("**/api/attendance/hospitality/tables/",r=>r.fulfill({json:{table_service_enabled:true,results:[{id:"table-test",label:"08",status:"OCCUPIED",active_occupancy:{id:"visit",generation:1,tabs:[tab]}}]}}));
 await page.route(/\/api\/attendance\/tabs\/tab-test\/(\?.*)?$/,r=>r.fulfill(readbackFail?{status:503,json:{message:"Readback indisponível"}}:{json:tab}));
 await page.route("**/api/attendance/tabs/tab-test/orders/confirm/",r=>{attempts.push(r.request().postData()!);tab.orders=[{id:"original-order",status:"CONFIRMED",confirmed_at:"2026-10-16T20:00:00Z",items:[{id:"i",product_name:"Fritas",quantity:1,state:"NEW",fulfillment_station_snapshot:"KITCHEN"}]}];return attempts.length===1?r.abort():r.fulfill({json:{id:"original-order",tab_id:tab.id}});});
 await page.goto("/attendance");await page.getByRole("button",{name:"Mesas",exact:true}).click();await page.getByRole("button",{name:/Mesa 08 Ocupada/}).click();await page.locator('button[data-tab-id="tab-test"]').click();
 await page.getByRole("button",{name:"＋ Adicionar itens",exact:true}).click();await page.getByRole("button",{name:"Adicionar Fritas",exact:true}).click();await page.getByRole("button",{name:/Enviar 1 item/}).click();
 await expect(page.getByText("Envio sem confirmação",{exact:true})).toBeVisible();expect(attempts).toHaveLength(1);
 const key="rodada.intent.staff-order.v1";const original=await page.evaluate(k=>sessionStorage.getItem(k),key);expect(original).toBeTruthy();
 await page.reload();await expect(page.getByText("Envio sem confirmação",{exact:true})).toBeVisible();expect(attempts).toHaveLength(1);
 readbackFail=true;await page.getByRole("button",{name:"Verificar mesmo pedido",exact:true}).click();await expect(page.getByText(/Resultado ainda não confirmado/)).toBeVisible();expect(await page.evaluate(k=>sessionStorage.getItem(k),key)).toBe(original);
 readbackFail=false;await page.getByRole("button",{name:"Verificar mesmo pedido",exact:true}).click();await expect(page.getByText("Pedido confirmado.",{exact:true})).toBeVisible();expect(attempts).toHaveLength(3);expect(new Set(attempts).size).toBe(1);expect(await page.evaluate(k=>sessionStorage.getItem(k),key)).toBeNull();
});

for(const width of [360,390,430,1280]) test(`UX2 repeat page edits selection and sends once ${width}`,async({page})=>{
 await page.setViewportSize({width,height:844});await fixture(page,"normal",true);
 const tab={id:"tab-test",display_label:"Marina",table_label:"08",state:"OPEN",version:1,exposure_cents:7200,effective_limit_cents:20000,remaining_capacity_cents:12800,orders:[{id:"previous",status:"CONFIRMED",confirmed_at:"2026-10-16T02:00:00Z",items:[{id:"old-fries",product_id:"fries",product_name:"Fritas",quantity:1,unit_price_cents:7200,state:"NEW",fulfillment_station_snapshot:"KITCHEN",customization_snapshot:{variant:null,modifiers:[],special_instructions:""}}]}],payments:[]};
 await page.route("**/api/attendance/hospitality/tables/",r=>r.fulfill({json:{table_service_enabled:true,results:[{id:"table-test",label:"08",status:"OCCUPIED",active_occupancy:{id:"visit",generation:1,tabs:[tab]}}]}}));
 await page.route(/\/api\/attendance\/tabs\/tab-test\/(\?.*)?$/,r=>r.fulfill({json:tab}));
 let sends=0;await page.route("**/api/attendance/tabs/tab-test/orders/confirm/",r=>{sends++;expect(r.request().postDataJSON().lines[0].quantity).toBe(2);tab.orders.push({...tab.orders[0],id:"new-round",confirmed_at:"2026-10-17T02:00:00Z"});return r.fulfill({json:{id:"new-round",tab_id:tab.id}});});
 await page.goto("/attendance");await page.getByRole("button",{name:"Mesas",exact:true}).click();await page.getByRole("button",{name:/Mesa 08 Ocupada/}).click();await page.locator('button[data-tab-id="tab-test"]').click();
 await page.getByRole("button",{name:"↻ Mais uma rodada",exact:true}).click();await expect(page.getByRole("heading",{name:"Mais uma rodada.",exact:true})).toBeVisible();await expect(page.getByRole("dialog")).toHaveCount(0);
 await page.getByRole("button",{name:"Reduzir Fritas",exact:true}).click();await expect(page.getByRole("button",{name:"Repetir rodada · enviar",exact:true})).toBeDisabled();
 await page.getByRole("button",{name:"Aumentar Fritas",exact:true}).click();await page.getByRole("button",{name:"Aumentar Fritas",exact:true}).click();await expect(page.getByLabel("Quantidade de Fritas",{exact:true})).toHaveText("2");await layoutAndA11y(page);await page.screenshot({path:`visual-artifacts/033/ux2-repeat-${width}.png`,fullPage:true});
 await page.getByRole("button",{name:"Repetir rodada · enviar",exact:true}).click();await expect(page.getByRole("region",{name:"Último pedido confirmado"})).toContainText("#new-round");expect(sends).toBe(1);
});
