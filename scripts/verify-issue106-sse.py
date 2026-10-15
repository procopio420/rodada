#!/usr/bin/env python3
"""Reconcile SSE-only fault independently against the same disposable PostgreSQL."""
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
from modules.ordering.models import Order, OrderItem
from modules.ledger.models import Charge, Payment
from modules.realtime.models import OutboxEvent
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
r = json.loads(Path("artifacts/sse-browser.json").read_text())
assert r["sha"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
assert r["database_instance_id"] == f["database_instance_id"] == database_instance_identity(connection)
order = Order.objects.get(pk=r["order_id"], tab_id=r["tab_id"], tab__venue_id=f["venue_id"])
assert Order.objects.filter(tab_id=order.tab_id).count() == 1
item = OrderItem.objects.get(pk=r["item_id"], order=order, product_id=f["kitchen_product_id"])
assert item.state == "NEW" and item.preparing_at is None and item.ready_at is None
assert OrderItem.objects.filter(order=order).count() == 1
assert Charge.objects.filter(tab_id=order.tab_id).count() == 1
assert Charge.objects.get(tab_id=order.tab_id).amount_cents == 1000
assert not Payment.objects.filter(tab_id=order.tab_id).exists()
events = OutboxEvent.objects.filter(venue_id=f["venue_id"], aggregate_id=str(order.pk), event_type="order.confirmed")
assert events.count() == 1
assert r["cuts"] > 0 and r["cursor_before"] == r["cursor_resumed"]
r.update(sql_independent=True, outbox_ids=[str(e.pk) for e in events], orders=1, charges=1, payments=0)
Path("artifacts/sse-sql.json").write_text(json.dumps(r, indent=2)+"\n")
print("PASS: SSE-only cut, unique NEW Order/Charge and outbox; no automatic prepare or Payment")
