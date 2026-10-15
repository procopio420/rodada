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
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Tab
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
assert all(p.status == "CONFIRMED" and p.method == "CASH" and p.confirmed_at for p in payments)
assert sorted(p.amount_cents for p in payments) == [300, r["paid_cents"] - 300]
assert sum(p.amount_cents for p in payments) == r["paid_cents"] == sum(c.amount_cents for c in Charge.objects.filter(tab=tab))
shift = CashShift.objects.get(pk=r["shift_id"], cash_point__venue_id=f["venue_id"])
assert shift.status == "CLOSED" and shift.review_status == "REVIEWED"
assert shift.expected_amount_cents_snapshot == r["expected_cents"]
assert shift.discrepancy_cents == r["discrepancy_cents"] == -1000
assert shift.counted_amount_cents == r["expected_cents"] - 1000
movements = CashMovement.objects.filter(shift=shift)
assert sorted(movements.values_list("kind", flat=True)) == ["CASH_PAYMENT", "CASH_PAYMENT", "OPENING_FLOAT", "SUPPLY", "WITHDRAWAL"]
assert sum(movements.values_list("amount_cents", flat=True)) == shift.expected_amount_cents_snapshot
assert set(str(x) for x in movements.exclude(payment_id=None).values_list("payment_id", flat=True)) == set(r["payment_ids"])
staff = StaffMember.objects.get(login_identifier="android-post-drop-operator")
assert shift.opened_by_id == shift.closed_by_id == shift.reviewed_by_id == staff.pk
assert shift.closed_at and shift.reviewed_at and shift.review_reason
assert all(m.actor_id == staff.pk and m.actor_session_id for m in movements)
events = AuditEvent.objects.filter(venue_id=f["venue_id"], entity_id=str(shift.pk), actor_staff=staff).exclude(actor_session_id=None)
assert {"cash.shift_opened", "cash.supplied", "cash.withdrawn", "cash.count_started", "cash.shift_closed", "cash.discrepancy_reviewed"}.issubset(set(events.values_list("event_type", flat=True)))
origins = json.loads(Path("artifacts/browser-origins.json").read_text())
assert not Payment.objects.filter(tab_id__in=origins["tab_ids"]).exists()
r.update(database_instance_id=f["database_instance_id"], database=f["database"], venue_id=f["venue_id"], audit_event_ids=[str(e.pk) for e in events], cash_movement_ids=[str(m.pk) for m in movements], status="PASS")
Path("artifacts/financial-sql.json").write_text(json.dumps(r, indent=2) + "\n")
print("PASS: partial/residual CASH test payments=2, drawer movements=5, preserved -1000 discrepancy, other Tab ledgers untouched")
