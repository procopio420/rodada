#!/usr/bin/env python3
"""Database proof for the real Android start/open response loss, no mocked mutations."""
import json
import os
import sys
from pathlib import Path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from modules.hospitality.models import TableOccupancy, TabOccupancyAssignment, ServiceCommand
from modules.audit.models import AuditEvent
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order

mode, phase = sys.argv[1:3]
fixture = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
evidence = json.loads(Path(os.environ["RODADA_POST_DROP_MARKER"]).read_text())
assert evidence["mode"] == mode
assert evidence["armed"] == (phase == "before")
events = evidence["events"]
assert events and all(200 <= event["upstream_status"] < 300 for event in events)
assert len({event["idempotency_key"] for event in events}) == 1
assert len({event["body_sha256"] for event in events}) == 1
occupancy = TableOccupancy.objects.get(table_id=fixture["table_id"])
assert occupancy.released_at is None
assert occupancy.responsibility_version == 1
assert occupancy.responsible_staff_id
assignments = TabOccupancyAssignment.objects.filter(occupancy=occupancy)
assert assignments.count() == (0 if mode == "start" else 1)
assert AuditEvent.objects.filter(entity_id=str(occupancy.id), event_type="occupancy.responsibility_assigned").count() == 1
command = ServiceCommand.objects.get(venue=occupancy.table.venue, action=mode, key=events[0]["idempotency_key"])
assert command.result
for link in assignments:
    assert not Order.objects.filter(tab=link.tab).exists()
    assert not Charge.objects.filter(tab=link.tab).exists()
    assert not Payment.objects.filter(tab=link.tab).exists()
if phase == "after":
    assert evidence["replays"]
    for replay in evidence["replays"]:
        assert replay["idempotency_key"] == events[0]["idempotency_key"]
        assert replay["body_sha256"] == events[0]["body_sha256"]
    path = Path(f"artifacts/android-table-{mode}-response-loss.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"mode": mode, "occupancy_id": str(occupancy.id), "tabs": assignments.count(), "exactly_once": True, "transport": evidence}, indent=2))
print(f"PASS: {mode} {phase}: original key, exactly one occupancy, {assignments.count()} Tabs, no financial effect")
