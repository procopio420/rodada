import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access", "0003_access_invalidation_event"),
        ("catalog", "0001_initial"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tab",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("display_label", models.CharField(blank=True, max_length=120)),
                ("state", models.CharField(choices=[("OPEN", "Open"), ("REQUIRES_ACTION", "Requires action"), ("SETTLING", "Settling"), ("CLOSED", "Closed"), ("CANCELLED", "Cancelled")], default="OPEN", max_length=24)),
                ("version", models.PositiveIntegerField(default=1)),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("opened_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="tabs_opened", to="access.staffmember")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tabs", to="venue.venue")),
            ],
            options={"ordering": ("-opened_at", "id")},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source", models.CharField(choices=[("STAFF", "Staff"), ("CASHIER", "Cashier"), ("GUEST", "Guest")], max_length=16)),
                ("status", models.CharField(choices=[("CONFIRMED", "Confirmed"), ("CANCELLED", "Cancelled")], default="CONFIRMED", max_length=16)),
                ("confirmed_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="orders_confirmed", to="access.staffmember")),
                ("tab", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="ordering.tab")),
            ],
            options={"ordering": ("confirmed_at", "id")},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("product_name_snapshot", models.CharField(max_length=160)),
                ("unit_price_cents", models.PositiveIntegerField()),
                ("quantity", models.PositiveIntegerField()),
                ("state", models.CharField(choices=[("NEW", "New"), ("ACCEPTED", "Accepted"), ("PREPARING", "Preparing"), ("READY", "Ready"), ("PICKED_UP", "Picked up"), ("DELIVERED", "Delivered"), ("CANCELLED", "Cancelled")], default="NEW", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("preparing_at", models.DateTimeField(blank=True, null=True)),
                ("ready_at", models.DateTimeField(blank=True, null=True)),
                ("picked_up_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="items", to="ordering.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="catalog.product")),
            ],
            options={"ordering": ("created_at", "id")},
        ),
        migrations.AddIndex(
            model_name="tab",
            index=models.Index(fields=["venue", "state", "opened_at"], name="ordering_tab_v_state_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["tab", "confirmed_at"], name="ordering_ord_tab_time_idx"),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(condition=Q(("quantity__gt", 0)), name="ordering_item_quantity_positive"),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(fields=["order", "state"], name="ordering_item_ord_state_idx"),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(fields=["product", "created_at"], name="ordering_item_product_idx"),
        ),
    ]
