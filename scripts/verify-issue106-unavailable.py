#!/usr/bin/env python3
"""Independent PostgreSQL reconciliation of #106/E2E-05 real UI stale-cart denials."""
import json
import os
from pathlib import Path
import subprocess

from cross_surface_fixture import (
    database_instance_identity,
    require_connected_database,
    require_disposable_database,
)

require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()

from django.db import connection
from modules.catalog.models import Product
from modules.ordering.models import Order, OrderItem
from modules.ledger.models import Charge, Payment

require_connected_database(connection)
fixture = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
instance = database_instance_identity(connection)

for source in ("cart", "staff"):
    receipt = json.loads(Path("artifacts/unavailable-" + source + "-browser.json").read_text())
    assert receipt["sha"] == sha
    assert receipt["database_instance_id"] == fixture["database_instance_id"] == instance
    assert receipt["venue_id"] == fixture["venue_id"]
    assert receipt["denial"] == {"status": 409, "code": "PRODUCTS_NOT_CONFIRMABLE"}
    product = Product.objects.get(pk=receipt["product_id"], venue_id=fixture["venue_id"])
    assert product.availability.state == "UNAVAILABLE"
    tab_id = receipt["tab_id"]
    assert not Order.objects.filter(tab_id=tab_id).exists()
    assert not OrderItem.objects.filter(order__tab_id=tab_id).exists()
    assert not Charge.objects.filter(tab_id=tab_id).exists()
    assert not Payment.objects.filter(tab_id=tab_id).exists()
    receipt.update(sql_independent=True, orders=0, items=0, charges=0, payments=0)
    Path("artifacts/unavailable-" + source + "-sql.json").write_text(json.dumps(receipt, indent=2) + "\n")
print("PASS: Guest and Web stale carts rejected on one disposable PostgreSQL with zero financial effects")
