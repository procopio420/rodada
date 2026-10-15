#!/usr/bin/env python3
"""Independent SQL reconciliation of real HTTP races on the shared PostgreSQL."""
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
from modules.audit.models import AuditEvent
from modules.ordering.models import Tab
from modules.ledger.models import Charge, Payment
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
r = json.loads(Path("artifacts/concurrency-http.json").read_text())
assert r["sha"] == subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
assert r["database_instance_id"] == f["database_instance_id"] == database_instance_identity(connection)
ids = []
for kind in ("start", "claim"):
    visit = TableOccupancy.objects.get(table_id=f["race_tables"][kind], table__venue_id=f["venue_id"])
    assert visit.responsibility_version == 1 and visit.responsible_staff_id
    assert TabOccupancyAssignment.objects.filter(occupancy=visit).count() == 0
    events = AuditEvent.objects.filter(venue_id=f["venue_id"], entity_id=str(visit.pk), event_type="occupancy.responsibility_assigned")
    assert events.count() == 1 and events.get().actor_staff_id == visit.responsible_staff_id
    assert events.get().actor_session_id
    ids.append(str(visit.pk))
released = TableOccupancy.objects.get(pk=r["release_occupancy_id"], table_id=f["race_tables"]["release"], table__venue_id=f["venue_id"])
assert released.released_at and released.table.status == "DIRTY"
assert not TabOccupancyAssignment.objects.filter(occupancy=released, released_at=None).exists()
tabs = Tab.objects.filter(venue_id=f["venue_id"], display_label="Race open")
if r["release_open"][1]["status"] == 201:
    assert tabs.count() == 1 and TabOccupancyAssignment.objects.filter(tab=tabs.get(), occupancy=released).exclude(released_at=None).count() == 1
else:
    assert tabs.count() == 0
assert not Charge.objects.filter(tab__in=tabs).exists() and not Payment.objects.filter(tab__in=tabs).exists()
r.update(occupancy_ids=ids+[str(released.pk)], tab_ids=[str(t.pk) for t in tabs], status="PASS")
Path("artifacts/concurrency-sql.json").write_text(json.dumps(r, indent=2)+"\n")
print("PASS: one occupancy/owner per race, one claim audit, atomic release/open and no financial effects")
