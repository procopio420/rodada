#!/usr/bin/env python3
"""Read-only PostgreSQL proof of the opt-in production MainActivity Compose journey."""
import json
import os
from pathlib import Path
import subprocess

from cross_surface_fixture import require_disposable_database, require_connected_database, require_fixture_order

require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django

django.setup()
from django.db import connection
from modules.ordering.models import Order

require_connected_database(connection)
fixture = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
assert fixture["database"] == connection.settings_dict["NAME"]
order = Order.objects.get(tab__venue_id=fixture["venue_id"], tab__display_label=os.environ["RODADA_COMPOSE_TAB_LABEL"])
require_fixture_order(order, fixture)
with connection.cursor() as cursor:
    cursor.execute("SELECT count(*) FROM ordering_order WHERE tab_id = %s", [order.tab_id])
    assert cursor.fetchone() == (1,)
    cursor.execute("SELECT id, product_id, quantity, state FROM ordering_orderitem WHERE order_id = %s", [order.pk])
    rows = cursor.fetchall()
    assert len(rows) == 2 and {str(r[1]) for r in rows} == {fixture["product_id"], fixture["kitchen_product_id"]}
    assert all(r[2:] == (1, "NEW") for r in rows), rows
    cursor.execute("SELECT id, amount_cents FROM ledger_charge WHERE tab_id = %s", [order.tab_id])
    charges = cursor.fetchall()
    assert len(charges) == 2 and sorted(c[1] for c in charges) == [700, 1000]
    cursor.execute("SELECT count(*) FROM ledger_payment WHERE tab_id = %s", [order.tab_id])
    assert cursor.fetchone() == (0,)
summary = {
    "sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "database": connection.settings_dict["NAME"], "venue_id": fixture["venue_id"],
    "venue_slug": fixture["venue_slug"], "result": "PASS", "native_ui": "production MainActivity Compose",
    "original_order_id": str(order.pk), "original_tab_id": str(order.tab_id),
    "original_order_item_ids": [str(r[0]) for r in rows], "charge_ids": [str(c[0]) for c in charges],
    "product_ids": {"BAR": fixture["product_id"], "KITCHEN": fixture["kitchen_product_id"]},
    "orders": 1, "order_items": 2, "charges": 2, "payments": 0,
    "tab_label": order.tab.display_label, "initial_state": "NEW",
}
Path("artifacts/android-compose-order.json").write_text(json.dumps(summary, indent=2) + "\n")
print("PASS: independent PostgreSQL readback of Compose-origin Order=1 Items=2 NEW Charges=1700 Payment=0")
