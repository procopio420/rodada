const {chromium}=require('../apps/web/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const out=path.resolve(__dirname,'../docs/design/evidence/android-visual-audit-2026-10-13');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1760,height:1060},locale:'pt-BR',timezoneId:'America/Sao_Paulo'});
 const meta=[];
 async function capture(name,locator,source,steps){await page.evaluate(()=>document.fonts.ready); await locator.screenshot({path:path.join(out,name+'.png'),animations:'disabled'});meta.push({file:name+'.png',source,steps,viewport:page.viewportSize(),bounds:await locator.boundingBox(),text:await locator.innerText(),inspected:false});console.log('CAPTURE',name);}
 for(const [id,entry,selector] of [['night','night/Main.dc.html','.phone'],['peak','peak/Pico.dc.html','.ph'],['connectivity','connectivity/Offline.dc.html','.ph'],['system','system/Sistema.dc.html','.ds'],['kitchen','kitchen/Cozinha.dc.html','.k']]){
   await page.goto('http://127.0.0.1:13121/prototype/references/'+entry); await page.waitForTimeout(700);
   if(id==='night'){
    const steps=page.locator('.rail .step');console.log('REFERENCE STEPS',await steps.allTextContents());
    for(const i of [0,1,2,3,4,5,6]){await steps.nth(i).click();await page.waitForTimeout(250);await capture('ref-night-'+i,page.locator(selector).first(),entry,'rail .step '+(i+1));}
   }else{for(let i=0;i<Math.min(await page.locator(selector).count(),3);i++)await capture('ref-'+id+'-'+i,page.locator(selector).nth(i),entry,'literal export instance '+i);}
 }
 await page.goto('http://127.0.0.1:13121/prototype/index.html'); await capture('ref-legacy',page.locator('body'),'prototype/index.html','initial');
 await page.setViewportSize({width:390,height:844}); await page.goto('http://localhost:13120/attendance');
 const auth=JSON.parse(fs.readFileSync(path.join(__dirname,'login.json')));
 await page.getByLabel('Estabelecimento').fill(auth.venue_slug);await page.getByLabel('Operador').fill(auth.login_identifier);await page.getByLabel('PIN',{exact:true}).fill(auth.pin);await page.getByRole('button',{name:'Entrar',exact:true}).click();
 await page.getByRole('button',{name:'Mesas',exact:true}).waitFor({timeout:60000}); await capture('web-agora-390',page.locator('body'),'Atendimento Web API real','login fictício');
 await page.getByRole('button',{name:'Mesas',exact:true}).click();await capture('web-mesas-390',page.locator('body'),'Atendimento Web API real','Mesas');
 console.log('WEB TEXT',await page.locator('body').innerText());
 await page.getByRole('button',{name:'Contas',exact:true}).click(); await capture('web-contas-390',page.locator('body'),'Atendimento Web API real','Contas');
 fs.writeFileSync(path.join(out,'browser-captures.json'),JSON.stringify(meta,null,2));await browser.close();
})().catch(e=>{console.error(e.message);process.exitCode=1});
