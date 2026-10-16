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
