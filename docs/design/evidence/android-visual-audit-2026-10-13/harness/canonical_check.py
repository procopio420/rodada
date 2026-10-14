from pathlib import Path
import os,sys,json
root=Path(__file__).resolve().parents[1]
for line in (root/'.audit-local/private.env').read_text().splitlines():
 k,v=line.split('=',1);os.environ[k]=v
sys.path.insert(0,str(root/'apps/api'))
import django;django.setup()
from modules.ordering.models import Order
from modules.ledger.models import Charge
from django.db.models import Sum
requests=[json.loads(s) for s in (root/'.audit-local/order-transport.jsonl').read_text().splitlines()]
last=next(r for r in reversed(requests) if r['stage']=='received')
key=last['body']['idempotency_key'];orders=Order.objects.filter(tab__venue__slug='audit-aderlan',idempotency_key=key)
row={'stage':sys.argv[1],'intent_key':key,'payload_sha256':last['payload_sha256'],'orders_for_intent':orders.count(),'order_ids':[str(o.id) for o in orders],'charge_count':Charge.objects.filter(order_item__order__in=orders).count(),'charge_cents':Charge.objects.filter(order_item__order__in=orders).aggregate(value=Sum('amount_cents'))['value'],'confirmed_actor_ids':[str(o.confirmed_by_id) for o in orders],'confirmed_at':[str(o.confirmed_at) for o in orders],'transport':[r for r in requests if r.get('payload_sha256')==last['payload_sha256']]}
p=root/'docs/design/evidence/android-visual-audit-2026-10-13'/('canonical-'+sys.argv[1]+'.json');p.write_text(json.dumps(row,ensure_ascii=False,indent=2))
print(json.dumps({k:row[k] for k in ['stage','orders_for_intent','charge_count','charge_cents']}))
