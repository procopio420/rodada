#!/usr/bin/env python3
"""Reconcile test-only UI payments and cash close against independent PostgreSQL rows."""
import json
import os
from pathlib import Path
import subprocess
from cross_surface_fixture import require_disposable_database, require_connected_database, database_instance_identity
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection
from modules.cash.models import CashShift, CashMovement
from modules.ledger.models import Charge, Payment, Refund
from modules.ordering.models import Tab, Order
from modules.audit.models import AuditEvent
from modules.access.models import StaffMember
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
r = json.loads(Path("artifacts/financial-browser.json").read_text())
assert f["database_instance_id"] == database_instance_identity(connection)
assert r["sha"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
assert r["test_only"] is True and f["database"] == connection.settings_dict["NAME"]
tab = Tab.objects.get(pk=r["tab_id"], venue_id=f["venue_id"], state="CLOSED")
payments = Payment.objects.filter(tab=tab)
assert payments.count() == 2 and {str(p.pk) for p in payments} == set(r["payment_ids"])
assert all(p.status in ("CONFIRMED", "PARTIALLY_REFUNDED") and p.method == "CASH" and p.confirmed_at for p in payments)
assert sorted(p.amount_cents for p in payments) == [300, r["paid_cents"] - 300]
assert sum(p.amount_cents for p in payments) == r["paid_cents"]
assert r["paid_cents"] - r["refund_cents"] == sum(c.amount_cents for c in Charge.objects.filter(tab=tab))
refund = Refund.objects.get(pk=r["refund_id"], payment_id=r["first_payment_id"])
assert refund.amount_cents == r["refund_cents"] == 100 and refund.status == "CONFIRMED" and refund.confirmed_at
assert Refund.objects.filter(payment__tab=tab).count() == 1
assert r["cash_response_loss_replays"] == 2
shift = CashShift.objects.get(pk=r["shift_id"], cash_point__venue_id=f["venue_id"])
assert shift.status == "CLOSED" and shift.review_status == "REVIEWED"
# Independent calendar calculation; do not call the API's business_date helper.
from datetime import timedelta
from zoneinfo import ZoneInfo
venue = shift.cash_point.venue
expected_business_date = (shift.opened_at.astimezone(ZoneInfo(venue.timezone)) - timedelta(hours=venue.business_day_cutoff_hour)).date()
assert shift.business_date == expected_business_date
roles = json.loads(Path("artifacts/financial-roles-browser.json").read_text())
assert roles["sha"] == r["sha"] and roles["database_instance_id"] == f["database_instance_id"]
assert roles["shift_id"] == str(shift.pk) and all(value == 403 for value in roles["denied_statuses"])
assert CashShift.objects.filter(cash_point_id=f["cash_point_id"]).count() == 1
assert shift.expected_amount_cents_snapshot == r["expected_cents"]
assert shift.discrepancy_cents == r["discrepancy_cents"] == -1000
assert shift.counted_amount_cents == r["expected_cents"] - 1000
movements = CashMovement.objects.filter(shift=shift)
assert sorted(movements.values_list("kind", flat=True)) == ["CASH_PAYMENT", "CASH_PAYMENT", "CASH_REFUND", "OPENING_FLOAT", "SUPPLY", "WITHDRAWAL"]
assert sum(movements.values_list("amount_cents", flat=True)) == shift.expected_amount_cents_snapshot
assert set(str(x) for x in movements.exclude(payment_id=None).values_list("payment_id", flat=True)) == set(r["payment_ids"])
staff = StaffMember.objects.get(login_identifier="android-post-drop-operator")
assert CashMovement.objects.filter(shift=shift, refund=refund).count() == 1
assert AuditEvent.objects.filter(venue_id=f["venue_id"], entity_id=str(refund.pk), actor_session_id__isnull=False).exists()
assert shift.opened_by_id == shift.closed_by_id == shift.reviewed_by_id == staff.pk
assert all(p.received_by_id == staff.pk and not p.provider and not p.provider_payment_id for p in payments)
assert shift.closed_at and shift.reviewed_at and shift.review_reason
assert all(m.actor_id == staff.pk and m.actor_session_id for m in movements)
events = AuditEvent.objects.filter(venue_id=f["venue_id"], entity_id=str(shift.pk), actor_staff=staff).exclude(actor_session_id=None)
assert events.filter(event_type="cash.discrepancy_reviewed").count() == 1
assert {"cash.shift_opened", "cash.supplied", "cash.withdrawn", "cash.count_started", "cash.shift_closed", "cash.discrepancy_reviewed"}.issubset(set(events.values_list("event_type", flat=True)))
origins = json.loads(Path("artifacts/browser-origins.json").read_text())
assert not Payment.objects.filter(tab_id__in=origins["tab_ids"]).exists()
with connection.cursor() as cursor:
    cursor.execute("SELECT coalesce(sum(c.amount_cents),0) FROM ledger_charge c JOIN ordering_tab t ON t.id=c.tab_id WHERE t.venue_id=%s", [f["venue_id"]])
    venue_charges, = cursor.fetchone()
    cursor.execute("SELECT coalesce(sum(p.amount_cents),0) FROM ledger_payment p JOIN ordering_tab t ON t.id=p.tab_id WHERE t.venue_id=%s AND p.status IN ('CONFIRMED','PARTIALLY_REFUNDED','REFUNDED')", [f["venue_id"]])
    venue_payments, = cursor.fetchone()
assert r["report_totals"]["net_sales_cents"] == venue_charges
assert r["report_totals"]["paid_cents"] == venue_payments == r["paid_cents"]
assert r["report_totals"]["current_open_exposure_cents"] == venue_charges - venue_payments + refund.amount_cents
assert r["report_totals"]["refunds_cents"] == refund.amount_cents
r.update(charge_ids=[str(x) for x in Charge.objects.filter(tab=tab).values_list("pk",flat=True)], order_ids=[str(x) for x in Order.objects.filter(tab=tab).values_list("pk",flat=True)], database_instance_id=f["database_instance_id"], database=f["database"], venue_id=f["venue_id"], audit_event_ids=[str(e.pk) for e in events], cash_movement_ids=[str(m.pk) for m in movements], status="PASS")
cutoff = json.loads(Path("artifacts/cash-cutoff-browser.json").read_text())
assert cutoff["sha"] == r["sha"] and cutoff["database_instance_id"] == f["database_instance_id"]
policy = cutoff["policy"]
assert venue.timezone == policy["original_timezone"] and venue.business_day_cutoff_hour == policy["original_cutoff_hour"]
dates = []
for entry in cutoff["shifts"]:
    controlled = CashShift.objects.get(pk=entry["id"],cash_point_id=cutoff["cash_point_id"],cash_point__venue_id=f["venue_id"],status="CLOSED")
    day = (controlled.opened_at.astimezone(ZoneInfo(policy["test_timezone"])) - timedelta(hours=policy[entry["phase"]+"_cutoff_hour"])).date()
    assert controlled.business_date == day and str(day) == entry["business_date"]
    assert controlled.expected_amount_cents_snapshot == controlled.counted_amount_cents == 0 and controlled.discrepancy_cents == 0
    assert controlled.movements.count() == 1 and controlled.movements.get().kind == "OPENING_FLOAT" and controlled.movements.get().amount_cents == 0
    dates.append(day)
assert dates[1]-dates[0] == timedelta(days=1)
cutoff.update(sql_independent=True, status="PASS", original_policy_restored=True)
Path("artifacts/cash-cutoff-sql.json").write_text(json.dumps(cutoff,indent=2)+"\n")
roles.update(sql_independent=True, business_date=str(expected_business_date), cutoff_hour=venue.business_day_cutoff_hour, status="PASS")
Path("artifacts/financial-roles-sql.json").write_text(json.dumps(roles, indent=2)+"\n")
from modules.dispatch.models import DispatchTask
projection = json.loads(Path("artifacts/projection-browser.json").read_text())
assert projection["sha"] == r["sha"] and projection["database_instance_id"] == f["database_instance_id"]
assert projection["attendance_ready_ui"] == projection["management_ready_ui"] == 7 and projection["guest_ready_ui"] is True
tasks = DispatchTask.objects.filter(venue_id=f["venue_id"], task_type="DELIVERY")
assert tasks.count() == 7 and {str(t.pk) for t in tasks} == set(projection["dispatch_ids"])
assert {str(t.order_item_id) for t in tasks} == set(projection["item_ids"])
assert all(t.state == "OPEN" and t.ready_at and not t.completed_at and not t.completed_by_id and not t.completion_source and t.order_item.state == "READY" for t in tasks)
assert AuditEvent.objects.filter(venue_id=f["venue_id"], event_type="dispatch.delivery_created", entity_id__in=projection["dispatch_ids"], actor_session_id__isnull=False).count() == 7
assert not AuditEvent.objects.filter(venue_id=f["venue_id"], event_type="dispatch.delivery_completed").exists()
projection.update(sql_independent=True, status="PASS")
Path("artifacts/projection-sql.json").write_text(json.dumps(projection,indent=2)+"\n")
Path("artifacts/financial-sql.json").write_text(json.dumps(r, indent=2) + "\n")
print("PASS: partial/residual CASH test payments=2, compensatory Refund=1, drawer movements=6, preserved -1000 discrepancy, other Tab ledgers untouched")
