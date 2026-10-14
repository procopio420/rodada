#!/usr/bin/env python3
"""Independent SQL reconciliation after real Android instrumentation -> Web Bar UI.

Only read an explicitly disposable database. This script must never seed a Venue,
simulate a payment, or accept a browser-generated order as native evidence.
"""
import json
import os
from pathlib import Path

if os.getenv("POSTGRES_DB") != "rodada_android_post_drop":
    raise SystemExit("Refusing verification outside dedicated rodada_android_post_drop PostgreSQL")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()

from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, OrderItem

native = json.loads(Path("artifacts/android-real-post-drop.json").read_text())
assert native["result"] == "PASS" and native["original_key_preserved"]
order = Order.objects.get(pk=native["original_order_id"])
assert str(order.tab_id) == native["original_tab_id"]
assert Order.objects.filter(tab_id=order.tab_id).count() == 1, "duplicate order"
items = OrderItem.objects.filter(order=order)
assert items.count() == 1, "duplicate item"
item = items.get()
assert item.state == "READY", f"Web did not persist READY; actual {item.state}"
charges = Charge.objects.filter(tab=order.tab)
assert charges.count() == 1, "duplicate charge"
assert charges.get().amount_cents == 700
assert Payment.objects.filter(tab=order.tab).count() == 0, "unconfirmed payment"
summary = {
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
