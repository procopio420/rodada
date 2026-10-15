if not __debug__:raise RuntimeError('Optimization disabled')
import base64,os,sys,json,urllib.request,urllib.error,urllib.parse,hmac,hashlib,time,threading,subprocess
p=json.load(sys.stdin);assert os.getenv('RAILWAY_GIT_COMMIT_SHA')==p['sha'];assert os.getenv('RODADA_ENABLE_TENANT_HOST_UI')=='false'
os.chdir('/app/apps/api');sys.path.insert(0,os.getcwd());os.environ.setdefault('DJANGO_SETTINGS_MODULE','rodada_api.settings')
import django;django.setup()
from modules.hospitality.models import Table
from modules.catalog.models import Product
expected_events={k:str(Product.objects.get(pk=p['products'][k],venue_id=p['ids'][k]).pk) for k in ('a','b')}
original_states={k:Product.objects.get(pk=p['products'][k],venue_id=p['ids'][k]).availability.state for k in ('a','b')};modified=set()
secret=os.environ['RODADA_BFF_HOST_SECRET'];tokens={};guest={};profiles={};qr_tokens={};results=[];streams={};readies={k+kind:threading.Event() for k in ('a','b') for kind in ('staff','guest')};threads=[];containment=None;containment_attempts=[];violation=threading.Event();changes={k+kind:threading.Event() for k in ('a','b') for kind in ('staff','guest')}

def req(url,body=None,headers=None,method=None):
 h={'User-Agent':'Mozilla/5.0 Rodada-Spec025-Audit',**(headers or {})}
 if body is not None:h['Content-Type']='application/json'
 try:r=urllib.request.urlopen(urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers=h,method=method),timeout=20)
 except urllib.error.HTTPError as e:r=e
 with r:
  try:d=json.loads(r.read(200000))
  except Exception:d={}
  return r.status,d

def signed(path,k,kind):
 host='e2e'+k+'.rodada.bar';t=str(int(time.time()));sig=hmac.new(secret.encode(),f'{t}\nGET\n{path}\n{host}'.encode(),hashlib.sha256).hexdigest()
 h={'Host':'api.rodada.bar','X-Rodada-Bff-Host':host,'X-Rodada-Bff-Time':t,'X-Rodada-Bff-Signature':sig}
 h.update({'Authorization':'Bearer '+tokens[k]['access_token']} if kind=='staff' else {'X-Guest-Session':guest[k]})
 return h

def witness(k,kind,cursor):
 key=k+kind;events=[];current=None;foreign=False
 try:
  path='/realtime/stream/' if kind=='staff' else '/guest/realtime/stream/'
  with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000'+path+'?cursor='+urllib.parse.quote(cursor),headers=signed(path,k,kind)),timeout=45) as r:
   until=time.monotonic()+45
   while time.monotonic()<until:
    line=r.readline(10000)
    if not line:break
    if line.startswith(b'event: '):
     event=line[7:].strip().decode();current=event;events.append(event)
     if event=='ready':readies[key].set()
     if event in ('revoked','reauthenticate'):break
    if line.startswith(b'data: ') and current=='change':
     data=json.loads(line[6:])
     if data.get('venue_id')!=p['ids'][k]:
      foreign=True;violation.set();raise RuntimeError('foreign event observed')
     if data.get('aggregate_id')==expected_events[k] and data.get('aggregate_type')=='Product' and data.get('type')=='product.availability_changed' and data.get('venue_id')==p['ids'][k]:changes[key].set()
  streams[key]={'ready':readies[key].is_set(),'revoked':any(e in ('revoked','reauthenticate') for e in events),'change_events':events.count('change'),'own_catalog_change_seen':changes[key].is_set(),'foreign_change_seen':foreign}
 except Exception:streams[key]={'ready':readies[key].is_set(),'revoked':False,'transport_error':True,'foreign_change_seen':foreign}

try:
 for k in ('a','b'):
  s,d=req('https://api.rodada.bar/auth/login/',{'venue_slug':'spec025-qa-'+k,'login_identifier':'spec025-qa-'+k+'-owner','pin':p['pins'][k],'installation_id':'spec025-final-revoke-'+k+'-'+str(int(time.time())),'platform':'ANDROID'})
  assert s==200;tokens[k]=d
  auth={'Authorization':'Bearer '+tokens[k]['access_token']}
  s,policy=req('https://api.rodada.bar/management/guest-policy/',headers=auth);assert s==200
  s,policy=req('https://api.rodada.bar/management/guest-policy/',{'blocked':False,'expected_version':policy['version'],'reason':'Spec025 controlled QA-only SSE containment verification'},auth,method='PATCH');assert s==200
  results.append({'scenario':k+'_QA_only_guest_policy_prepared','pass':True,'status':s})
  table=Table.objects.get(pk=p['tables'][k],venue__slug='spec025-qa-'+k);qr_tokens[k]=table.public_token
  s,d=req('https://api.rodada.bar/guest/qr/resolve/',{'token':table.public_token});assert s in (200,201);guest[k]=d['guest_session_token']
  password=base64.urlsafe_b64encode(hmac.new(p['pins'][k].encode(),('spec025-profile-new-'+p['run']).encode(),hashlib.sha256).digest()).decode().rstrip('=')
  s,d=req('https://api.rodada.bar/guest/customer/login/',{'username':'qa-profile-'+k+'-'+p['run'],'password':password},{'X-Guest-Session':guest[k]});assert s==200;profiles[k]=d['customer_auth_token']
  s,d=req('https://api.rodada.bar/guest/customer/context/',headers={'X-Guest-Session':guest[k],'X-Customer-Session':profiles[k]});assert s==200 and d.get('authenticated') is True
  results.append({'scenario':k+'_native_profile_valid_before_containment','pass':True,'status':s})
  for kind in ('staff','guest'):
   path='/realtime/snapshot/' if kind=='staff' else '/guest/realtime/snapshot/'
   h={'Authorization':'Bearer '+tokens[k]['access_token']} if kind=='staff' else {'X-Guest-Session':guest[k]}
   s,d=req('https://api.rodada.bar'+path,headers=h);assert s==200
   t=threading.Thread(target=witness,args=(k,kind,d['cursor']),daemon=True);t.start();threads.append(t)
 assert all(e.wait(15) for e in readies.values())
 results.append({'scenario':'four_streams_ready_before_containment','pass':True})
 for k in ('a','b'):
  modified.add(k)
  status,data=req('https://api.rodada.bar/catalog/products/'+p['products'][k]+'/availability/',{'state':'UNAVAILABLE' if original_states[k]=='AVAILABLE' else 'AVAILABLE'},{'Authorization':'Bearer '+tokens[k]['access_token']},method='POST')
  assert status==200
 deadline=time.monotonic()+12
 while time.monotonic()<deadline and not violation.is_set() and not all(event.is_set() for event in changes.values()):time.sleep(0.02)
 assert not violation.is_set() and all(event.is_set() for event in changes.values())
 results.append({'scenario':'four_concurrent_streams_receive_only_own_catalog_changes','pass':True})
except Exception:results.append({'scenario':'four_streams_ready_before_containment','pass':False,'reason':'setup failed; containment still attempted'})
finally:
 for k in modified:
  try:
   rs,rd=req('https://api.rodada.bar/catalog/products/'+p['products'][k]+'/availability/',{'state':original_states[k]},{'Authorization':'Bearer '+tokens[k]['access_token']},method='POST')
   results.append({'scenario':k+'_QA_availability_restored','pass':rs==200 and rd.get('state')==original_states[k],'status':rs})
  except Exception:results.append({'scenario':k+'_QA_availability_restored','pass':False})
 for attempt in range(3):
  r=subprocess.run([sys.executable,'-c',p['containment_script']],input=json.dumps({'operation':'deactivate','sha':p['sha']}),text=True,capture_output=True,timeout=90)
  diagnostics={'attempt':attempt+1,'committed':r.returncode==0,'lock_not_available':'could not obtain lock' in r.stderr,'qa_nowait_refusal':'REFUSE: QA access operation in progress; no changes committed. Retry after it completes; containment has NOT succeeded.' in r.stderr,'serialization_failure':'could not serialize access' in r.stderr,'deadlock':'deadlock detected' in r.stderr,'scope_guard_failed':'foreign row changed:' in r.stderr,'error_types':__import__('re').findall(r'^([A-Za-z_.]+(?:Error|Exception))(?::|$)',r.stderr,__import__('re').M),'trace_lines':__import__('re').findall(r'File "<string>", line (\d+)',r.stderr)}
  containment_attempts.append(diagnostics)
  if r.returncode==0 or not any(diagnostics[k] for k in ('lock_not_available','qa_nowait_refusal','serialization_failure','deadlock')):break
  time.sleep(0.2)
 if r.returncode==0:
  containment=json.loads(r.stdout)
  results.append({'scenario':'QA_containment_committed','pass':containment['committed_readback_matches']})
 else:results.append({'scenario':'QA_containment_committed','pass':False,'reason':'requires inspect; no success claimed'})
 for t in threads:t.join(30)
for k in ('a','b'):
 if k in tokens:
  for path,body in [('/auth/me/',None),('/auth/refresh/',{'refresh_token':tokens[k]['refresh_token']})]:
   s,d=req('https://api.rodada.bar'+path,body,{'Authorization':'Bearer '+tokens[k]['access_token']});results.append({'scenario':k+'_after_containment'+path,'status':s,'pass':s in (401,403) and 'venue' not in d and 'access_token' not in d})
  s,d=req('https://api.rodada.bar/auth/login/',{'venue_slug':'spec025-qa-'+k,'login_identifier':'spec025-qa-'+k+'-owner','pin':p['pins'][k],'installation_id':'spec025-final-denial-'+k,'platform':'ANDROID'});results.append({'scenario':k+'_new_native_login_denied','status':s,'pass':s==403 and d.get('code')=='MEMBERSHIP_SUSPENDED'})
 if k in qr_tokens:
  s,d=req('https://api.rodada.bar/guest/qr/resolve/',{'token':qr_tokens[k]});results.append({'scenario':k+'_new_native_QR_denied','status':s,'pass':s==403 and d.get('code')=='VENUE_GUEST_MUTATIONS_BLOCKED' and 'guest_session_token' not in d})
 if k in profiles:
  s,d=req('https://api.rodada.bar/guest/customer/context/',headers={'X-Guest-Session':guest[k],'X-Customer-Session':profiles[k]});results.append({'scenario':k+'_customer_identity_after_guest_containment_denied','status':s,'pass':s in (401,403,404) and 'display_name' not in d and 'claimable_tabs' not in d})
 if k in guest:
  s,d=req('https://api.rodada.bar/guest/context/',headers={'X-Guest-Session':guest[k]});results.append({'scenario':k+'_old_native_guest_session_denied','status':s,'pass':s in (401,403,404) and 'session_scope' not in d})
  s,d=req('https://api.rodada.bar/guest/realtime/stream/?once=1',headers={'X-Guest-Session':guest[k]});results.append({'scenario':k+'_native_guest_SSE_reconnect_denied','status':s,'pass':s in (401,403,404)})
 if k in tokens:
  for kind in ('staff','guest'):
   if kind=='guest' and k not in guest:continue
   path='/realtime/stream/' if kind=='staff' else '/guest/realtime/stream/'
   s,d=req('http://127.0.0.1:8000'+path+'?once=1',headers=signed(path,k,kind));results.append({'scenario':k+'_'+kind+'_canonical_reconnect_denied','status':s,'pass':s==421})
print(json.dumps({'sha':p['sha'],'flag_off':True,'scope':'After flag false redeploy: four live signed ASGI staff/guest streams and QA containment; no money/order operations','containment':containment,'containment_attempts':containment_attempts,'streams':streams,'results':results,'all_pass':len(streams)==4 and all(v['ready'] and v['revoked'] and v.get('own_catalog_change_seen') and not v.get('foreign_change_seen') for v in streams.values()) and all(x['pass'] for x in results)}))
