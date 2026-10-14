const {chromium}=require('../apps/web/node_modules/playwright');const fs=require('fs'),path=require('path');
const out=path.resolve(__dirname,'../docs/design/evidence/android-visual-audit-2026-10-13');
(async()=>{
const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844},locale:'pt-BR'});const auth=JSON.parse(fs.readFileSync(path.join(__dirname,'login.json')));const log=[];
await p.goto('http://localhost:13120/attendance');await p.getByLabel('Estabelecimento').fill(auth.venue_slug);await p.getByLabel('Operador').fill(auth.login_identifier);await p.getByLabel('PIN',{exact:true}).fill(auth.pin);await p.getByRole('button',{name:'Entrar',exact:true}).click();await p.getByText(/Atualizado às/).waitFor({timeout:60000});
async function cap(n){await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:path.join(out,n+'.png'),fullPage:true});log.push({file:n+'.png',text:await p.locator('body').innerText(),viewport:p.viewportSize(),fixture:'audit-aderlan-v1',api:'real PostgreSQL',inspected:false});console.log('CAPTURE',n);fs.writeFileSync(path.join(out,'web-real.json'),JSON.stringify(log,null,2));}
await cap('web-agora-loaded-390');await p.getByRole('button',{name:'Mesas',exact:true}).click();await p.getByRole('button',{name:'Organizar mesa 01',exact:true}).waitFor();await p.getByText(/Atualizado às/).waitFor();await cap('web-mesas-loaded-390');
await p.getByRole('button',{name:'Organizar mesa 01',exact:true}).click();await cap('web-multicomanda-390');console.log('DIALOG',await p.getByRole('dialog').innerText());await p.getByRole('dialog').getByRole('button',{name:'Voltar',exact:true}).click();
await p.getByRole('button',{name:'Contas',exact:true}).click();await p.getByText(/Atualizado às/).waitFor();await p.getByRole('button',{name:/Rodadas · demonstração/}).click();await p.getByLabel('Buscar item no cardápio').fill('Água');await p.getByRole('button',{name:/Água mineral/}).first().waitFor();await cap('web-comanda-loaded-390');console.log('WORKSPACE',await p.locator('body').innerText());
await p.getByRole('button',{name:/Água mineral/}).first().click();await cap('web-draft-390');await p.getByRole('region',{name:'Pedido atual'}).getByRole('button',{name:'Editar',exact:true}).click();await cap('web-nota-produto-simples-390');
await b.close();
})().catch(e=>{console.error(e.message);process.exitCode=1});
