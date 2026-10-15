#!/usr/bin/env python3
"""Reconcile test-only UI payments and cash close against independent PostgreSQL rows."""
import json
import os
from pathlib import Path
import subprocess
from cross_surface_fixture import require_disposable_database, require_connected_database
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection
from modules.cash.models import CashShift, CashMovement
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Tab
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
r = json.loads(Path("artifacts/financial-browser.json").read_text())
assert r["sha"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
assert r["test_only"] is True and f["database"] == connection.settings_dict["NAME"]
tab = Tab.objects.get(pk=r["tab_id"], venue_id=f["venue_id"], state="CLOSED")
payments = Payment.objects.filter(tab=tab)
assert payments.count() == 2 and {str(p.pk) for p in payments} == set(r["payment_ids"])
assert all(p.status == "CONFIRMED" and p.method == "CASH" and p.confirmed_at for p in payments)
assert sum(p.amount_cents for p in payments) == r["paid_cents"] == sum(c.amount_cents for c in Charge.objects.filter(tab=tab))
shift = CashShift.objects.get(pk=r["shift_id"], cash_point__venue_id=f["venue_id"])
assert shift.status == "CLOSED" and shift.review_status == "REVIEWED"
assert shift.expected_at_close_cents == r["expected_cents"]
assert shift.discrepancy_cents == r["discrepancy_cents"] == -1000
assert shift.counted_amount_cents == r["expected_cents"] - 1000
movements = CashMovement.objects.filter(shift=shift)
assert sorted(movements.values_list("kind", flat=True)) == ["CASH_PAYMENT", "CASH_PAYMENT", "OPENING_FLOAT", "SUPPLY", "WITHDRAWAL"]
assert sum(movements.values_list("amount_cents", flat=True)) == shift.expected_at_close_cents
assert set(str(x) for x in movements.exclude(payment_id=None).values_list("payment_id", flat=True)) == set(r["payment_ids"])
origins = json.loads(Path("artifacts/browser-origins.json").read_text())
assert not Payment.objects.filter(tab_id__in=origins["tab_ids"]).exists()
r.update(database=f["database"], venue_id=f["venue_id"], cash_movement_ids=[str(m.pk) for m in movements], status="PASS")
Path("artifacts/financial-sql.json").write_text(json.dumps(r, indent=2) + "\n")
print("PASS: partial/residual CASH test payments=2, drawer movements=5, preserved -1000 discrepancy, other Tab ledgers untouched")
