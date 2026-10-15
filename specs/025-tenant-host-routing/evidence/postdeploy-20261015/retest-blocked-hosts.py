import subprocess,json,tempfile,pathlib,datetime
hosts=['e2ea.rodada.bar','e2eb.rodada.bar','unregistered-preview.rodada.bar']
cases=[('GET','/'),('HEAD','/staff'),('GET','/staff/'),('GET','/atendimento?venue=web-e2e'),('GET','/m/invalid-audit-proof'),('GET','/manifest.webmanifest'),('GET','/api/venue/context'),('POST','/api/auth/login',{}),('GET','/api/auth/me'),('GET','/api/auth/me',None,{'Cookie':'rodada_staff_refresh=invalid-audit-proof'}),('POST','/api/guest/qr/resolve',{}),('POST','/api/guest/qr/resolve',{'token':'invalid-audit-proof'}),('POST','/api/guest/qr/resolve/',{'token':'invalid-audit-proof'}),('GET','/api/guest/context'),('GET','/api/guest/context',None,{'X-Guest-Session':'invalid-audit-proof'}),('POST','/api/guest/orders',{}),('GET','/api/realtime/stream?once=1'),('OPTIONS','/api/auth/login'),('POST','/nonexistent',{})]
results=[]
with tempfile.TemporaryDirectory() as t:
 for host in hosts:
  for case in cases:
   method,path=case[:2];headers={'Origin':'https://'+host,'User-Agent':'Mozilla/5.0 Rodada-Postdeploy-Audit','X-Forwarded-Host':'bardoaderlan.rodada.bar','X-Rodada-Bff-Host':'bardoaderlan.rodada.bar','X-Rodada-Bff-Time':'0','X-Rodada-Bff-Signature':'0'*64,**(case[3] if len(case)>3 else {})}
   cmd=['curl','--silent','--show-error','--max-time','25','-D',t+'/headers','-o',t+'/body','-w','%{http_code}','https://'+host+path]
   cmd+=['--head'] if method=='HEAD' else ['-X',method]
   for k,v in headers.items():cmd+=['-H',k+': '+v]
   if len(case)>2 and case[2] is not None:cmd+=['-H','Content-Type: application/json','--data-binary',json.dumps(case[2])]
   p=subprocess.run(cmd,capture_output=True,text=True)
   h=pathlib.Path(t+'/headers').read_text().lower();body=pathlib.Path(t+'/body').read_text()
   try:code=json.loads(body).get('code') if method!='HEAD' else None
   except:code=None
   ok=p.returncode==0 and p.stdout=='421' and '\nlocation:' not in h and '\nset-cookie:' not in h and 'no-store' in h and (method=='HEAD' or code=='VENUE_HOST_NOT_FOUND')
   results.append({'host':host,'method':method,'path':path,'invalid_refresh':bool(len(case)>3 and 'Cookie'in case[3]),'status':p.stdout,'tls_verified':p.returncode==0,'code':code,'no_redirect':'\nlocation:'not in h,'no_set_cookie':'\nset-cookie:'not in h,'no_store':'no-store'in h,'result':'PASS'if ok else'FAIL'})
   if not ok:print(json.dumps(results[-1]),flush=True)
d={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'curl HTTPS; TLS verification enabled; no redirects; spoofed external assertions; dummy invalid proofs only','cases':results,'all_pass':all(x['result']=='PASS' for x in results)}
pathlib.Path('blocked-hosts-curl-retest.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'cases':len(results),'all_pass':d['all_pass']}))
