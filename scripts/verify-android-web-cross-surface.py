#!/usr/bin/env python3
"""Independent SQL reconciliation after real Android instrumentation -> Web Bar UI.

Only read an explicitly disposable database. This script must never seed a Venue,
simulate a payment, or accept a browser-generated order as native evidence.
"""
import json
import os
import subprocess
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

for mode in ("recovery", "compose"):
    native_path = "artifacts/android-real-post-drop.json" if mode == "recovery" else "artifacts/android-compose-order.json"
    native = json.loads(Path(native_path).read_text())
    assert native["sha"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "stale native receipt"
    assert native["result"] == "PASS"
    if mode == "recovery":
        assert native["original_key_preserved"]
    else:
        assert native["native_ui"] == "production MainActivity Compose"
    order = Order.objects.get(pk=native["original_order_id"])
    fixture = json.loads(Path(os.environ.get("RODADA_POST_DROP_FIXTURE", "/tmp/rodada-android-live-fixture.json")).read_text())
    require_fixture_order(order, fixture)
    assert fixture["database"] == connection.settings_dict["NAME"], "fixture from another database"
    assert native["database"] == connection.settings_dict["NAME"], "receipt from another database"
    assert native["venue_id"] == str(order.tab.venue_id), "receipt from another Venue"
    assert str(order.tab_id) == native["original_tab_id"]
    assert Order.objects.filter(tab_id=order.tab_id).count() == 1, "duplicate order"
    items = OrderItem.objects.filter(order=order)
    expected_count = 2 if mode == "compose" else 1
    expected_products = {fixture["product_id"], fixture["kitchen_product_id"]} if mode == "compose" else {fixture["product_id"]}
    assert items.count() == expected_count, "duplicate or missing item"
    assert {str(item.product_id) for item in items} == expected_products, "foreign fixture product"
    assert all(item.state == "READY" for item in items), "Web did not persist READY for every station"
    charges = Charge.objects.filter(tab=order.tab)
    assert charges.count() == expected_count, "duplicate or missing charge"
    expected_total = 1700 if mode == "compose" else 700
    assert sum(charge.amount_cents for charge in charges) == expected_total
    assert Payment.objects.filter(tab=order.tab).count() == 0, "unconfirmed payment"
    summary = {
        "database": connection.settings_dict["NAME"],
        "venue_id": str(order.tab.venue_id),
        "status": "PASS",
        "scenario": ("Android committed POST / force-stop / same-key replay" if mode == "recovery" else "Android production MainActivity Compose confirmation") + " -> Web Bar UI PREPARING then READY",
        "native_receipt": native_path,
        "original_order_id": str(order.pk),
        "original_tab_id": str(order.tab_id),
        "original_order_item_ids": [str(item.pk) for item in items],
        "final_item_states": [item.state for item in items],
        "orders": 1,
        "items": expected_count,
        "charges": expected_count,
        "payments": 0,
        "charge_cents": expected_total,
        "scope": "disposable PostgreSQL, emulator and browser; not a physical/payment/fiscal pilot",
    }
    out = Path("artifacts/android-web-cross-surface.json" if mode == "recovery" else "artifacts/android-compose-web-sql.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("PASS: native Android -> Web Bar -> SQL READY; Order=1 Item=1 Charge=1 Payment=0")
