"""Read-only gate for the native refund journey, isolated test database only."""
import argparse,json,os,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
assert os.environ.get("POSTGRES_DB")=="rodada_demo"
assert os.environ.get("POSTGRES_HOST")=="127.0.0.1" and os.environ.get("POSTGRES_PORT")=="55523"
p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args()
out=(root/a.out).resolve();assert out.is_relative_to(root/"docs/design/evidence")
sys.path.insert(0,str(root/"apps/api"));os.environ.setdefault("DJANGO_SETTINGS_MODULE","rodada_api.settings")
import django
django.setup()
from modules.ordering.models import Tab
from modules.ledger.models import Refund
from modules.audit.models import AuditEvent
nodes=json.loads((out/"native-tab.json").read_text(encoding="utf-8"))
labels=[n["text"] for n in nodes if n["text"].startswith("Spec023 test ")];assert len(labels)==1
tab=Tab.objects.get(venue__slug="release-demo",display_label=labels[0])
assert tab.state=="CLOSED" and tab.closed_at and tab.orders.count()==1
charges=sum(tab.charges.values_list("amount_cents",flat=True));assert charges==600
payments=list(tab.payments.order_by("amount_cents"));assert [x.amount_cents for x in payments]==[300,600]
assert payments[0].status=="CONFIRMED" and payments[1].status=="PARTIALLY_REFUNDED"
assert all(x.method=="CASH" and not x.provider_payment_id and x.confirmed_at for x in payments)
assert all(x.received_by_id==tab.opened_by_id for x in payments)
refunds=list(Refund.objects.filter(payment__tab=tab));assert len(refunds)==1
refund=refunds[0];assert refund.payment_id==payments[1].id and refund.amount_cents==300
assert refund.status=="CONFIRMED" and refund.confirmed_at and refund.reason=="Estorno test nativo"
assert refund.created_by_id==tab.opened_by_id and not refund.provider_refund_id
movement=refund.cash_movement;assert movement.amount_cents==-300 and movement.kind=="CASH_REFUND"
assert movement.actor_id==refund.created_by_id
shift=movement.shift;assert shift.status=="CLOSED" and shift.closed_at
assert shift.counted_amount_cents==shift.expected_amount_cents_snapshot==600 and shift.discrepancy_cents==0
assert AuditEvent.objects.filter(entity_type="Refund",entity_id=str(refund.id),event_type="payment.refunded",actor_staff_id=refund.created_by_id,reason=refund.reason).count()==1
assert not tab.ledger_adjustments.exists()
assert charges-sum(x.amount_cents for x in payments)+refund.amount_cents==0
result={"passed":True,"source":"read-only Django ORM, real isolated PostgreSQL55523","native_android_ui":"RUN_API36","payments":"MANUAL_TEST","tab_state":tab.state,"orders":1,"charges_cents":charges,"payments_cents":900,"refunds_cents":300,"open_exposure_cents":0,"original_payment":"PARTIALLY_REFUNDED, preserved600","refund_count":1,"refund_actor_timestamp_audit":True,"cash_refund_movement_cents":-300,"cash_expected_cents":600,"cash_counted_cents":600,"cash_discrepancy_cents":0,"provider":"NOT_RUN","hardware":"NOT_RUN"}
(out/"native-refund-readback.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result))
