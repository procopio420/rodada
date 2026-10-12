import json, os, django
from urllib.request import Request,urlopen
from urllib.error import HTTPError
os.environ.setdefault('DJANGO_SETTINGS_MODULE','rodada_api.settings'); django.setup()
from modules.ordering.models import Order,OrderItem
from modules.ledger.models import Charge,Payment
from modules.hospitality.models import Table
from modules.venue.models import Venue
from modules.ledger.services import totals as tab_totals
BASE='http://127.0.0.1:8000'
def api(method,path,data=None,token=None,guest=None):
 h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 if guest:h['X-Guest-Session']=guest
 r=Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=h,method=method)
 try:
  with urlopen(r,timeout=20) as q:return q.status,json.load(q)
 except HTTPError as q:return q.code,json.load(q)
status,login=api('POST','/auth/login/',dict(venue_slug='pinned-pilot-test',login_identifier='pinned-owner-test',pin=json.load(open('/tmp/pinned-test-credentials.json'))['pin'],installation_id='pinned-final-probe',platform='WEB',friendly_label='Disposable final test'));assert status==200,(status,login.get('code'))
t=login['access_token']
if not Order.objects.exists():
 products=[]
 for name,price,station in [('PINNED TEST BAR',500,'BAR'),('PINNED TEST KITCHEN',1000,'KITCHEN')]:
  status,product=api('POST','/catalog/resolve-or-create/',{'name':name,'price_cents':price,'fulfillment_station':station},t);assert status in (200,201),(status,product);products.append(product['product'])
 status,tab=api('POST','/tabs/',{'display_label':'Pinned TEST canonical order'},t);assert status==201
 status,neworder=api('POST',f"/tabs/{tab['id']}/orders/confirm/",{'idempotency_key':'pinned-final19-order','lines':[{'product_id':p['id'],'quantity':1} for p in products]},t);assert status==201
 status,newtable=api('POST','/hospitality/tables/',{'label':'PINNED TEST QR','guest_ordering_mode':'DIRECT'},t);assert status==201
 status,_=api('POST',f"/hospitality/tables/{newtable['id']}/occupy/",{'tab_id':tab['id']},t);assert status in (200,201)
order=Order.objects.get();items=list(order.items.all());table=Table.objects.get(label='PINNED TEST QR')
status,replay=api('POST',f'/tabs/{order.tab_id}/orders/confirm/',{'idempotency_key':order.idempotency_key,'lines':[{'product_id':str(i.product_id),'quantity':i.quantity} for i in items]},t);assert status==200
for station in ['BAR','KITCHEN']:
 status,queue=api('GET',f'/production/{station}/',token=t);assert status==200
status,policy=api('GET','/management/guest-policy/',token=t);assert status==200
if not policy['blocked']:
 status,policy=api('PATCH','/management/guest-policy/',{'blocked':True,'expected_version':policy['version'],'reason':'Restore secure default after interrupted test'},t);assert status==200
status,_=api('POST','/guest/qr/resolve/',{'token':table.public_token});assert status==403
status,policy=api('PATCH','/management/guest-policy/',{'blocked':False,'expected_version':policy['version'],'reason':'Disposable QR acceptance'},t);assert status==200
try:
 status,guest=api('POST','/guest/qr/resolve/',{'token':table.public_token});assert status in (200,201),(status,guest.get('code'))
 qr_status=status
finally:
 status,policy=api('PATCH','/management/guest-policy/',{'blocked':True,'expected_version':policy['version'],'reason':'Restore disabled guest mutations'},t);assert status==200
status,payload=api('POST','/guest/tabs/',{},guest=guest['guest_session_token']);assert status==403,(status,payload.get('code'))
status,snapshot=api('GET','/realtime/snapshot/',token=t);assert status==200
with urlopen(Request(BASE+'/realtime/stream/',headers={'Authorization':'Bearer '+t}),timeout=20) as q:
 assert q.status==200 and 'text/event-stream' in q.headers['Content-Type'];assert q.readline()
counts={'orders':Order.objects.count(),'items':OrderItem.objects.count(),'charges':Charge.objects.count(),'payments':Payment.objects.count()};assert counts==dict(orders=1,items=2,charges=2,payments=0),counts
result={'source_sha':'19dfc80e27f619a32c02518fad745e30db09830e','order_id':str(order.id),'tab_id':str(order.tab_id),'counts':counts,'totals':tab_totals(order.tab),'order_replay_status':200,'bar_kitchen_queues':True,'qr_resolution_status':qr_status,'guest_mutations_reblocked':Venue.objects.get().guest_mutations_blocked,'guest_mutation_status':403,'authenticated_snapshot_sse':True,'scope':'Disposable deployed API; no real payment/customer/hardware'}
json.dump(result,open('/tmp/pinned-api-evidence.json','w'),indent=2,default=str);print(json.dumps(result,default=str))
