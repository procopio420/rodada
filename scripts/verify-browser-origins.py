#!/usr/bin/env python3
"""Independent PostgreSQL assertions for shared Guest/Web origin and KDS recovery."""
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
from modules.hospitality.models import TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Order, OrderItem
from modules.ledger.models import Charge, Payment
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
r = json.loads(Path("artifacts/browser-origins.json").read_text())
assert r["sha"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
assert f["database_instance_id"] == database_instance_identity(connection)
assert f["database"] == connection.settings_dict["NAME"]
o = TableOccupancy.objects.get(pk=r["occupancy_id"], table_id=r["table_id"], table__venue_id=f["venue_id"])
assert set(str(x) for x in TabOccupancyAssignment.objects.filter(occupancy=o).values_list("tab_id", flat=True)) == set(r["tab_ids"])
orders = Order.objects.filter(pk__in=r["order_ids"], tab_id__in=r["tab_ids"], tab__venue_id=f["venue_id"])
assert orders.count() == 2 and {x.source for x in orders} == {"GUEST", "STAFF"}
for tab_id in r["tab_ids"]:
    assert Order.objects.filter(tab_id=tab_id).count() == 1
    items = OrderItem.objects.filter(order__tab_id=tab_id)
    assert items.count() == 2 and all(i.state == "READY" and i.preparing_at and i.ready_at and i.preparing_at <= i.ready_at for i in items)
    assert {str(i.product_id) for i in items} == {f["product_id"], f["kitchen_product_id"]}
    assert Charge.objects.filter(tab_id=tab_id).count() == 2
    with connection.cursor() as cursor:
        cursor.execute("SELECT sum(amount_cents) FROM ledger_charge WHERE tab_id = %s", [tab_id])
        assert cursor.fetchone() == (1700,)
    assert not Payment.objects.filter(tab_id=tab_id).exists()
assert r["changed_payload_status"] == 409
assert r["guest_replays"] == 2 and r["kitchen_reconnected"] is True
r.update(database_instance_id=f["database_instance_id"], database=f["database"], venue_id=f["venue_id"], status="PASS", orders=2, items=4, charges=4, payments=0)
Path("artifacts/browser-origins-sql.json").write_text(json.dumps(r, indent=2) + "\n")
print("PASS: Guest/Web share one occupancy, independent 1700-cent ledgers, 2 Orders/4 READY Items/4 Charges/0 Payments")
