import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for(const width of [360,390,430]) test(`Gerência reveals one section and returns through browser history at ${width}`,async({page})=>{
  await page.setViewportSize({width,height:844});await fixture(page);await page.goto("/manage");
  await expect(page.getByRole("heading",{name:"Agora",exact:true})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Conta da casa",exact:true})).toHaveCount(0);
  await expect(page.getByLabel("Produto",{exact:true})).toHaveCount(0);
  await page.getByText("Ver mais do resumo",{exact:true}).click();
  await expect(page.getByText("Itens indisponíveis",{exact:true})).toBeVisible();
  await page.getByRole("navigation").getByRole("link",{name:"Operação",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Produção e entrega"})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Agora",exact:true})).toHaveCount(0);
  await page.getByRole("navigation").getByRole("link",{name:"Mais",exact:true}).click();
  await page.getByRole("link",{name:"Cardápio e nomes dos produtos",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Cardápio",exact:true}).first()).toBeVisible();
  await page.getByRole("link",{name:"Voltar à Gerência →",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Cadastros e configurações"})).toBeVisible();
  await page.goBack();await expect(page.getByRole("heading",{name:"Cardápio",exact:true}).first()).toBeVisible();
  await page.goForward();await expect(page.getByRole("heading",{name:"Cadastros e configurações"})).toBeVisible();
  await layoutAndA11y(page);
});

test("DEV lost create response preserves exact intent and reauthenticates on retry",async({page})=>{
  await fixture(page,"normal",true);
  await page.route("**/api/auth/me",route=>route.fulfill({json:{staff:{id:"owner",display_name:"Owner"},venue:{id:"venue",slug:"web-test",name:"Test"},membership:{id:"m",role:"OWNER",status:"ACTIVE",version:1},capabilities:["staff.manage"],session:{id:"s",expires_at:"2026-10-09T08:00:00Z",access_expires_at:"2026-10-08T21:15:00Z"},device:null}}));
  const payloads: unknown[]=[];
  await page.route("**/api/pos/developer/staff/",async route=>{
    if(route.request().method()==="GET")return route.fulfill({json:{results:[]}});
    payloads.push(route.request().postDataJSON());
    if(payloads.length===1)return route.abort("failed");
    return route.fulfill({status:201,json:{id:"new",staff:{id:"new-staff",display_name:"Local operator",login_identifier:"local.operator"},role:"STAFF",status:"ACTIVE",version:1}});
  });
  await page.goto("/dev/staff");await expect(page.getByRole("heading",{name:"Administrar equipe"})).toBeVisible();
  await page.getByLabel("Nome do operador").fill("Local operator");await page.getByLabel("Login do novo operador").fill("local.operator");await page.getByLabel("PIN do novo operador").fill("7319");await page.getByLabel("Seu PIN para confirmar").fill("2468");await page.getByRole("button",{name:"Criar operador",exact:true}).click();
  await expect(page.getByRole("button",{name:"Criar operador",exact:true})).toBeDisabled();
  await expect(page.getByLabel("Nome do operador")).toBeDisabled();
  await page.getByLabel("Seu PIN para confirmar").fill("2468");await page.getByRole("button",{name:"Verificar mesma tentativa"}).click();
  await expect(page.getByText("Alteração confirmada. A lista mostra o estado atual.")).toBeVisible();
  expect(payloads).toHaveLength(2);expect(payloads[1]).toEqual(payloads[0]);
  await expect(page.getByLabel("PIN do novo operador")).toHaveValue("");
  await layoutAndA11y(page);
});

for (const width of [360, 390, 430]) test(`DEV existing staff and edit controls remain accessible at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "owner", display_name: "Owner" }, venue: { id: "venue", slug: "web-test", name: "Test" }, membership: { id: "m", role: "OWNER", status: "ACTIVE", version: 1 }, capabilities: ["staff.manage"], session: { id: "s", expires_at: "2026-10-09T08:00:00Z", access_expires_at: "2026-10-08T21:15:00Z" }, device: null } }));
  const longName = "Operador com nome completo muito longo para testar leitura na equipe";
  await page.route("**/api/pos/developer/staff/", route => route.fulfill({ json: { results: [{ id: "member", staff: { id: "operator", display_name: longName, login_identifier: "operator." + "x".repeat(100) }, role: "STAFF", status: "ACTIVE", version: 1 }] } }));
  await page.goto("/dev/staff");
  await page.getByRole("button", { name: `Gerenciar ${longName}`, exact: true }).click();
  await expect(page.getByLabel("Função", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Remover acesso", exact: true }).click();
  await expect(page.getByRole("button", { name: "Confirmar remoção do acesso" })).toBeDisabled();
  await layoutAndA11y(page);
});


test("catalog name lost response and failed read never confirm success or leave controls busy", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { capabilities: ["catalog.icon.manage"] } }));
  let reads = 0;
  await page.route("**/api/pos/catalog/products/", async route => {
    reads += 1;
    if (reads === 1) await route.fallback();
    else await route.abort("failed");
  });
  await page.route("**/api/pos/catalog/products/fries/", route => route.abort("failed"));
  await page.goto("/manage/products");
  await page.getByText("Editar produto e ícone", { exact: true }).click();
  await page.getByLabel("Produto", { exact: true }).selectOption("fries");
  await page.getByLabel("Nome do produto").fill("Fritas revisadas");
  await page.getByRole("button", { name: "Salvar nome" }).click();
  await expect(page.getByRole("status")).toContainText("Resultado não confirmado; não foi possível consultar o produto.");
  await expect(page.getByRole("button", { name: "Salvar nome" })).toBeEnabled();
  await expect(page.getByText("Nome confirmado. Pedidos anteriores conservam seu histórico.")).toHaveCount(0);
});
