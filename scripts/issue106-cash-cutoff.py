#!/usr/bin/env python3
"""Controlled fixture calendar settings; actual UI/server clock remains real."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from cross_surface_fixture import require_disposable_database, require_connected_database, database_instance_identity
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection
from modules.venue.models import Venue
require_connected_database(connection)
f=json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
assert f["database_instance_id"]==database_instance_identity(connection)
v=Venue.objects.get(pk=f["venue_id"],slug="android-post-drop-ci")
p=Path("artifacts/cash-cutoff-control.json")
sha=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
action=sys.argv[1]
if action=="prepare":
    assert not p.exists(), "Preserve previous calendar evidence before a fresh run"
    for zone in ("America/Sao_Paulo","UTC","Pacific/Honolulu"):
        hour=datetime.now(timezone.utc).astimezone(ZoneInfo(zone)).hour
        if 1<=hour<=21: break
    else: raise RuntimeError("No safe fixture cutoff window")
    c={"sha":sha,"database_instance_id":f["database_instance_id"],"venue_id":str(v.pk),"test_timezone":zone,
       "before_cutoff_hour":hour+2,"after_cutoff_hour":hour-1,"original_timezone":v.timezone,
       "original_cutoff_hour":v.business_day_cutoff_hour,"status":"PREPARED"}
    p.write_text(json.dumps(c,indent=2)+"\n")
else:
    assert action in ("before","after","restore")
    c=json.loads(p.read_text())
    assert c["sha"]==sha and c["database_instance_id"]==f["database_instance_id"] and c["venue_id"]==str(v.pk)
    v.timezone=c["original_timezone"] if action=="restore" else c["test_timezone"]
    v.business_day_cutoff_hour=c["original_cutoff_hour"] if action=="restore" else c[action+"_cutoff_hour"]
    v.save(update_fields=["timezone","business_day_cutoff_hour"])
print(json.dumps(c))
