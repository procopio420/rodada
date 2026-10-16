#!/usr/bin/env python3
"""Independently reconcile real QR/browser lifecycle actions in disposable PostgreSQL."""
import json
import os
import subprocess
from pathlib import Path
from cross_surface_fixture import require_disposable_database, require_connected_database, database_instance_identity
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection
from modules.audit.models import AuditEvent
from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Tab, Order
from modules.ledger.models import Charge, Payment
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
r = json.loads(Path("artifacts/qr-lifecycle-browser.json").read_text())
assert r["sha"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "stale browser receipt"
assert f["database_instance_id"] == database_instance_identity(connection)
assert f["database"] == connection.settings_dict["NAME"]
t = Table.objects.get(pk=r["table_id"], venue_id=f["venue_id"])
o = TableOccupancy.objects.get(pk=r["occupancy_id"], table=t)
assert TableOccupancy.objects.filter(table=t).count() == 2
new_visit = TableOccupancy.objects.get(pk=r["new_occupancy_id"], table=t, generation=r["final_generation"], released_at=None)
assert new_visit.pk != o.pk and new_visit.responsible_staff_id is None
assert TabOccupancyAssignment.objects.filter(occupancy=new_visit, tab_id=r["new_tab_id"]).count() == 1
assert r["cleaning_mode"] == "staged"
assert o.released_at and o.cleaning_started_at and o.ready_at and o.responsible_staff_id
assert o.released_at <= o.cleaning_started_at <= o.ready_at, "Cleaning timestamps out of lifecycle order"
assert t.status == "OCCUPIED" and t.access_generation == r["final_generation"] > r["initial_generation"]
assert set(str(x) for x in TabOccupancyAssignment.objects.filter(occupancy=o).values_list("tab_id", flat=True)) == set(r["tab_ids"])
assert Tab.objects.filter(pk__in=r["tab_ids"], venue_id=f["venue_id"], state="CLOSED").count() == 2
assert not Order.objects.filter(tab_id__in=r["tab_ids"]).exists()
assert not Charge.objects.filter(tab_id__in=r["tab_ids"]).exists()
assert not Payment.objects.filter(tab_id__in=r["tab_ids"]).exists()
events = list(AuditEvent.objects.filter(venue_id=f["venue_id"], entity_id=str(o.pk)).values("id", "event_type", "actor_staff_id"))
assert any(e["event_type"] == "occupancy.responsibility_assigned" and e["actor_staff_id"] for e in events), events
out = {**r, "database_instance_id": f["database_instance_id"], "database": f["database"], "venue_id": f["venue_id"], "orders": 0, "charges": 0, "payments": 0, "audit": events, "status": "PASS"}
Path("artifacts/qr-lifecycle-sql.json").write_text(json.dumps(out, default=str, indent=2) + "\n")
print("PASS: one visit, two closed independent Tabs, explicit release/cleaning, audited claim, zero financial effects")
