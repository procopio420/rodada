"""Live ASGI/PostgreSQL smoke. Run against a disposable migrated database.

POSTGRES_DB=rodada_realtime_verification python scripts/verify_realtime.py
The same environment must be used by the running API on localhost:18764.
"""

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django

django.setup()
from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import Product
from modules.hospitality.models import GuestOrderingMode, Table
from modules.ordering.models import Tab
from modules.realtime.models import OutboxEvent
from modules.venue.models import Venue

BASE = os.environ.get("REALTIME_API_URL", "http://127.0.0.1:18764")


def api(path, data=None, headers=None):
    req = Request(
        BASE + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urlopen(req, timeout=10) as response:
        return json.load(response)


def stream(path, cursor, headers):
    return urlopen(
        Request(
            BASE + path + "?cursor=" + cursor, headers={"Accept": "text/event-stream", **headers}
        ),
        timeout=10,
    )


def until(connection, wanted):
    event, payload, cursor = "", None, ""
    while True:
        line = connection.readline().decode().strip()
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("id: "):
            cursor = line[4:]
        elif line.startswith("data: "):
            payload = json.loads(line[6:])
        elif not line and event:
            if event == wanted:
                return payload, cursor
            event, payload = "", None


suffix = uuid.uuid4().hex[:8]
venue = Venue.objects.create(name="Realtime integration", slug="rt-" + suffix)
staff = StaffMember.objects.create(display_name="Integration", login_identifier="rt-" + suffix)
staff.set_pin("1234")
staff.save(update_fields=["pin_hash"])
VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role=StaffRole.MANAGER)
product = Product.objects.create(
    venue=venue, name="Beer", price_cents=1200, fulfillment_station="BAR"
)
table = Table.objects.create(
    venue=venue, label="Smoke", guest_ordering_mode=GuestOrderingMode.DIRECT
)
login = api(
    "/auth/login/",
    {
        "venue_slug": venue.slug,
        "login_identifier": staff.login_identifier,
        "pin": "1234",
        "installation_id": "rt-" + suffix,
        "platform": "WEB",
    },
)
auth = {"Authorization": "Bearer " + login["access_token"]}
guest = api("/guest/qr/resolve/", {"token": table.public_token})
guest_auth = {"X-Guest-Session": guest["guest_session_token"]}
tab = api("/guest/tabs/", {"display_label": "Smoke guest"}, guest_auth)
baseline = api("/guest/realtime/snapshot/", headers=guest_auth)["cursor"]
with stream("/guest/realtime/stream/", baseline, guest_auth) as live:
    until(live, "ready")
    started = time.monotonic()
    payload = {
        "idempotency_key": "rt-" + suffix,
        "lines": [{"product_id": str(product.id), "quantity": 1}],
    }
    order = api("/guest/orders/confirm/", payload, guest_auth)
    events = OutboxEvent.objects.filter(venue=venue)
    assert events.filter(event_type="order.confirmed", published_at__isnull=True).exists()
    # Publication in a distinct process proves facts survive command process lifetime.
    subprocess.run(
        [sys.executable, "manage.py", "dispatch_realtime", "--once"],
        check=True,
        capture_output=True,
    )
    change, accepted = until(live, "change")
    assert change["aggregate_id"] == order["id"]
    delivery_ms = round((time.monotonic() - started) * 1000)
    assert api("/guest/orders/confirm/", payload, guest_auth)["id"] == order["id"]
item = order["items"][0]["id"]
api(f"/order-items/{item}/transition/", {"state": "ACCEPTED"}, auth)
api(f"/order-items/{item}/transition/", {"state": "READY"}, auth)
subprocess.run(
    [sys.executable, "manage.py", "dispatch_realtime", "--once"], check=True, capture_output=True
)
with stream("/guest/realtime/stream/", accepted, guest_auth) as replay:
    missed, _ = until(replay, "change")
    assert missed["aggregate_id"] == item
snapshot = api("/guest/realtime/snapshot/", headers=guest_auth)
assert snapshot["tab"]["exposure_cents"] == 1200
assert snapshot["tab"]["orders"][0]["items"][0]["state"] == "READY"
with stream("/guest/realtime/stream/", "invalid", guest_auth) as gap:
    reset, _ = until(gap, "reset")
    assert reset["snapshot_required"]
# A connected session is revoked on the next authenticated read, without a new request.
with stream("/guest/realtime/stream/", snapshot["cursor"], guest_auth) as revoked:
    until(revoked, "ready")
    api(f"/hospitality/tables/{table.id}/release/", {}, auth)
    until(revoked, "revoked")
assert Tab.objects.get(pk=tab["id"]).charges.count() == 1
print(
    json.dumps(
        {
            "passed": True,
            "confirmation_to_event_ms": delivery_ms,
            "verified": [
                "live_guest",
                "publication_process_restart",
                "duplicate_command",
                "replay",
                "reload_balance",
                "cursor_reset",
                "connected_revocation",
            ],
        }
    )
)
