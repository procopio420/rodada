#!/usr/bin/env python3
"""Real HTTP shift. No mocks, SQL writes, provider callbacks or actual settlement.

Uses test-only identities provisioned by seed_release_demo. Prints sanitized
financial evidence; access/session credentials stay in process memory.
"""

import argparse
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:18764")
parser.add_argument("--evidence", default="/tmp/rodada-demo-shift.json")
parser.add_argument(
    "--verify", action="store_true", help="Verify recorded shift after stack restart"
)
args = parser.parse_args()


def request(path, body=None, token=None, method=None, expected=(200, 201, 202)):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(
        args.url + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        response = urlopen(req, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        result = json.load(response)
        assert response.status in expected, (path, response.status, result)
        return result


def login(identifier, pin, venue="release-demo"):
    result = request(
        "/auth/login/",
        {
            "venue_slug": venue,
            "login_identifier": identifier,
            "pin": pin,
            "installation_id": "release-" + uuid.uuid4().hex,
            "platform": "ANDROID",
        },
    )
    return result["access_token"]


owner = login("release-owner", "2468")


def api(path, body=None, **kwargs):
    return request(path, body, owner, **kwargs)


def verify(evidence):
    for tab_id in evidence["tabs"]:
        tab = api(f"/tabs/{tab_id}/")
        assert tab["state"] == "CLOSED" and tab["exposure_cents"] == 0, tab
        computed = (
            tab["charges_cents"]
            + tab["adjustments_cents"]
            - tab["payments_cents"]
            + tab["refunds_cents"]
            + tab["transfers_cents"]
        )
        assert computed == 0
    shift = api(f"/cash/shifts/{evidence['shift_id']}/")
    assert shift["status"] == "CLOSED" and shift["discrepancy_cents"] == 0
    report = api(
        f"/management/reports/?start={evidence['business_date']}&end={evidence['business_date']}"
    )
    assert report["totals"] == evidence["report_totals"], report["totals"]
    print(
        json.dumps(
            {
                "verified_persistence": True,
                "run_id": evidence["run_id"],
                "report_totals": report["totals"],
            }
        )
    )


if args.verify:
    verify(json.loads(Path(args.evidence).read_text()))
    raise SystemExit

run_id = uuid.uuid4().hex[:10]
staff = login("release-staff", "1357")
me = request("/auth/me/", token=staff)
assert me["device"]["trust_state"] == "UNTRUSTED"
assert me["device"]["platform"] == "ANDROID"
# This is the Android protocol via HTTP, not a claim of native device interaction.
api("/auth/reauthenticate/", {"pin": "2468"})
for kind, limit in [("VISITOR", 20000), ("HOUSE", 1200)]:
    api("/house-account/policies/", {"kind": kind, "limit_cents": limit}, method="PUT")
business_date = api("/management/calendar/")["business_date"]
before = api(f"/management/reports/?start={business_date}&end={business_date}")["totals"]
point = api("/cash/points/create/", {"label": "QA " + run_id})
shift = api(
    "/cash/shifts/",
    {
        "cash_point_id": point["id"],
        "opening_float_cents": 10000,
        "business_date": business_date,
        "idempotency_key": run_id + "-shift",
    },
)


def product(label, price, station):
    result = api(
        "/catalog/resolve-or-create/",
        {"name": label + " " + run_id, "price_cents": price, "fulfillment_station": station},
    )
    return result["product"]["id"]


bar = product("QA Beer", 1200, "BAR")
kitchen = product("QA Burger", 2000, "KITCHEN")
cancel = product("QA Wrong item", 600, "KITCHEN")


def configure(kind, values, **extra):
    return api(
        f"/catalog/products/{kitchen}/customization/", {"kind": kind, "values": values, **extra}
    )["id"]


variant = configure("variant", {"name": "Double", "price_cents": 3000})
group = configure(
    "group", {"name": "Extras", "selection_mode": "MULTI", "min_selections": 1, "max_selections": 2}
)
option = configure("option", {"name": "Bacon", "price_delta_cents": 500}, group_id=group)
tab = request("/tabs/", {}, staff)
assert tab["display_label"] == ""
dest = api("/tabs/", {"display_label": "Split " + run_id})
table = api("/hospitality/tables/", {"label": "QA " + run_id, "guest_ordering_mode": "DIRECT"})
occupancy = api(f"/hospitality/tables/{table['id']}/occupy/", {})
for current in (tab, dest):
    api(f"/hospitality/occupancies/{occupancy['id']}/tabs/", {"tab_id": current["id"]})
baseline = api("/realtime/snapshot/")["cursor"]
order_path = f"/tabs/{tab['id']}/orders/confirm/"
cart = {
    "idempotency_key": run_id + "-order",
    "lines": [
        {"product_id": bar, "quantity": 2},
        {
            "product_id": kitchen,
            "quantity": 1,
            "variant_id": variant,
            "modifier_option_ids": [option],
        },
        {"product_id": cancel, "quantity": 1},
    ],
}
# Concurrent retransmissions after an ambiguous response must share one identity.
with ThreadPoolExecutor(max_workers=2) as pool:
    orders = list(pool.map(lambda _: request(order_path, cart, staff), range(2)))
assert orders[0]["id"] == orders[1]["id"]
order = orders[0]
assert sum(item["line_total_cents"] for item in order["items"]) == 6500
items = {item["product_id"]: item for item in order["items"]}
assert items[kitchen]["unit_price_cents"] == 3500
for station, selected in [("BAR", [bar]), ("KITCHEN", [kitchen, cancel])]:
    queue = api("/production/" + station + "/")["results"]
    ids = {row["id"] for row in queue}
    assert all(items[p]["id"] in ids for p in selected)
    assert (
        all(row["product_id"] != bar for row in queue)
        if station == "KITCHEN"
        else all(row["product_id"] != kitchen for row in queue)
    )
    for row in queue:
        if row["id"] == items[kitchen]["id"]:
            assert row["customization_snapshot"] == items[kitchen]["customization_snapshot"]


def sse(cursor):
    req = Request(
        args.url + "/realtime/stream/?once=1&cursor=" + cursor,
        headers={"Authorization": "Bearer " + owner, "Accept": "text/event-stream"},
    )
    with urlopen(req, timeout=15) as response:
        return response.read().decode()


for _ in range(30):
    events = sse(baseline)
    if "order.confirmed" in events:
        break
    time.sleep(0.2)
assert "order.confirmed" in events
# Disconnect: retain cursor, mutate states, then recover missed facts.
resume = api("/realtime/snapshot/")["cursor"]
for p in (bar, kitchen):
    for state in ("ACCEPTED", "PREPARING", "READY"):
        api(f"/order-items/{items[p]['id']}/transition/", {"state": state})
for _ in range(30):
    replay = sse(resume)
    if "order_item." in replay:
        break
    time.sleep(0.2)
assert "order_item." in replay
assert "event: reset" in sse("unknown-cursor")


# Complete real delivery work so a closed shift leaves no prepared QA items behind.
def deliver(item_id):
    tasks = api("/dispatch/delivery/")["results"]
    task = next(row for row in tasks if row["order_item_id"] == item_id)
    completed = api(f"/dispatch/delivery/{task['id']}/complete/", {})
    assert completed["state"] == "DONE"


for p in (bar, kitchen):
    deliver(items[p]["id"])

# Split before payments: the original Charge/Order history stays on source.
source_state = api(f"/tabs/{tab['id']}/operations/")
dest_state = api(f"/tabs/{dest['id']}/operations/")
bar_charge = next(row for row in source_state["lines"] if row["order_item_id"] == items[bar]["id"])[
    "charge_id"
]
split_body = {
    "kind": "SPLIT",
    "idempotency_key": run_id + "-split",
    "expected_version": source_state["tab"]["version"],
    "destination_tab_id": dest["id"],
    "destination_version": dest_state["tab"]["version"],
    "lines": [{"charge_id": bar_charge, "quantity": 1}],
}
split = api(f"/tabs/{tab['id']}/operations/", split_body)
assert split["amount_cents"] == 1200
assert api(f"/tabs/{tab['id']}/operations/", split_body) == split
# Stale Product/option cannot generate a new charge, but old intent remains replayable.
api(
    f"/catalog/products/{kitchen}/customization/option/{option}/availability/",
    {"state": "UNAVAILABLE", "expected_version": 1, "reason": "QA stale choice"},
)
blocked = request(
    order_path, {**cart, "idempotency_key": run_id + "-stale-option"}, staff, expected=(409,)
)
assert blocked["code"] == "MODIFIER_UNAVAILABLE"
api(
    f"/catalog/products/{bar}/availability/", {"state": "UNAVAILABLE", "reason": "QA stale catalog"}
)
blocked = request(
    order_path,
    {"idempotency_key": run_id + "-stale-product", "lines": [{"product_id": bar, "quantity": 1}]},
    staff,
    expected=(409,),
)
assert blocked["code"] == "PRODUCTS_NOT_CONFIRMABLE"
assert request(order_path, cart, staff)["id"] == order["id"]
api(f"/catalog/products/{bar}/availability/", {"state": "AVAILABLE"})
# MANUAL_TEST: staff-confirmed terminal fallback, no provider settlement asserted.
payment_body = {
    "amount_cents": 1000,
    "method": "EXTERNAL_TERMINAL",
    "idempotency_key": run_id + "-partial",
}
with ThreadPoolExecutor(max_workers=2) as pool:
    partials = list(pool.map(lambda _: api(f"/tabs/{tab['id']}/payments/", payment_body), range(2)))
assert partials[0]["id"] == partials[1]["id"]
correction = api(
    f"/order-items/{items[cancel]['id']}/corrections/cancel/",
    {
        "kind": "WRONG_ITEM_ENTERED",
        "reason_code": "DUPLICATE_ENTRY",
        "reason_text": "QA test correction",
        "idempotency_key": run_id + "-correct",
    },
)
assert correction["financial_disposition"] == "REFUND_REQUIRED"
api("/auth/reauthenticate/", {"pin": "2468"})
refund_body = {
    "payment_id": partials[0]["id"],
    "amount_cents": 600,
    "refund_idempotency_key": run_id + "-refund",
}
refund = api(f"/corrections/{correction['id']}/settle-refund/", refund_body)
assert (
    api(f"/corrections/{correction['id']}/settle-refund/", refund_body)["refund_id"]
    == refund["refund_id"]
)
assert refund["exposure_cents"] == 4300
# House account: hit limit, reject, partial restores capacity, consume again.
customer = api("/customers/", {"display_name": "QA House " + run_id, "kind": "HOUSE"})
house = request("/tabs/", {"customer_id": customer["id"]}, staff)
house_path = f"/tabs/{house['id']}/orders/confirm/"
house_cart = {"idempotency_key": run_id + "-house-1", "lines": [{"product_id": bar, "quantity": 1}]}
house_first = request(house_path, house_cart, staff)
blocked = request(
    house_path, {**house_cart, "idempotency_key": run_id + "-house-block"}, staff, expected=(409,)
)
assert blocked["code"] == "SPENDING_LIMIT_EXCEEDED"
api(
    f"/tabs/{house['id']}/payments/",
    {
        "amount_cents": 1200,
        "method": "EXTERNAL_TERMINAL",
        "idempotency_key": run_id + "-house-partial",
    },
)
house_second = request(house_path, {**house_cart, "idempotency_key": run_id + "-house-2"}, staff)
# Prepaid work must finish even after financial closure (release regression).
api(
    f"/tabs/{house['id']}/payments/",
    {
        "amount_cents": 1200,
        "method": "EXTERNAL_TERMINAL",
        "idempotency_key": run_id + "-house-final",
    },
)
api(f"/tabs/{house['id']}/close/", {})
for house_order in (house_first, house_second):
    for item in house_order["items"]:
        for state in ("ACCEPTED", "READY"):
            api(f"/order-items/{item['id']}/transition/", {"state": state})
        deliver(item["id"])
# Resolve another venue with an authorized identity; then test forbidden access from original venue.
other = login("release-owner", "2468", "release-other")
other_tab = request("/tabs/", {}, other)
assert request(f"/tabs/{other_tab['id']}/", token=staff, expected=(404,))["code"] == "TAB_NOT_FOUND"
assert (
    request(f"/tabs/{other_tab['id']}/payments/", payment_body, owner, expected=(404,))["code"]
    == "TAB_NOT_FOUND"
)
request(f"/tabs/{other_tab['id']}/close/", {}, other)
# Close all QA financial responsibility with auditable manual/test payments.
for current in (tab, dest, house):
    detail = api(f"/tabs/{current['id']}/")
    if detail["state"] == "CLOSED":
        assert detail["exposure_cents"] == 0
        continue
    body = {
        "amount_cents": detail["exposure_cents"],
        "method": "CASH" if current == tab else "EXTERNAL_TERMINAL",
        "cash_point_id": point["id"],
        "amount_tendered_cents": detail["exposure_cents"],
        "idempotency_key": run_id + "-final-" + current["id"],
    }
    paid = api(f"/tabs/{current['id']}/payments/", body)
    api(f"/tabs/{current['id']}/close/", {})
    assert api(f"/tabs/{current['id']}/payments/", body)["id"] == paid["id"]
# Clients restart by logging in again and reloading canonical projections.
owner = login("release-owner", "2468")
assert api("/hospitality/tables/")["results"]
assert (
    next(row for row in api("/hospitality/tables/")["results"] if row["id"] == table["id"])[
        "status"
    ]
    == "OCCUPIED"
)
api(f"/hospitality/tables/{table['id']}/release/", {})
api(f"/hospitality/tables/{table['id']}/cleaning/start/", {})
api(f"/hospitality/tables/{table['id']}/cleaning/complete/", {})
count = api(f"/cash/shifts/{shift['id']}/count/start/", {})
closed = api(
    f"/cash/shifts/{shift['id']}/close/",
    {"counted_amount_cents": 14300, "expected_version": count["version"]},
)
assert closed["discrepancy_cents"] == 0
report = api(f"/management/reports/?start={business_date}&end={business_date}")["totals"]
expected_delta = {
    "gross_cents": 8900,
    "adjustments_cents": -600,
    "net_sales_cents": 8300,
    "paid_cents": 8900,
    "refunds_cents": 600,
    "net_received_cents": 8300,
    "current_open_exposure_cents": 0,
    "current_open_tabs": 0,
}
for key, delta in expected_delta.items():
    assert report[key] - before[key] == delta, (key, before[key], report[key], delta)
api("/auth/reauthenticate/", {"pin": "2468"})
audit = api("/manage/access/audit/")["results"]
assert {"payment.collected", "tab.closed", "payment.refunded"} <= {
    row["event_type"] for row in audit
}
assert all(
    row["actor_staff_id"] and row["actor_session_id"]
    for row in audit
    if row["event_type"] == "payment.collected"
)
# Session revocation via public API denies mutations on a formerly valid BYOD session.
api("/manage/access/sessions/" + me["session"]["id"] + "/revoke/", {"reason": "QA revoke"})
request("/tabs/", {}, staff, expected=(401, 403))
evidence = {
    "run_id": run_id,
    "payment_classification": "MANUAL_TEST",
    "native_android_ui": "NOT_RUN",
    "tabs": [tab["id"], dest["id"], house["id"]],
    "shift_id": shift["id"],
    "business_date": business_date,
    "report_totals": report,
    "report_delta": expected_delta,
    "cash_expected_cents": 14300,
    "cash_discrepancy_cents": 0,
    "sse_replay": True,
    "duplicate_order": order["id"],
    "duplicate_payment": partials[0]["id"],
    "audit_events_observed": len(audit),
}
Path(args.evidence).write_text(json.dumps(evidence, indent=2) + "\n")
verify(evidence)
print(json.dumps(evidence, indent=2))
