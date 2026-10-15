#!/usr/bin/env python3
"""Final read-only reconciliation after all shared-client and financial mutations.

Earlier receipts prove intermediate states (notably Payment=0 before payment).
This verifier proves their correlated orders and immutable charges still exist
at the end, with exactly the money and foreign-Venue effects exercised by UI.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from cross_surface_fixture import require_disposable_database, require_connected_database, database_instance_identity
from e2e_evidence import INVARIANTS

require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection, transaction
from modules.ordering.models import Order, OrderItem, Tab
from modules.ledger.models import Charge, Payment, Refund, LedgerAdjustment
from modules.cash.models import CashShift, CashMovement
from modules.guest_access.models import GuestSession
from modules.hospitality.models import Table, TableOccupancy
from modules.payment_provider.models import PaymentAttempt

require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
instance = database_instance_identity(connection)
assert instance == f["database_instance_id"]
sources = {}


def receipt(name):
    path = Path("artifacts") / name
    data = json.loads(path.read_text())
    assert data["sha"] == sha and data["database_instance_id"] == instance, name
    assert data.get("status", data.get("result")) == "PASS", name
    sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return data


recovery = receipt("android-web-cross-surface.json")
native = receipt("android-compose-order.json")
receipt("android-compose-web-sql.json")
receipt("android-context-readback-sql.json")
receipt("projection-sql.json")
origins = receipt("browser-origins-sql.json")
sse = receipt("sse-sql.json")
finance = receipt("financial-sql.json")
receipt("financial-roles-sql.json")
cutoff = receipt("cash-cutoff-sql.json")
receipt("pending-payment-sql.json")
qr = receipt("qr-lifecycle-sql.json")
receipt("concurrency-sql.json")
negative_tabs = []
for name in ("android-catalog", "android-offline-conflict", "android-offline-revocation", "unavailable-cart", "unavailable-staff", "revocation", "isolation", "guest-isolation"):
    r = receipt(name + "-sql.json")
    negative_tabs.extend(r.get("tab_ids", [r.get("tab_id")]))
negative_tabs = [x for x in negative_tabs if x]

expected_orders = {recovery["original_order_id"], native["original_order_id"], sse["order_id"], *origins["order_ids"]}
assert len(expected_orders) == 5
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        cursor.execute("SELECT id, tab_id FROM ordering_order WHERE tab_id IN (SELECT id FROM ordering_tab WHERE venue_id=%s)", [f["venue_id"]])
        orders = cursor.fetchall()
        assert {str(row[0]) for row in orders} == expected_orders
        assert len({row[1] for row in orders}) == 5
        cursor.execute("""SELECT i.id, i.order_id, i.quantity, i.unit_price_cents, i.state,
          i.preparing_at, i.ready_at, c.id, c.amount_cents, c.tab_id, o.tab_id
          FROM ordering_orderitem i JOIN ordering_order o ON o.id=i.order_id
          JOIN ordering_tab t ON t.id=o.tab_id LEFT JOIN ledger_charge c ON c.order_item_id=i.id
          WHERE t.venue_id=%s""", [f["venue_id"]])
        rows = cursor.fetchall()
        assert len(rows) == 8 and len({r[0] for r in rows}) == 8
        assert sum(r[8] for r in rows) == 6800
        for r in rows:
            assert r[2] == 1 and r[3] in (700, 1000) and r[7] and r[8] == r[2] * r[3] and r[9] == r[10]
            if str(r[1]) == sse["order_id"]:
                assert r[4] == "NEW" and r[5] is None and r[6] is None
            else:
                assert r[4] == "READY" and r[5] and r[6] and r[5] <= r[6]
        assert {str(r[7]) for r in rows if str(r[1]) == native["original_order_id"]} == set(native["charge_ids"])
        cursor.execute("""SELECT p.id, p.amount_cents, p.status, p.confirmed_at, p.provider, p.provider_payment_id
          FROM ledger_payment p JOIN ordering_tab t ON t.id=p.tab_id WHERE t.venue_id=%s""", [f["venue_id"]])
        payments = cursor.fetchall()
        assert len(payments) == 3 and all(not p[4] and not p[5] for p in payments)
        confirmed = [p for p in payments if p[2] in ("CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED")]
        pending = [p for p in payments if p[2] == "PENDING"]
        assert {str(p[0]) for p in confirmed} == set(finance["payment_ids"])
        assert sum(p[1] for p in confirmed) == 1800 and all(p[3] for p in confirmed)
        assert len(pending) == 1 and str(pending[0][0]) == f["pending_payment_id"] and pending[0][1] == 700 and pending[0][3] is None
    refunds = Refund.objects.filter(payment__tab__venue_id=f["venue_id"])
    assert refunds.count() == 1 and refunds.get().status == "CONFIRMED" and refunds.get().amount_cents == 100
    assert str(refunds.get().pk) == finance["refund_id"]
    assert not PaymentAttempt.objects.filter(payment__tab__venue_id=f["venue_id"]).exists()
    assert not LedgerAdjustment.objects.filter(tab__venue_id=f["venue_id"]).exists()
    assert not CashMovement.objects.filter(payment_id=f["pending_payment_id"]).exists()
    assert Tab.objects.get(pk=f["pending_tab_id"]).state == "OPEN"
    assert Tab.objects.get(pk=native["original_tab_id"]).state == "CLOSED"
    assert not Order.objects.filter(tab_id__in=negative_tabs).exists()
    assert not Charge.objects.filter(tab_id__in=negative_tabs).exists()
    assert not Payment.objects.filter(tab_id__in=negative_tabs).exists()
    for model in (Order, Charge, Payment, LedgerAdjustment):
        assert not model.objects.filter(tab__venue_id=f["foreign_venue_id"]).exists()
    shifts = CashShift.objects.filter(cash_point__venue_id=f["venue_id"])
    assert shifts.count() == 3 and {str(s.pk) for s in shifts} == {finance["shift_id"], *(s["id"] for s in cutoff["shifts"])}
    main = shifts.get(pk=finance["shift_id"])
    assert main.status == "CLOSED" and main.review_status == "REVIEWED"
    assert main.expected_amount_cents_snapshot == 12700 and main.counted_amount_cents == 11700 and main.discrepancy_cents == -1000
    assert main.movements.count() == 6 and sum(main.movements.values_list("amount_cents", flat=True)) == 12700
    assert CashMovement.objects.filter(shift__in=shifts).count() == 6
    assert not CashMovement.objects.filter(shift__in=shifts.exclude(pk=main.pk)).exists()
    old = GuestSession.objects.filter(occupancy_id=qr["occupancy_id"])
    table = Table.objects.get(pk=qr["table_id"], venue_id=f["venue_id"])
    assert old.exists() and TableOccupancy.objects.get(pk=qr["occupancy_id"]).released_at
    assert all(s.generation < table.access_generation for s in old)
    assert qr["revoked_status"] == 403 and table.access_generation == qr["final_generation"]
    assert GuestSession.objects.filter(occupancy_id=qr["new_occupancy_id"], tab_id=qr["new_tab_id"], revoked_at=None).exists()
    assert finance["report_totals"]["current_open_exposure_cents"] == 6800 - 1800 + 100 == 5100

output = {"sha":sha, "database_instance_id":instance, "status":"PASS", "sql_independent":True,
          "venue_id":f["venue_id"], "order_ids":sorted(expected_orders), "tab_ids":sorted(str(r[1]) for r in orders),
          "item_ids":sorted(str(r[0]) for r in rows), "charge_ids":sorted(str(r[7]) for r in rows),
          "payment_ids":sorted(str(p[0]) for p in payments), "charge_cents":6800, "confirmed_gross_cents":1800,
          "refund_cents":100, "open_exposure_cents":5100, "source_sha256":sources,
          "invariants":{name:"PASS" for name in sorted(INVARIANTS)},
          "scope":"disposable integrated automation only; external device/network/PSP/fiscal gates separate"}
Path("artifacts/final-state-sql.json").write_text(json.dumps(output,indent=2)+"\n")
print("PASS final SQL: 5 Orders / 8 immutable Charges 6800; 2 cash Payments 1800 - Refund 100; exposure 5100; foreign/denied effects zero")
