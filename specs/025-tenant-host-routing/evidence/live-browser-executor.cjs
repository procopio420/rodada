const {chromium,request}=require('../../../apps/web/node_modules/playwright');
let input='';process.stdin.on('data',b=>input+=b);process.stdin.on('end',()=>run(JSON.parse(input)).catch(()=>{process.stdout.write(JSON.stringify({all_pass:false,fatal:'sanitized execution failure; require rollback'}));process.exitCode=1;}));
async function run(p){
 const results=[],contexts={},guests={},rows={},tabs={},products={},cursors={};let browser;
 const profilePass=(k,rotated=false)=>require('node:crypto').createHmac('sha256',p.pins[k]).update('spec025-profile-'+(rotated?'new-':'')+p.run).digest('base64url');
 const profileUser=k=>'qa-profile-'+k+'-'+p.run;
 const check=(scenario,ok,extra={})=>{results.push({scenario,pass:!!ok,...extra});if(!ok)throw Error(scenario);};
 const host=k=>`https://e2e${k}.rodada.bar`;
 const call=async(ctx,k,path,method='GET',data,extra={})=>{const r=await ctx.request.fetch(host(k)+path,{method,data,headers:{...(method!=='GET'?{Origin:host(k)}:{}),...extra},timeout:25000});let d={};try{d=await r.json()}catch{}return {s:r.status(),d,r};};
 try{
 browser=await chromium.launch({headless:true,...(process.env.SPEC025_CHROMIUM_PATH?{executablePath:process.env.SPEC025_CHROMIUM_PATH}:{}),args:['--disable-dev-shm-usage']});
 for(const k of ['a','b']){
  const ctx=await browser.newContext({ignoreHTTPSErrors:false,viewport:{width:390,height:844}});contexts[k]=ctx;
  const page=await ctx.newPage();const errors=[];page.on('pageerror',()=>errors.push('pageerror'));
  let response=await page.goto(host(k)+'/staff',{waitUntil:'domcontentloaded',timeout:45000});check(k+'_browser_staff_https',response.status()===200);
  await page.getByLabel('Operador',{exact:true}).fill('spec025-qa-'+k+'-owner');await page.getByLabel('PIN',{exact:true}).fill(p.pins[k]);
  const loginWait=page.waitForResponse(r=>r.url()===host(k)+'/api/auth/login'&&r.request().method()==='POST');await page.getByRole('button',{name:'Entrar',exact:true}).click();const login=await loginWait;
  check(k+'_browser_UI_login',login.status()===200,{http_status:login.status()});
  let q=await call(ctx,k,'/api/auth/me');check(k+'_browser_identity',q.s===200&&q.d.venue?.id===p.ids[k]);
  const cookies=(await ctx.cookies(host(k))).filter(c=>c.name.startsWith('rodada_staff_'));
  check(k+'_staff_cookie_host_only_secure_httpOnly',cookies.length>=2&&cookies.every(c=>c.domain==='e2e'+k+'.rodada.bar'&&c.secure&&c.httpOnly&&c.sameSite==='Lax'));
  q=await call(ctx,k,'/manifest.webmanifest');check(k+'_manifest',q.s===200&&q.d.name==='Rodada — Spec025 QA '+k.toUpperCase()+' — test only'&&q.d.start_url==='/'&&q.d.scope==='/');
  q=await call(ctx,k,'/api/pos/management/guest-policy');check(k+'_guest_policy_read',q.s===200);
  q=await call(ctx,k,'/api/pos/management/guest-policy','PATCH',{blocked:false,expected_version:q.d.version,reason:'Spec025 controlled QA-only HTTPS verification'});check(k+'_enable_QA_guest_only',q.s===200);
  q=await call(ctx,k,'/api/pos/hospitality/tables/','POST',{label:'QA HTTPS '+k.toUpperCase()+' '+p.run,guest_ordering_mode:'DIRECT'});check(k+'_create_QA_table',q.s===201);rows[k]=q.d;
  q=await call(ctx,k,'/api/pos/hospitality/tables/','POST',{label:'QA group peer '+k.toUpperCase()+' '+p.run,guest_ordering_mode:'DISABLED'});check(k+'_create_QA_group_peer',q.s===201);rows[k].peerId=q.d.id;rows[k].peerLabel=q.d.label;
  const groupIntent={table_ids:[rows[k].id,rows[k].peerId],label:'QA physical group '+k.toUpperCase()+' '+p.run,request_key:require('node:crypto').randomUUID()};q=await call(ctx,k,'/api/pos/hospitality/table-groups/','POST',groupIntent);check(k+'_QA_physical_group_create',q.s===201&&q.d.active);rows[k].groupId=q.d.id;rows[k].groupLabel=q.d.label;const gr=await call(ctx,k,'/api/pos/hospitality/table-groups/','POST',groupIntent);check(k+'_group_idempotent_replay',gr.s===200&&gr.d.replayed===true&&gr.d.id===rows[k].groupId);
  q=await call(ctx,k,'/api/pos/catalog/resolve-or-create/','POST',{name:'QA HTTPS item '+k.toUpperCase()+' '+p.run,price_cents:100,fulfillment_station:'BAR'});check(k+'_create_catalog_definition_no_sale',q.s===201);products[k]=q.d.product;
  const again=await call(ctx,k,'/api/pos/catalog/resolve-or-create/','POST',{name:products[k].name,price_cents:100,fulfillment_station:'BAR'});check(k+'_catalog_resolve_retry_same_product',again.s===200&&again.d.product.id===products[k].id&&!again.d.created);
  const intent={idempotency_key:'spec025-live-service-'+p.run,display_label:'QA no-money '+k.toUpperCase()};
  q=await call(ctx,k,`/api/pos/hospitality/tables/${rows[k].id}/service/open-tab/`,'POST',intent);check(k+'_start_QA_service_no_order',q.s===201&&q.d.replayed===false);tabs[k]=q.d;
  const replay=await call(ctx,k,`/api/pos/hospitality/tables/${rows[k].id}/service/open-tab/`,'POST',intent);check(k+'_service_idempotency_retry',replay.s===200&&replay.d.replayed===true&&replay.d.tab_id===tabs[k].tab_id&&replay.d.occupancy_id===tabs[k].occupancy_id&&replay.d.table_id===tabs[k].table_id);
  q=await call(ctx,k,'/api/pos/hospitality/tables/');check(k+'_own_table_visible',q.s===200&&q.d.results.some(t=>t.id===rows[k].id));
  q=await call(ctx,k,'/api/realtime/snapshot');check(k+'_staff_snapshot',q.s===200);cursors[k]=q.d.cursor;
  q=await call(ctx,k,'/api/realtime/stream?once=1&cursor='+encodeURIComponent(cursors[k]));check(k+'_staff_SSE_ready',q.s===200&&(await q.r.text()).includes('event: ready'));
  const beforeRefresh=(await ctx.cookies(host(k))).find(c=>c.name==='rodada_staff_refresh')?.value;await ctx.clearCookies({name:'rodada_staff_access'});q=await call(ctx,k,'/api/auth/me');check(k+'_refresh_only_cookie',q.s===200&&q.d.venue?.id===p.ids[k]&&(await ctx.cookies(host(k))).find(c=>c.name==='rodada_staff_refresh')?.value!==beforeRefresh);
  q=await call(ctx,k,'/api/realtime/stream?once=1&cursor='+encodeURIComponent(cursors[k]));check(k+'_staff_SSE_reconnect',q.s===200&&(await q.r.text()).includes('event: ready'));
  const guest=await browser.newContext({ignoreHTTPSErrors:false});guests[k]=guest;const gp=await guest.newPage();gp.on('pageerror',()=>errors.push('guest-pageerror'));const qrWait=gp.waitForResponse(r=>r.url().includes('/api/guest/qr/resolve'),{timeout:25000});response=await gp.goto(host(k)+'/m/'+rows[k].public_token,{waitUntil:'domcontentloaded',timeout:45000});check(k+'_browser_guest_QR_page',response.status()===200);const qrBrowser=await qrWait;check(k+'_browser_guest_actual_QR_request',[200,201].includes(qrBrowser.status()));
  q=await call(guest,k,'/api/guest/qr/resolve','POST',{token:rows[k].public_token});check(k+'_guest_QR_resolve',q.s===200||q.s===201);
  check(k+'_guest_scope',q.d.session_scope?.venue_id===p.ids[k]);
  const gc=(await guest.cookies()).filter(c=>c.name.startsWith('rodada_guest_'));check(k+'_guest_host_only_secure_httpOnly',gc.length>=1&&gc.every(c=>c.domain==='e2e'+k+'.rodada.bar'&&c.secure&&c.httpOnly));
  q=await call(guest,k,'/api/guest/context','GET',undefined,{'X-Guest-Session':rows[k].public_token});check(k+'_guest_context',q.s===200&&q.d.session_scope?.venue_id===p.ids[k]);check(k+'_guest_group_only_own_physical_labels',q.d.table?.group?.label===rows[k].groupLabel&&JSON.stringify(Object.keys(q.d.table.group).sort())===JSON.stringify(['label','tables'])&&JSON.stringify([...q.d.table.group.tables].sort())===JSON.stringify([rows[k].label,rows[k].peerLabel].sort()));
  q=await call(guest,k,'/api/guest/realtime/snapshot','GET',undefined,{'X-Guest-Session':rows[k].public_token});check(k+'_guest_snapshot',q.s===200);rows[k].guestCursor=q.d.cursor;
  q=await call(guest,k,'/api/guest/realtime/stream?once=1&cursor='+encodeURIComponent(q.d.cursor),'GET',undefined,{'X-Guest-Session':rows[k].public_token});check(k+'_guest_SSE_ready',q.s===200&&(await q.r.text()).includes('event: ready'));
  const gh={'X-Guest-Session':rows[k].public_token};
  q=await call(guest,k,'/api/guest/tabs','POST',{display_label:'QA profile empty '+k.toUpperCase()},gh);check(k+'_guest_empty_Tab_create',q.s===201);rows[k].guestTabId=q.d.id;
  q=await call(guest,k,'/api/guest/tabs','POST',{display_label:'QA profile empty '+k.toUpperCase()},gh);check(k+'_guest_Tab_retry_same_ID',q.s===201&&q.d.id===rows[k].guestTabId);
  q=await call(guest,k,'/api/guest/customer/register','POST',{username:profileUser(k),password:profilePass(k),display_name:'Fictional QA profile '+k.toUpperCase()},gh);check(k+'_customer_enroll_no_token_in_body',q.s===201&&q.d.authenticated===true&&!('customer_auth_token' in q.d));
  const cc=(await guest.cookies(host(k))).filter(c=>c.name.startsWith('rodada_customer_'));check(k+'_customer_cookie_host_only_secure_httpOnly',cc.length===1&&cc.every(c=>c.domain==='e2e'+k+'.rodada.bar'&&c.secure&&c.httpOnly&&c.sameSite==='Lax'));
  q=await call(guest,k,'/api/guest/customer/context','GET',undefined,gh);check(k+'_own_customer_context',q.s===200&&q.d.authenticated===true&&q.d.display_name==='Fictional QA profile '+k.toUpperCase()&&q.d.linked_tab_id===rows[k].guestTabId);
  q=await call(guest,k,'/api/guest/customer/claim','POST',{target_tab_id:rows[k].guestTabId},gh);check(k+'_own_customer_Tab_claim',q.s===200&&q.d.tab_id===rows[k].guestTabId);
  const beforeRotate=(await guest.cookies(host(k))).map(c=>c.name+'='+c.value).join('; ');
  q=await call(guest,k,'/api/guest/customer/password','POST',{old_password:profilePass(k),new_password:profilePass(k,true)},gh);check(k+'_customer_password_rotate',q.s===200&&!('customer_auth_token' in q.d));
  const rp=await request.newContext();try{const old=await rp.get(host(k)+'/api/guest/customer/context',{headers:{Cookie:beforeRotate,...gh}});check(k+'_old_customer_cookie_after_rotate_denied',old.status()===401);}finally{await rp.dispose();}
  q=await call(guest,k,'/api/guest/customer/login','POST',{username:profileUser(k),password:profilePass(k)},gh);check(k+'_old_profile_password_denied',q.s===401);
  q=await call(guest,k,'/api/guest/customer/login','POST',{username:profileUser(k),password:profilePass(k,true)},gh);check(k+'_rotated_profile_password_login',q.s===200&&q.d.authenticated===true&&!('customer_auth_token' in q.d));
  check(k+'_browser_no_uncaught_errors',errors.length===0);
 }
 const raw=await request.newContext({ignoreHTTPSErrors:false});
 for(const k of ['a','b']){
  const o=k==='a'?'b':'a',ctx=contexts[k],guest=guests[k];let q;
  const gh={'X-Guest-Session':rows[k].public_token};
  q=await call(guest,k,'/api/guest/customer/claim','POST',{target_tab_id:rows[o].guestTabId},gh);check(k+'_customer_foreign_Tab_claim_denied',q.s===404);
  q=await call(guest,k,'/api/guest/customer/login','POST',{username:profileUser(o),password:profilePass(o,true)},gh);check(k+'_foreign_customer_credentials_no_relationship_denied',q.s===403&&q.d.code==='CUSTOMER_NOT_IN_VENUE');
  const ownCookies=await guest.cookies(host(k)),foreignCustomer=(await guests[o].cookies(host(o))).find(c=>c.name.startsWith('rodada_customer_')),ownCustomer=ownCookies.find(c=>c.name.startsWith('rodada_customer_'));
  const wrongCustomer=ownCookies.map(c=>c.name+'='+(c.name===ownCustomer.name?foreignCustomer.value:c.value)).join('; ');let pr=await raw.get(host(k)+'/api/guest/customer/context',{headers:{Cookie:wrongCustomer,...gh}});let pd=await pr.json();check(k+'_foreign_customer_cookie_with_own_guest_denied',pr.status()===401&&!('display_name' in pd)&&!('claimable_tabs' in pd));
  pr=await raw.get(host(o)+'/api/guest/customer/context',{headers:{Cookie:ownCookies.map(c=>c.name+'='+c.value).join('; '),...gh}});pd=await pr.json();check(k+'_customer_and_guest_cross_host_denied',[403,404].includes(pr.status())&&!('display_name' in pd)&&!('claimable_tabs' in pd));
  q=await call(guest,k,'/api/guest/customer/context','GET',undefined,{...gh,'X-Customer-Session':foreignCustomer.value});check(k+'_external_customer_header_ignored',q.s===200&&q.d.display_name==='Fictional QA profile '+k.toUpperCase()&&q.d.linked_tab_id===rows[k].guestTabId&&!q.d.claimable_tabs.some(t=>t.id===rows[o].guestTabId));
  q=await call(ctx,k,'/api/pos/catalog/products/');check(k+'_catalog_no_foreign',q.s===200&&q.d.results.some(x=>x.id===products[k].id)&&!q.d.results.some(x=>x.id===products[o].id));
  q=await call(ctx,k,'/api/pos/hospitality/tables/');check(k+'_tables_no_foreign',q.s===200&&!q.d.results.some(x=>x.id===rows[o].id));
  const cookie=(await ctx.cookies(host(k))).map(c=>c.name+'='+c.value).join('; ');
  for(const path of ['/api/auth/me','/api/realtime/snapshot','/api/realtime/stream?once=1']){const r=await raw.get(host(o)+path,{headers:{Cookie:cookie}});const d=await r.json();check(k+'_session_on_'+o+path,r.status()===403&&d.code==='VENUE_HOST_MISMATCH');}
  let r=await raw.post(host(o)+'/api/pos/hospitality/tables/',{headers:{Origin:host(o),Cookie:cookie},data:{label:'FOREIGN-MUST-NOT-EXIST-'+p.run+'-'+k}});check(k+'_foreign_mutation_denied',r.status()===403);
  const refresh=(await ctx.cookies(host(k))).filter(c=>c.name==='rodada_staff_refresh').map(c=>c.name+'='+c.value).join('; ');r=await raw.get(host(o)+'/api/auth/me',{headers:{Cookie:refresh}});check(k+'_foreign_refresh_denied',r.status()===403);
  r=await raw.post(host(k)+'/api/auth/login',{headers:{Origin:host(k)},data:{venue_slug:'spec025-qa-'+o,login_identifier:'spec025-qa-'+o+'-owner',pin:p.pins[o]}});check(k+'_foreign_credentials_denied',r.status()===403);
  r=await raw.post(host(k)+'/api/auth/login',{headers:{Origin:host(o),'X-Forwarded-Host':'e2e'+o+'.rodada.bar'},data:{login_identifier:'spec025-qa-'+k+'-owner',pin:p.pins[k]}});check(k+'_cross_origin_login_denied',r.status()===403);
  q=await call(ctx,k,'/api/pos/hospitality/table-groups/');check(k+'_groups_no_foreign',q.s===200&&q.d.results.some(x=>x.id===rows[k].groupId)&&!q.d.results.some(x=>x.id===rows[o].groupId));q=await call(ctx,k,`/api/pos/hospitality/table-groups/${rows[o].groupId}/dissolve/`,'POST',{});check(k+'_foreign_group_ID_dissolve_denied',q.s===404);q=await call(ctx,k,'/api/pos/hospitality/table-groups/','POST',{table_ids:[rows[k].id,rows[o].id],label:'MUST-NOT-MIX',request_key:require('node:crypto').randomUUID()});check(k+'_mixed_tenant_group_create_denied',q.s===404);
  q=await call(ctx,k,`/api/pos/tabs/${tabs[o].tab_id}/`);check(k+'_foreign_Tab_ID_read_denied',q.s===404);
  r=await raw.post(host(o)+`/api/pos/hospitality/tables/${rows[o].id}/service/open-tab/`,{headers:{Origin:host(o),Cookie:cookie},data:{idempotency_key:'spec025-live-service-'+p.run,display_label:'QA no-money '+k.toUpperCase()}});check(k+'_idempotency_replay_cannot_bypass_host',r.status()===403);
  q=await call(ctx,k,`/api/pos/hospitality/tables/${rows[o].id}/guest-ordering/`,'POST',{blocked:true});check(k+'_foreign_table_ID_write_denied',q.s===404);
  q=await call(ctx,k,`/api/pos/catalog/products/${products[o].id}/`,'PATCH',{name:'FOREIGN-MUST-NOT-MODIFY'});check(k+'_foreign_product_ID_write_denied',q.s===404);
  q=await call(ctx,k,'/api/realtime/stream?once=1&cursor='+encodeURIComponent(cursors[o]));check(k+'_foreign_staff_cursor_reset',q.s===200&&(await q.r.text()).includes('event: reset'));
  q=await call(guest,k,'/api/guest/qr/resolve','POST',{token:rows[o].public_token});check(k+'_foreign_QR_denied',q.s===404&&q.d.code==='QR_NOT_FOUND');
  const gc=(await guest.cookies(host(k))).map(c=>c.name+'='+c.value).join('; ');r=await raw.get(host(o)+'/api/guest/context',{headers:{Cookie:gc,'X-Guest-Session':rows[k].public_token}});check(k+'_foreign_guest_cookie_denied',r.status()===404);
  q=await call(guest,k,'/api/guest/realtime/stream?once=1&cursor='+encodeURIComponent(rows[o].guestCursor),'GET',undefined,{'X-Guest-Session':rows[k].public_token});check(k+'_foreign_guest_cursor_reset',q.s===200&&(await q.r.text()).includes('event: reset'));
  q=await call(ctx,k,'/api/pos/hospitality/tables/');check(k+'_no_foreign_creation',q.s===200&&!q.d.results.some(t=>t.label.startsWith('FOREIGN-MUST-NOT-EXIST')));
  q=await call(ctx,k,'/api/auth/me','GET',undefined,{'X-Forwarded-Host':'e2e'+o+'.rodada.bar','X-Rodada-Bff-Host':'e2e'+o+'.rodada.bar','X-Rodada-Bff-Time':'0','X-Rodada-Bff-Signature':'0'.repeat(64)});check(k+'_forged_headers_no_tenant_switch',q.s===200&&q.d.venue?.id===p.ids[k]);
 }
 for(const k of ['a','b']){const gh={'X-Guest-Session':rows[k].public_token},guest=guests[k];const old=(await guest.cookies(host(k))).map(c=>c.name+'='+c.value).join('; ');let q=await call(guest,k,'/api/guest/customer/logout','POST',{},gh);check(k+'_customer_logout',q.s===200);const r=await raw.get(host(k)+'/api/guest/customer/context',{headers:{Cookie:old,...gh}});check(k+'_customer_logout_cookie_replay_denied',r.status()===401);q=await call(guest,k,'/api/guest/context','GET',undefined,gh);check(k+'_customer_logout_preserves_anonymous_visit',q.s===200&&q.d.session_scope?.venue_id===p.ids[k]);}
 const u=await raw.get('https://unregistered-preview.rodada.bar/api/venue/context');check('enabled_unknown_host_denied',u.status()===421);await raw.dispose();
 }catch(e){results.push({scenario:'execution_stopped',pass:false,reason:'A scenario failed; no secret or response body published'});}
 finally{
  for(const k of Object.keys(contexts))try{const replayCookie=(await contexts[k].cookies(host(k))).map(c=>c.name+'='+c.value).join('; ');const q=await call(contexts[k],k,'/api/auth/logout','POST',{});results.push({scenario:k+'_logout_own_browser_session',pass:q.s===204,http_status:q.s});const q2=await call(contexts[k],k,'/api/auth/me');results.push({scenario:k+'_logged_out_session_denied',pass:q2.s===401,http_status:q2.s});const probe=await request.newContext();try{const revoked=await probe.get(host(k)+'/api/auth/me',{headers:{Cookie:replayCookie}});results.push({scenario:k+'_revoked_cookie_replay_denied',pass:revoked.status()===401,http_status:revoked.status()});}finally{await probe.dispose();}}catch{results.push({scenario:k+'_logout_cleanup',pass:false})}
  if(browser)await browser.close();
 }
 process.stdout.write(JSON.stringify({sha:p.sha,run:p.run,scope:'real Chromium HTTPS browser and APIs; QA-only nonfinancial writes; no screenshots/traces/storage state or credentials persisted',all_pass:results.length>70&&results.every(x=>x.pass),results,qa_objects:Object.fromEntries(Object.entries(rows).map(([k,v])=>[k,{table_id:v.id,product_id:products[k]?.id,tab_id:tabs[k]?.tab_id,occupancy_id:tabs[k]?.occupancy_id,group_id:rows[k]?.groupId,guest_tab_id:rows[k]?.guestTabId}]))}));
}
