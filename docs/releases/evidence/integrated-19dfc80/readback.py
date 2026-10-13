import os,json,django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','rodada_api.settings');django.setup()
from modules.ordering.models import Order,OrderItem
from modules.ledger.models import Charge,Payment,Refund
from modules.ledger.services import totals
from modules.access.models import StaffMember
from modules.audit.models import AuditEvent
from modules.venue.models import Venue
order=Order.objects.get();staff=StaffMember.objects.get();pin=json.load(open('/tmp/pinned-test-credentials.json'))['pin'];assert staff.check_pin(pin)
result={'source_sha':'19dfc80e27f619a32c02518fad745e30db09830e','order_id':str(order.id),'tab_id':str(order.tab_id),'orders':Order.objects.count(),'items':OrderItem.objects.count(),'charges':Charge.objects.count(),'payments':Payment.objects.count(),'refunds':Refund.objects.count(),'totals':totals(order.tab),'staff':StaffMember.objects.count(),'pin_preserved':True,'guest_blocked':Venue.objects.get().guest_mutations_blocked,'bootstrap_audits':AuditEvent.objects.filter(event_type='access.owner_bootstrapped').count(),'audits':AuditEvent.objects.count()}
assert result['orders']==1 and result['items']==2 and result['charges']==2 and result['payments']==0 and result['refunds']==0 and result['bootstrap_audits']==1 and result['totals']['charges_cents']==1500
print(json.dumps(result))
