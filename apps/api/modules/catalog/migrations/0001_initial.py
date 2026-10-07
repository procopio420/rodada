import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access", "0003_access_invalidation_event"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("normalized_name", models.CharField(editable=False, max_length=180)),
                ("price_cents", models.PositiveIntegerField()),
                ("active", models.BooleanField(default=True)),
                ("fulfillment_station", models.CharField(choices=[("BAR", "Bar"), ("KITCHEN", "Kitchen")], max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="products", to="venue.venue")),
            ],
            options={"ordering": ("name", "id")},
        ),
        migrations.CreateModel(
            name="ProductAvailability",
            fields=[
                ("product", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="availability", serialize=False, to="catalog.product")),
                ("state", models.CharField(choices=[("AVAILABLE", "Available"), ("UNAVAILABLE", "Unavailable")], default="AVAILABLE", max_length=16)),
                ("version", models.PositiveIntegerField(default=1)),
                ("changed_at", models.DateTimeField(auto_now=True)),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="product_availability_changes", to="access.staffmember")),
            ],
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(fields=("venue", "normalized_name"), name="catalog_unique_product_name_per_venue"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["venue", "active", "fulfillment_station"], name="catalog_v_active_station_idx"),
        ),
        migrations.AddIndex(
            model_name="productavailability",
            index=models.Index(fields=["state", "changed_at"], name="catalog_avail_state_idx"),
        ),
    ]
