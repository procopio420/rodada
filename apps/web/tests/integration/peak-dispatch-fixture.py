"""Only disposable Web E2E data; persisted queues, no simulated HTTP payloads."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "api"))
os.environ["DJANGO_SETTINGS_MODULE"] = "rodada_api.settings"
import django
django.setup()
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from modules.venue.models import Venue
from modules.catalog.models import Product
from modules.hospitality.models import Zone, Table, TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Tab, Order, OrderItem
from modules.ledger.models import Charge, Payment, LedgerAdjustment
from modules.dispatch.models import DispatchTask
from modules.dispatch.services import ensure_delivery_task_for_ready_order_item

config = settings.DATABASES["default"]
assert os.environ.get("RODADA_E2E_POSTGRES") == "1"
assert config["NAME"] == "rodada_web_e2e" and config["HOST"] in {"127.0.0.1", "localhost"}
venue = Venue.objects.get(slug="web-e2e")
with transaction.atomic():
    if not Tab.objects.filter(venue=venue, display_label="Peak 50").exists():
        products = [Product.objects.create(venue=venue, name="Peak Bar", price_cents=0, fulfillment_station="BAR"),
                    Product.objects.create(venue=venue, name="Peak Kitchen", price_cents=0, fulfillment_station="KITCHEN")]
        zones = [Zone.objects.create(venue=venue, label=f"Peak zone {i + 1}") for i in range(5)]
        for i in range(50):
            table = Table.objects.create(venue=venue, label=f"Peak {i + 1:02}", zone=zones[i % 5], status="OCCUPIED")
            occupancy = TableOccupancy.objects.create(table=table, generation=table.access_generation)
            tab = Tab.objects.create(venue=venue, display_label=f"Peak {i + 1}")
            TabOccupancyAssignment.objects.create(occupancy=occupancy, tab=tab)
            order = Order.objects.create(tab=tab, source="STAFF")
            product = products[i % 2]
            item = OrderItem.objects.create(order=order, product=product, product_name_snapshot=product.name,
                fulfillment_station_snapshot=product.fulfillment_station, unit_price_cents=0, quantity=i % 3 + 1,
                state="READY", ready_at=timezone.now())
            Charge.objects.create(tab=tab, order_item=item, amount_cents=0)
            ensure_delivery_task_for_ready_order_item(item_id=item.id)
            DispatchTask.objects.create(venue=venue, task_type="SERVICE_REQUEST", destination_table=table,
                destination_occupancy=occupancy, destination_label=f"Mesa {table.label}")

print(json.dumps({
    "tasks": list(DispatchTask.objects.filter(venue=venue).order_by("id").values("id", "state", "claimed_by_id", "completed_at", "order_item_id")),
    "items": list(OrderItem.objects.filter(order__tab__venue=venue).order_by("id").values("id", "state", "quantity")),
    "charges": list(Charge.objects.filter(tab__venue=venue).order_by("id").values("id", "tab_id", "amount_cents")),
    "payments": list(Payment.objects.filter(tab__venue=venue).order_by("id").values("id", "amount_cents", "status")),
    "adjustments": list(LedgerAdjustment.objects.filter(tab__venue=venue).order_by("id").values("id", "amount_cents")),
}, default=str))
