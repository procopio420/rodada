#!/usr/bin/env python3
"""Read-only negative SQL proof for shared-fixture Web auth/tenant scenarios."""
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
from modules.access.models import StaffSession
from modules.ordering.models import Tab, Order
from modules.ledger.models import Charge, Payment
from modules.audit.models import AuditEvent
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
for scenario in ("isolation", "guest-isolation", "revocation"):
    r = json.loads(Path(f"artifacts/{scenario}-browser.json").read_text())
    assert r["sha"] == sha and r["database_instance_id"] == f["database_instance_id"] == database_instance_identity(connection)
    if scenario in ("isolation", "guest-isolation"):
        ids = r["tab_ids"]
        assert Tab.objects.get(pk=ids[0]).venue_id == Tab.objects.get(pk=ids[0], venue_id=f["venue_id"]).venue_id
        assert str(Tab.objects.get(pk=ids[1]).venue_id) == f["foreign_venue_id"]
    else:
        ids = [r["tab_id"]]
        assert Tab.objects.get(pk=ids[0], venue_id=f["venue_id"])
        session = StaffSession.objects.get(pk=r["session_id"], venue_id=f["venue_id"])
        assert session.revoked_at and session.revocation_reason == "LOGOUT"
        assert AuditEvent.objects.filter(venue_id=f["venue_id"], event_type="auth.session_revoked", actor_session_id=session.pk).count() == 1
    assert not Order.objects.filter(tab_id__in=ids).exists()
    assert not Charge.objects.filter(tab_id__in=ids).exists()
    assert not Payment.objects.filter(tab_id__in=ids).exists()
    r.update(orders=0, charges=0, payments=0, sql_independent=True)
    Path(f"artifacts/{scenario}-sql.json").write_text(json.dumps(r, indent=2)+"\n")
print("PASS: both Venue controls unchanged; revoked-session UI intent preserved; no Order/Charge/Payment")
