#!/usr/bin/env python3
"""Real concurrent HTTP commands on the existing shared fixture; no simulated client UI."""
import json
import os
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4
from cross_surface_fixture import require_disposable_database, require_connected_database, database_instance_identity
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection
require_connected_database(connection)
# Reuse the existing real barrier/separate-connection harness; do not duplicate it.
from tests.test_table_service_concurrency import race
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
assert f["database_instance_id"] == database_instance_identity(connection)
base = "http://127.0.0.1:8101"


def api(path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            return {"status": response.status, "body": json.load(response)}
    except HTTPError as error:
        return {"status": error.code, "body": json.load(error)}


def login(identifier):
    r = api("/auth/login/", {"venue_slug": f["venue_slug"], "login_identifier": identifier,
        "pin": "2468", "installation_id": "issue106-race-" + identifier, "platform": "WEB"})
    assert r["status"] == 200
    return r["body"]["access_token"]


tokens = [login("android-post-drop-operator"), login("android-post-drop-other")]
start_id = f["race_tables"]["start"]
started = race(*(lambda token=token: api(f"/hospitality/tables/{start_id}/service/start/", {"idempotency_key": str(uuid4())}, token) for token in tokens))
assert sorted(r["status"] for r in started) == [201, 409]
assert next(r for r in started if r["status"] == 409)["body"]["code"] == "OCCUPANCY_ALREADY_ACTIVE"
claimed = race(*(lambda token=token: api(f"/hospitality/occupancies/{f['claim_occupancy_id']}/responsibility/claim/", {"idempotency_key":str(uuid4()),"expected_responsibility_version":0,"mode":"CLAIM_UNASSIGNED"}, token) for token in tokens))
assert sorted(r["status"] for r in claimed) == [201, 409]
assert next(r for r in claimed if r["status"] == 409)["body"]["code"] == "RESPONSIBILITY_CONFLICT"
release_id = f["race_tables"]["release"]
pre = api(f"/hospitality/tables/{release_id}/service/start/", {"idempotency_key": str(uuid4())}, tokens[0])
assert pre["status"] == 201
occupancy_id = pre["body"]["active_occupancy"]["id"]
released = race(lambda: api(f"/hospitality/tables/{release_id}/release/", {}, tokens[0]), lambda: api(f"/hospitality/occupancies/{occupancy_id}/tabs/open/", {"idempotency_key":str(uuid4()),"expected_generation":1,"display_label":"Race open"}, tokens[1]))
assert released[0]["status"] == 200
assert released[1]["status"] in (201,409)
if released[1]["status"] == 409:
    assert released[1]["body"]["code"] == "OCCUPANCY_RELEASED"
# Never serialize bearer/session credentials. Only canonical result IDs/codes.
summary = {"sha":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(), "database_instance_id":f["database_instance_id"],"venue_id":f["venue_id"],"start":started,"claim":claimed,"release_open":released,"release_occupancy_id":occupancy_id,"status":"PASS","transport":"real concurrent HTTP, shared PostgreSQL, existing Barrier harness"}
Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/concurrency-http.json").write_text(json.dumps(summary,indent=2)+"\n")
print("PASS: actual shared-backend HTTP start/start, claim/claim CAS and release/open races")
