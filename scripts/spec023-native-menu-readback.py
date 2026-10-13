"""Read-only verification of the isolated native canonical-menu cash journey."""
import argparse
import json
import os
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", required=True)
parser.add_argument("--port", required=True)
parser.add_argument("--final", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
assert os.environ.get("POSTGRES_DB") == "rodada_demo"
assert os.environ.get("POSTGRES_HOST") == "127.0.0.1"
assert os.environ.get("POSTGRES_PORT") == args.port and args.port != "5432"
out = (root / args.out).resolve()
assert out.is_relative_to(root / "visual-artifacts") or out.is_relative_to(root / "docs/design/evidence")
sys.path.insert(0, str(root / "apps/api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from modules.ordering.models import Tab
from modules.ledger.models import Refund
from modules.audit.models import AuditEvent
from modules.cash.models import CashShift

nodes = json.loads((out / "native-tab.json").read_text(encoding="utf-8"))
labels = [node["text"] for node in nodes if node["text"].startswith("Spec023 test ")]
assert len(labels) == 1
tab = Tab.objects.get(venue__slug="release-demo", display_label=labels[0])
charges = sum(tab.charges.values_list("amount_cents", flat=True))
payments = list(tab.payments.order_by("amount_cents"))
refunds = list(Refund.objects.filter(payment__tab=tab))
items = list(tab.orders.get().items.all())
shift = CashShift.objects.filter(venue=tab.venue).latest("opened_at")
result = {
    "source": "read-only Django ORM on isolated PostgreSQL",
    "native_android_ui": "API36 emulator", "classification": "MANUAL_TEST",
    "tab_state": tab.state, "orders": tab.orders.count(),
    "items": [{"name": item.product_name_snapshot, "quantity": item.quantity,
               "station": item.fulfillment_station_snapshot, "state": item.state,
               "line_total_cents": item.line_total_cents} for item in items],
    "charges_cents": charges, "payments_cents": sum(payment.amount_cents for payment in payments),
    "refunds_cents": sum(refund.amount_cents for refund in refunds),
    "payment_count": len(payments), "refund_count": len(refunds),
    "shift_status": shift.status, "cash_expected_cents": shift.expected_amount_cents_snapshot,
    "cash_counted_cents": shift.counted_amount_cents, "cash_discrepancy_cents": shift.discrepancy_cents,
}
result["open_exposure_cents"] = charges - result["payments_cents"] + result["refunds_cents"]
if args.final:
    assert tab.state == "CLOSED" and tab.closed_at and tab.orders.count() == 1
    assert charges == 1550 and len(items) == 2
    assert {(item.fulfillment_station_snapshot, item.line_total_cents) for item in items} == {("BAR", 1200), ("KITCHEN", 350)}
    assert all(item.state == "DELIVERED" for item in items)
    assert [payment.amount_cents for payment in payments] == [300, 1550]
    assert [payment.status for payment in payments] == ["CONFIRMED", "PARTIALLY_REFUNDED"]
    assert all(payment.method == "CASH" and not payment.provider_payment_id and payment.confirmed_at
               and payment.received_by_id == tab.opened_by_id for payment in payments)
    assert len(refunds) == 1
    refund = refunds[0]
    assert refund.payment_id == payments[1].id and refund.amount_cents == 300
    assert refund.status == "CONFIRMED" and refund.confirmed_at and not refund.provider_refund_id
    assert refund.created_by_id == tab.opened_by_id and refund.cash_movement.amount_cents == -300
    assert refund.cash_movement.actor_id == refund.created_by_id
    assert AuditEvent.objects.filter(entity_type="Refund", entity_id=str(refund.id),
                                    event_type="payment.refunded", actor_staff_id=refund.created_by_id,
                                    reason=refund.reason).count() == 1
    assert shift.status == "CLOSED" and shift.closed_at
    assert shift.expected_amount_cents_snapshot == shift.counted_amount_cents == 1550
    assert shift.discrepancy_cents == result["open_exposure_cents"] == 0
    assert not tab.ledger_adjustments.exists()
    result.update(passed=True, refund_actor_timestamp_audit=True, provider="NOT_RUN", hardware="NOT_RUN")
    (out / "native-menu-readback.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
