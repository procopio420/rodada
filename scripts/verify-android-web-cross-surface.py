#!/usr/bin/env python3
"""Independent SQL reconciliation after real Android instrumentation -> Web Bar UI.

Only read an explicitly disposable database. This script must never seed a Venue,
simulate a payment, or accept a browser-generated order as native evidence.
"""
import json
import os
from pathlib import Path

from cross_surface_fixture import (
    require_connected_database,
    require_disposable_database,
    require_fixture_order,
)

require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django

django.setup()
from django.db import connection

require_connected_database(connection)

from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, OrderItem

native = json.loads(Path("artifacts/android-real-post-drop.json").read_text())
assert native["result"] == "PASS" and native["original_key_preserved"]
order = Order.objects.get(pk=native["original_order_id"])
fixture = json.loads(Path(os.environ.get("RODADA_POST_DROP_FIXTURE", "/tmp/rodada-android-live-fixture.json")).read_text())
require_fixture_order(order, fixture)
assert fixture["database"] == connection.settings_dict["NAME"], "fixture from another database"
assert native["database"] == connection.settings_dict["NAME"], "receipt from another database"
assert native["venue_id"] == str(order.tab.venue_id), "receipt from another Venue"
assert str(order.tab_id) == native["original_tab_id"]
assert Order.objects.filter(tab_id=order.tab_id).count() == 1, "duplicate order"
items = OrderItem.objects.filter(order=order)
assert items.count() == 1, "duplicate item"
item = items.get()
assert str(item.product_id) == fixture["product_id"], "foreign fixture product"
assert item.state == "READY", f"Web did not persist READY; actual {item.state}"
charges = Charge.objects.filter(tab=order.tab)
assert charges.count() == 1, "duplicate charge"
assert charges.get().amount_cents == 700
assert Payment.objects.filter(tab=order.tab).count() == 0, "unconfirmed payment"
summary = {
    "database": connection.settings_dict["NAME"],
    "venue_id": str(order.tab.venue_id),
    "status": "PASS",
    "scenario": "Android native instrumented committed POST / force-stop / same-key replay -> Web Bar UI PREPARING then READY",
    "native_receipt": "artifacts/android-real-post-drop.json",
    "original_order_id": str(order.pk),
    "original_tab_id": str(order.tab_id),
    "original_order_item_id": str(item.pk),
    "final_item_state": item.state,
    "orders": 1,
    "items": 1,
    "charges": 1,
    "payments": 0,
    "charge_cents": 700,
    "scope": "disposable PostgreSQL, emulator and browser; not a physical/payment/fiscal pilot",
}
out = Path("artifacts/android-web-cross-surface.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print("PASS: native Android -> Web Bar -> SQL READY; Order=1 Item=1 Charge=1 Payment=0")
