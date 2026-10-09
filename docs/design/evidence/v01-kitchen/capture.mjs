import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=process.cwd(),out=path.join(root,'docs/design/evidence/v01-kitchen');
const require=createRequire(path.join(root,'apps/web/package.json'));
const {chromium,expect}=require('@playwright/test');
const refBase=process.env.V01_REFERENCE_URL??'http://127.0.0.1:9123';
const appBase=process.env.V01_APP_URL??'http://127.0.0.1:9124';
const sha=b=>createHash('sha256').update(b).digest('hex');
await mkdir(out,{recursive:true});
const manifest=JSON.parse(await readFile(path.join(root,'prototype/references/manifest.json'))).find(x=>x.id==='kitchen');
const sources=[`prototype/${manifest.archive}`,'prototype/references/kitchen/Cozinha.dc.html','prototype/references/kitchen/support.js','prototype/references/kitchen/vendor/react.js','prototype/references/kitchen/vendor/react-dom.js','prototype/fonts/fonts.css','prototype/fonts/Archivo.ttf','prototype/fonts/JetBrainsMono.ttf'];
for(const asset of await readdir(path.join(root,'prototype/references/kitchen/assets')))sources.push('prototype/references/kitchen/assets/'+asset);
const sourceHashes={};for(const f of sources)sourceHashes[f]=sha(await readFile(path.join(root,f)));
expect(sourceHashes[`prototype/${manifest.archive}`]).toBe(manifest.sha256);
const browser=await chromium.launch();
const context=await browser.newContext({viewport:{width:1280,height:800},deviceScaleFactor:1,locale:'pt-BR',timezoneId:'America/Sao_Paulo',colorScheme:'dark',reducedMotion:'reduce'});
const reference=await context.newPage(), errors=[];reference.on('pageerror',e=>errors.push(e.message));reference.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
async function stable(p){await p.evaluate(()=>document.fonts.ready);await expect.poll(()=>p.locator('img').evaluateAll(xs=>xs.every(x=>x.complete&&x.naturalWidth>0))).toBe(true)}
async function measure(p,map){const result={};for(const [id,selector] of Object.entries(map)){const loc=p.locator(selector);expect(await loc.count(),selector).toBe(1);result[id]=await loc.evaluate(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {box:{x:r.x,y:r.y,width:r.width,height:r.height},text:e.innerText,style:Object.fromEntries(['display','gridTemplateColumns','gridTemplateRows','padding','gap','borderRightWidth','borderBottomWidth','backgroundColor','color','fontFamily','fontSize','fontWeight','fontStretch','fontVariationSettings','lineHeight','letterSpacing','textTransform','borderRadius','boxShadow','overflow'].map(k=>[k,s[k]]))}});result[id].selector=selector;}return result;}
const refSelectors={root:'.k',header:'.k > header',summary:'.k > section:nth-of-type(1)',tickets:'.k > section:nth-of-type(2)',pass:'.k > section:nth-of-type(3)',firstDish:'.dish:nth-of-type(2)',firstTicket:'.tk:nth-of-type(2)',firstAction:'.tk:nth-of-type(2) .btn',firstPass:'.pass:nth-of-type(2)',dishName:'.dish:nth-of-type(2) .n',quantity:'.dish:nth-of-type(2) .q',chip:'.dish:nth-of-type(2) .chip:nth-of-type(1)',headerTitle:'.k > header > div:nth-of-type(1) > b',ticketName:'.tk:nth-of-type(2) .i',ticketMeta:'.tk:nth-of-type(2) .a',passUnclaimed:'.pass:nth-of-type(2) .w',passWaiting:'.pass:nth-of-type(3) .w',passTaken:'.pass:nth-of-type(4)',newBadge:'.tk:nth-of-type(6) .i > span'};
await reference.goto(refBase+'/prototype/references/kitchen/Cozinha.dc.html');await stable(reference);expect(await reference.locator('.k').count()).toBe(1);
const refMeasures=await measure(reference,refSelectors);
const fontStatus=await reference.evaluate(()=>({archivo:document.fonts.check('900 44px Archivo'),mono:document.fonts.check('800 52px "JetBrains Mono"'),faces:[...document.fonts].map(f=>({family:f.family,status:f.status,weight:f.weight,stretch:f.stretch}))}));
const initialHTML=await reference.locator('.k').innerHTML(),initialImage=await reference.locator('.k').screenshot({path:path.join(out,'reference-initial-1280.png')});
for(const id of ['header','summary','tickets','pass'])await reference.locator(refSelectors[id]).screenshot({path:path.join(out,`reference-${id}.png`)});
const clicks=[];for(let i=0;i<5;i++){await reference.locator('.btn').nth(i).click();clicks.push({index:i+1,label:'Pronto',rootHTMLUnchanged:await reference.locator('.k').innerHTML()===initialHTML,urlUnchanged:reference.url()===refBase+'/prototype/references/kitchen/Cozinha.dc.html'});}
await reference.reload();await stable(reference);const repeated=await reference.locator('.k').screenshot();expect(sha(repeated)).toBe(sha(initialImage));
await reference.locator('.btn').first().focus();await reference.locator('.k').screenshot({path:path.join(out,'reference-focus-1280.png')});
const focused=await reference.locator('.btn').first().evaluate(e=>({outline:getComputedStyle(e).outline,focused:document.activeElement===e}));
const clock='2026-10-08T21:00:00Z';
const tuples=[['Bolinho de bacalhau',2,'P22 · Galera da 22',790],['Fritas',1,'P08 · Renata',562],['Calabresa',1,'P08 · Renata',562],['Fritas',2,'P25 · Turma do Vasco',375],['Calabresa',1,'P41 · Carlos Mecânico',250],['Fritas',1,'P37 · João da Oficina',31]];
const queue=tuples.map(([product_name,quantity,tab_label,seconds],i)=>({id:`reference-${i}`,product_name,quantity,tab_label,state:'PREPARING',created_at:new Date(Date.parse(clock)-seconds*1000).toISOString()}));
for(const [i,[product_name,tab_label,seconds]]of [['Calabresa','P12',220],['Bolinho','B4',80],['Torresmo','P44',30]].entries())queue.push({id:`pass-${i}`,product_name,quantity:1,tab_label,state:'READY',created_at:'2026-10-08T20:45:00Z',ready_at:new Date(Date.parse(clock)-seconds*1000).toISOString()});
const catalog=[{id:'fries-test',name:'Fritas',price_cents:7200,fulfillment_station:'KITCHEN',availability:'AVAILABLE'},{id:'omelette-test',name:'Omelete',price_cents:1800,fulfillment_station:'KITCHEN',availability:'UNAVAILABLE'}];
await writeFile(path.join(out,'inspection-fixture.json'),JSON.stringify({id:'kitchen-main-inspection-v1',clock,queue,catalog,notes:['API intercepted in browser; no database writes.','Split P08 into two OrderItem lines.','P44 rendered READY for layout inspection; reference ownership not reproduced.','Literal summary/metadata are not normalized or claimed equivalent.']},null,2)+'\n');
const actual=await context.newPage(),actualErrors=[];actual.on('pageerror',e=>actualErrors.push(e.message));await actual.clock.install({time:new Date(clock)});await actual.clock.pauseAt(new Date(clock));
let mode='initial',reads=0,posts=[];
await actual.route('**/api/**',async route=>{const u=new URL(route.request().url());if(u.pathname==='/api/auth/me')return route.fulfill({json:{capabilities:['catalog.product.create'],session:{id:'inventory-only'},venue:{id:'inventory-only'},staff:{id:'inventory-only'}}});if(u.pathname.startsWith('/api/auth/'))return route.fulfill({json:{cursor:0,results:[]}});
 if(route.request().method()==='POST'){posts.push(route.request().postDataJSON());if(mode==='saving')return;return route.fulfill({status:503,json:{code:'UPSTREAM_UNAVAILABLE',message:'Estado não confirmado'}})}
 if(mode==='loading')return;
 if(mode==='error'||mode==='stale')return route.fulfill({status:503,json:{code:'UPSTREAM_UNAVAILABLE',message:'Sem resposta na inspeção visual'}});
 let items=queue;if(mode==='empty')items=[];if(mode==='missing-time')items=[{...queue[0],state:'NEW'},{...queue[1],state:'ACCEPTED'},{...queue[6],ready_at:null},{...queue[7],state:'PICKED_UP'}];
 if(u.pathname.startsWith('/api/pos/production/')){reads++;return route.fulfill({json:{results:items}})}
 if(u.pathname==='/api/pos/catalog/products/')return route.fulfill({json:{results:mode==='empty'?[]:catalog}});
 throw new Error('Unmapped fixture '+u.pathname);
});
const actualSelectors={root:'main.productionShell',header:'.productHeader',workspace:'.productionWorkspace',summary:'.productionSummary',tickets:'section[aria-labelledby="queue-title"]',pass:'section[aria-labelledby="ready-title"]',firstAction:'section[aria-labelledby="queue-title"] article:first-of-type button',availability:'section[aria-labelledby="availability-title"]'};
const observations={};
async function capture(state){await stable(actual);await actual.screenshot({path:path.join(out,`main-${state}-1280.png`),fullPage:true});observations[state]={text:await actual.locator('main').innerText(),controls:await actual.locator('main button').evaluateAll(es=>es.map(e=>({label:e.getAttribute('aria-label')??e.innerText,disabled:e.disabled}))),scroll:await actual.evaluate(()=>({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,viewportWidth:innerWidth,viewportHeight:innerHeight}))};}
await actual.goto(appBase+'/kitchen');await expect(actual.getByRole('button',{name:'Pronto: 2 Bolinho de bacalhau, P22 · Galera da 22',exact:true})).toBeVisible();await expect(actual.getByRole('button',{name:'+ Item',exact:true})).toBeVisible();await capture('initial');const actualMeasures=await measure(actual,actualSelectors);
await actual.locator('.productionWorkspace').screenshot({path:path.join(out,'main-workspace-1280.png')});
await actual.reload();await expect(actual.locator('[aria-busy=true]')).toHaveCount(0);await stable(actual);const repeatedMain=await actual.screenshot({fullPage:true});const initialMain=await readFile(path.join(out,'main-initial-1280.png'));expect(sha(repeatedMain)).toBe(sha(initialMain));
mode='saving';await actual.getByRole('button',{name:'Pronto: 2 Bolinho de bacalhau, P22 · Galera da 22',exact:true}).click();await expect(actual.getByText('Salvando…')).toBeVisible();await capture('saving');
await actual.reload();mode='initial';// reload request remains saving but reads are successful; no new command.
await expect(actual.getByRole('button',{name:'Pronto: 2 Bolinho de bacalhau, P22 · Galera da 22',exact:true})).toBeVisible();mode='stale';await actual.clock.runFor(5000);await expect(actual.locator('main .notice[role=alert]')).toContainText('Último estado confirmado');await capture('stale');
for(const state of ['empty','loading','error','missing-time']){mode=state;await actual.reload();if(state==='loading')await expect(actual.getByText('Carregando fila…')).toBeVisible();else if(state==='error')await expect(actual.locator('main .notice[role=alert]')).toBeVisible();else await expect(actual.locator('[aria-busy=true]')).toHaveCount(0);await capture(state);}
await actual.clock.setFixedTime(new Date(clock));
const responsive={};for(const width of [360,430,768]){await reference.setViewportSize({width,height:800});responsive[width]={referenceRoot:await reference.locator('.k').boundingBox(),referenceScrollWidth:await reference.evaluate(()=>document.documentElement.scrollWidth)};mode='initial';await actual.setViewportSize({width,height:800});await actual.reload();await expect(actual.locator('[aria-busy=true]')).toHaveCount(0);await stable(actual);responsive[width].main=await measure(actual,{root:actualSelectors.root,workspace:actualSelectors.workspace});responsive[width].mainScrollWidth=await actual.evaluate(()=>document.documentElement.scrollWidth);await actual.screenshot({path:path.join(out,`main-initial-${width}.png`),fullPage:true});}
const result={scope:'V01 kitchen only; inventory, not parity acceptance',baseCommit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),environment:{os:process.platform,node:process.version,playwright:require('@playwright/test/package.json').version,chromium:browser.version(),viewport:{width:1280,height:800},dpr:1,locale:'pt-BR',timezone:'America/Sao_Paulo',build:'Next webpack; shared unchanged node_modules'},manifest,sourceHashes,reference:{fontStatus,measures:refMeasures,clicks,focused,repeatCaptureHash:sha(repeated),renderErrors:errors},implementation:{renderErrors:actualErrors,repeatCaptureHash:sha(repeatedMain),fixture:'inspection-fixture.json',measures:actualMeasures,states:observations,interceptedPosts:posts,reads},responsive};
expect(actualErrors).toEqual([]);
await writeFile(path.join(out,'measurements.json'),JSON.stringify(result,null,2)+'\n');await browser.close();console.log(JSON.stringify({base:result.baseCommit,reference:refMeasures.root.box,actual:actualMeasures.root.box,unchangedClicks:clicks.every(x=>x.rootHTMLUnchanged),errors,states:Object.keys(observations),fontStatus,repeatVerified:true}));
