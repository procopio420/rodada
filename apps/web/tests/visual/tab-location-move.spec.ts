import { expect, test, type Page } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
const tabId = "11111111-1111-4111-8111-111111111111";
const operationId = "99999999-9999-4999-8999-999999999999";
const a = "22222222-2222-4222-8222-222222222222", b = "33333333-3333-4333-8333-333333333333";
const oa = "44444444-4444-4444-8444-444444444444", ob = "55555555-5555-4555-8555-555555555555";
const storage = "rodada.intent.tab-location.v1";
async function setup(page: Page) {
  await fixture(page, "normal", true);
  const state = { moved: false, failReadback: false, session: "session-move", contextError: false };
  await page.route("**/api/attendance/hospitality/occupancies/*/party-size/", route => route.fulfill({ json: { current: { covers_count: null, version: 1, source: null } } }));
  await page.route("**/api/auth/me", route => route.fulfill({ json: {
    staff: { id: "staff-move", display_name: "Operador de teste" }, venue: { id: "venue-move", slug: "test", name: "Estabelecimento de teste" },
    membership: { id: "membership-move", role: "STAFF", status: "ACTIVE", version: 1 }, capabilities: ["tab.move", "table.manage"],
    session: { id: state.session, access_expires_at: "2026-10-09T08:00:00Z", expires_at: "2026-10-09T08:00:00Z" }, device: null,
  } }));
  const detail = () => ({ id: tabId, display_label: "Comanda móvel", state: "OPEN", version: state.moved ? 2 : 1, exposure_cents: 900, payable_cents: 1000, charges_cents: 1000, payments_cents: 100, orders: [], payments: [], refund_required_corrections: [] });
  await page.route("**/api/attendance/tabs/?*", route => route.fulfill({ json: { results: [detail()], next_offset: null } }));
  await page.route(/\/api\/attendance\/tabs\/11111111[^/]*\/(\?.*)?$/, route => {
    const context = new URL(route.request().url()).searchParams.has("table_id");
    if (context && state.contextError) return route.fulfill({ status: 409, json: { code: "TABLE_CONTEXT_CHANGED", message: "O vínculo mudou. Atualize as mesas." } });
    if (!context && state.failReadback) return route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Leitura indisponível." } });
    return route.fulfill({ json: detail() });
  });
  await page.route("**/api/attendance/hospitality/tables/", route => route.fulfill({ json: { results: [
    { id: a, label: "A", status: "OCCUPIED", active_occupancy: { id: oa, tabs: state.moved ? [] : [detail()] } },
    { id: b, label: "B", status: "OCCUPIED", active_occupancy: { id: ob, tabs: state.moved ? [detail()] : [] } },
    { id: "66666666-6666-4666-8666-666666666666", label: "C", status: "AVAILABLE" },
  ] } }));
  return state;
}
async function open(page: Page) {
  await page.goto("/attendance"); await stable(page);
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByRole("button", { name: `Mover comanda Comanda móvel · ID ${tabId}`, exact: true }).click();
  await expect(page.getByLabel("Mesa de destino")).toBeEnabled();
}
const result = { operation_id: operationId, source: { id: tabId, version: 2, occupancy_id: ob } };
for (const width of [360,390,430]) {
  test(`location move confirms explicit destination and preserves draft at ${width}`, async ({ page }) => {
    await page.setViewportSize({width,height:900}); const state = await setup(page); const requests: string[] = [];
    await page.route(`**/api/attendance/tabs/${tabId}/operations/`, route => { requests.push(route.request().postData()!); state.moved = true; return route.fulfill({json:result}); });
    await open(page); const dialog = page.getByRole("dialog"); await layoutAndA11y(page);
    expect(await page.getByLabel("Mesa de destino").locator("option").allTextContents()).toEqual(["Escolha outra mesa ocupada", "Mesa B"]);
    await dialog.getByRole("button", {name:"Voltar",exact:true}).click(); expect(requests).toHaveLength(0);
    await page.getByRole("button", {name:`Abrir comanda Comanda móvel · ID ${tabId}`,exact:true}).click();
    await page.getByRole("button", {name:/^Fritas/}).click();
    await page.getByRole("button", {name:"Voltar à mesa A",exact:true}).click();
    await page.getByRole("button", {name:`Mover comanda Comanda móvel · ID ${tabId}`,exact:true}).click();
    await expect(page.getByLabel("Mesa de destino")).toBeEnabled(); await page.getByLabel("Mesa de destino").selectOption(ob); await page.getByLabel("Motivo (opcional)").fill("Mudança de lugar");
    await page.getByRole("button", {name:"Confirmar movimento",exact:true}).evaluate(button => { (button as HTMLButtonElement).click(); (button as HTMLButtonElement).click(); });
    await expect(page.getByText("Movimento confirmado. Local atual: mesa B.",{exact:true})).toBeVisible();
    expect(requests).toHaveLength(1); expect(JSON.parse(requests[0])).toMatchObject({kind:"MOVE_LOCATION",expected_version:1,occupancy_id:ob,reason:"Mudança de lugar"});
    await page.getByRole("button", {name:"Contas",exact:true}).click(); await expect(page.getByText("1× Fritas",{exact:true})).toBeVisible();
    expect(await page.evaluate(key => sessionStorage.getItem(key),storage)).toBeNull(); await layoutAndA11y(page);
  });
  test(`ambiguous location move recovers after reload with exact payload at ${width}`, async ({ page }) => {
    await page.setViewportSize({width,height:900}); const state = await setup(page); const requests: string[] = [];
    await page.route(`**/api/attendance/tabs/${tabId}/operations/`, route => { requests.push(route.request().postData()!); state.moved=true; return requests.length === 1 ? route.abort() : route.fulfill({json:result}); });
    await open(page); await page.getByLabel("Mesa de destino").selectOption(ob); await page.getByRole("button", {name:"Confirmar movimento",exact:true}).click();
    await expect(page.getByRole("button", {name:"Verificar mesmo movimento",exact:true})).toBeEnabled();
    await expect(page.getByRole("button", {name:"Mesas",exact:true})).toBeDisabled(); await expect(page.getByRole("button", {name:"Sair",exact:true})).toBeDisabled();
    await page.keyboard.press("Escape"); await expect(page.getByRole("dialog")).toBeVisible();
    await page.reload(); await stable(page); await expect(page.getByRole("button", {name:"Verificar mesmo movimento",exact:true})).toBeEnabled(); expect(requests).toHaveLength(1);
    state.failReadback=true; await page.getByRole("button", {name:"Verificar mesmo movimento",exact:true}).click(); await expect(page.getByText(/Resultado ainda não confirmado/)).toBeVisible();
    expect(await page.evaluate(key => sessionStorage.getItem(key),storage)).not.toBeNull();
    state.failReadback=false; await page.getByRole("button", {name:"Verificar mesmo movimento",exact:true}).click(); await expect(page.getByText("Movimento confirmado. Local atual: mesa B.",{exact:true})).toBeVisible();
    expect(requests).toHaveLength(3); expect(new Set(requests).size).toBe(1); await layoutAndA11y(page);
  });
}
test("changed session does not adopt location intent", async ({page}) => {
  const state=await setup(page); let posts=0;
  await page.route(`**/api/attendance/tabs/${tabId}/operations/`,route => { posts++; return route.abort(); });
  await open(page); await page.getByLabel("Mesa de destino").selectOption(ob); await page.getByRole("button",{name:"Confirmar movimento",exact:true}).click();
  await expect(page.getByRole("button",{name:"Verificar mesmo movimento",exact:true})).toBeEnabled(); state.session="other-session";
  await page.getByRole("button",{name:"Verificar mesmo movimento",exact:true}).click(); await expect(page.getByText(/Este movimento pertence à sessão original/)).toBeVisible(); expect(posts).toBe(1);
});
test("storage failure prevents a location POST", async ({page}) => {
  await setup(page); let posts=0; await page.route(`**/api/attendance/tabs/${tabId}/operations/`,route => { posts++; return route.abort(); });
  await open(page); await page.getByLabel("Mesa de destino").selectOption(ob);
  await page.evaluate(() => { const original=Storage.prototype.setItem; Storage.prototype.setItem=function(key,value) { if(key==="rodada.intent.tab-location.v1") throw new Error("Unavailable"); return original.call(this,key,value); }; });
  await page.getByRole("button",{name:"Confirmar movimento",exact:true}).click(); await expect(page.getByText(/Não foi possível preparar o movimento/)).toBeVisible(); expect(posts).toBe(0);
});
test("stale origin cannot reach confirmation", async ({page}) => {
  const state=await setup(page); state.contextError=true;
  await page.goto("/attendance"); await stable(page); await page.getByRole("button",{name:"Mesas",exact:true}).click();
  await page.getByRole("button",{name:`Mover comanda Comanda móvel · ID ${tabId}`,exact:true}).click();
  await expect(page.getByText("O vínculo mudou. Atualize as mesas.",{exact:true})).toBeVisible(); await expect(page.getByRole("button",{name:"Confirmar movimento",exact:true})).toBeDisabled();
});

test("definitive first rejection clears intent and requires a reviewed new choice", async ({page}) => {
  const state=await setup(page); const requests:string[]=[];
  await page.route(`**/api/attendance/tabs/${tabId}/operations/`,route=> {
    requests.push(route.request().postData()!);
    if(requests.length===1) return route.fulfill({status:409,json:{code:"OCCUPANCY_NOT_ACTIVE",message:"Destino não está ativo."}});
    state.moved=true; return route.fulfill({json:result});
  });
  await open(page); await page.getByLabel("Mesa de destino").selectOption(ob); await page.getByRole("button",{name:"Confirmar movimento",exact:true}).click();
  await expect(page.getByText("Destino não está ativo.",{exact:true})).toBeVisible();
  expect(await page.evaluate(key=>sessionStorage.getItem(key),storage)).toBeNull(); await expect(page.getByRole("button",{name:"Confirmar movimento",exact:true})).toBeDisabled();
  await page.getByRole("dialog").getByRole("button",{name:"Voltar",exact:true}).click();
  await page.getByRole("button",{name:`Mover comanda Comanda móvel · ID ${tabId}`,exact:true}).click(); await expect(page.getByLabel("Mesa de destino")).toBeEnabled();
  await page.getByLabel("Mesa de destino").selectOption(ob); await page.getByRole("button",{name:"Confirmar movimento",exact:true}).click();
  await expect(page.getByText("Movimento confirmado. Local atual: mesa B.",{exact:true})).toBeVisible();
  expect(requests).toHaveLength(2); expect(JSON.parse(requests[0]).idempotency_key).not.toBe(JSON.parse(requests[1]).idempotency_key);
});

test("rejected replay keeps original intent frozen", async ({page}) => {
  await setup(page); let posts=0;
  await page.route(`**/api/attendance/tabs/${tabId}/operations/`,route=> ++posts===1 ? route.abort() : route.fulfill({status:409,json:{code:"OCCUPANCY_NOT_ACTIVE",message:"Destino não está ativo."}}));
  await open(page); await page.getByLabel("Mesa de destino").selectOption(ob); await page.getByRole("button",{name:"Confirmar movimento",exact:true}).click();
  await expect(page.getByRole("button",{name:"Verificar mesmo movimento",exact:true})).toBeEnabled();
  const saved=await page.evaluate(key=>sessionStorage.getItem(key),storage);
  await page.getByRole("button",{name:"Verificar mesmo movimento",exact:true}).click(); await expect(page.getByText("Destino não está ativo.",{exact:true})).toBeVisible();
  expect(await page.evaluate(key=>sessionStorage.getItem(key),storage)).toBe(saved); await expect(page.getByRole("dialog").getByRole("button",{name:"Voltar",exact:true})).toBeDisabled();
});

test("corrupt persisted movement prevents sending and operational navigation", async ({page}) => {
  await setup(page); await page.addInitScript(key=>sessionStorage.setItem(key,'{"schema":1}'),storage);
  await page.goto("/attendance"); await expect(page.getByText(/Não foi possível preservar o movimento/)).toBeVisible();
  await expect(page.getByRole("button",{name:"Contas",exact:true})).toBeDisabled(); await expect(page.getByRole("button",{name:"Sair",exact:true})).toBeDisabled();
});

test("completed replay reports current unassigned location without recreating assignment", async ({page}) => {
  const state=await setup(page); let posts=0;
  await page.route(`**/api/attendance/tabs/${tabId}/operations/`,route=> { state.moved=true; return ++posts===1 ? route.abort() : route.fulfill({json:result}); });
  await open(page); await page.getByLabel("Mesa de destino").selectOption(ob); await page.getByRole("button",{name:"Confirmar movimento",exact:true}).click();
  await expect(page.getByRole("button",{name:"Verificar mesmo movimento",exact:true})).toBeEnabled();
  await page.route("**/api/attendance/hospitality/tables/",route=>route.fulfill({json:{results:[{id:a,label:"A",status:"OCCUPIED",active_occupancy:{id:oa,tabs:[]}},{id:b,label:"B",status:"DIRTY"}]}}));
  await page.getByRole("button",{name:"Verificar mesmo movimento",exact:true}).click(); await expect(page.getByText("Movimento confirmado. Local atual: sem mesa ativa.",{exact:true})).toBeVisible(); expect(posts).toBe(2);
});
