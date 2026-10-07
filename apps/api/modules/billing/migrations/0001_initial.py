import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access", "0003_access_invalidation_event"),
        ("ordering", "0001_initial"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Charge",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("CONSUMPTION", "Consumption")], default="CONSUMPTION", max_length=20)),
                ("amount_cents", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order_item", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="charge", to="ordering.orderitem")),
                ("tab", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="charges", to="ordering.tab")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="charges", to="venue.venue")),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("amount_cents", models.PositiveIntegerField()),
                ("method", models.CharField(choices=[("TAP_TO_PAY", "Tap to Pay"), ("PIX", "Pix"), ("CARD_ONLINE", "Card online"), ("CASH", "Cash"), ("EXTERNAL_TERMINAL", "External terminal"), ("OTHER", "Other")], max_length=24)),
                ("status", models.CharField(choices=[("CREATED", "Created"), ("PENDING", "Pending"), ("PROCESSING", "Processing"), ("AUTHORIZED", "Authorized"), ("CONFIRMATION_PENDING", "Confirmation pending"), ("CONFIRMED", "Confirmed"), ("FAILED", "Failed"), ("CANCELLED", "Cancelled"), ("PARTIALLY_REFUNDED", "Partially refunded"), ("REFUNDED", "Refunded")], default="CREATED", max_length=24)),
                ("idempotency_key", models.CharField(max_length=120)),
                ("provider", models.CharField(blank=True, max_length=64)),
                ("external_reference", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="payments_created", to="access.staffmember")),
                ("tab", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="ordering.tab")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="venue.venue")),
            ],
        ),
        migrations.CreateModel(
            name="Adjustment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("ITEM_DISCOUNT", "Item discount"), ("TAB_DISCOUNT", "Tab discount"), ("COURTESY", "Courtesy"), ("SERVICE_CHARGE", "Service charge"), ("SERVICE_CHARGE_REDUCTION", "Service charge reduction"), ("CORRECTION", "Correction"), ("REVERSAL", "Reversal")], max_length=32)),
                ("scope", models.CharField(choices=[("CHARGE", "Charge"), ("TAB", "Tab")], max_length=16)),
                ("calculation_type", models.CharField(choices=[("PERCENTAGE", "Percentage"), ("FIXED", "Fixed"), ("DERIVED", "Derived")], max_length=16)),
                ("requested_value", models.IntegerField(blank=True, null=True)),
                ("effect_cents", models.IntegerField()),
                ("reason_code", models.CharField(blank=True, max_length=64)),
                ("reason_text", models.CharField(blank=True, max_length=240)),
                ("idempotency_key", models.CharField(max_length=120)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="adjustments_approved", to="access.staffmember")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="adjustments_created", to="access.staffmember")),
                ("source_charge", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="adjustments", to="billing.charge")),
                ("supersedes_adjustment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="superseding_adjustments", to="billing.adjustment")),
                ("tab", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="adjustments", to="ordering.tab")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="adjustments", to="venue.venue")),
            ],
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(condition=Q(("amount_cents__gte", 0)), name="billing_charge_amount_nonnegative"),
        ),
        migrations.AddIndex(
            model_name="charge",
            index=models.Index(fields=["tab", "created_at"], name="billing_charge_tab_time_idx"),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(condition=Q(("amount_cents__gt", 0)), name="billing_payment_amount_positive"),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.UniqueConstraint(fields=("venue", "idempotency_key"), name="billing_unique_payment_idempotency"),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["tab", "status", "created_at"], name="billing_pay_tab_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="adjustment",
            constraint=models.UniqueConstraint(fields=("venue", "idempotency_key"), name="billing_unique_adjustment_idempotency"),
        ),
        migrations.AddIndex(
            model_name="adjustment",
            index=models.Index(fields=["tab", "created_at"], name="billing_adj_tab_time_idx"),
        ),
        migrations.AddIndex(
            model_name="adjustment",
            index=models.Index(fields=["source_charge", "created_at"], name="billing_adj_charge_idx"),
        ),
    ]
