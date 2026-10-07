import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access", "0003_access_invalidation_event"),
        ("ordering", "0002_order_idempotency"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderCorrection",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("CANCEL_ITEM", "Cancel item"),
                            ("CUSTOMER_CHANGED_MIND", "Customer changed mind"),
                            ("WRONG_ITEM_ENTERED", "Wrong item entered"),
                            ("STATION_MISTAKE", "Station mistake"),
                            ("CUSTOMER_REJECTED", "Customer rejected"),
                            ("REMAKE", "Remake"),
                            ("REPLACEMENT", "Replacement"),
                            ("COMPLAINT", "Complaint"),
                            ("OTHER_EXCEPTION", "Other exception"),
                        ],
                        max_length=32,
                    ),
                ),
                ("stage_at_request", models.CharField(max_length=16)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("REQUESTED", "Requested"),
                            ("APPLIED", "Applied"),
                            ("REJECTED", "Rejected"),
                        ],
                        default="REQUESTED",
                        max_length=16,
                    ),
                ),
                ("reason_code", models.CharField(max_length=80)),
                ("reason_text", models.CharField(blank=True, max_length=400)),
                (
                    "financial_disposition",
                    models.CharField(
                        choices=[
                            ("NONE", "None"),
                            ("REVERSE_OPEN_RESPONSIBILITY", "Reverse open responsibility"),
                            ("COURTESY_REPLACEMENT", "Courtesy replacement"),
                            ("REFUND_REQUIRED", "Refund required"),
                            ("MANUAL_REVIEW_REQUIRED", "Manual review required"),
                        ],
                        default="NONE",
                        max_length=32,
                    ),
                ),
                ("idempotency_key", models.CharField(max_length=120)),
                ("request_fingerprint", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("applied_at", models.DateTimeField(blank=True, null=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_corrections_approved",
                        to="access.staffmember",
                    ),
                ),
                (
                    "original_order_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="corrections",
                        to="ordering.orderitem",
                    ),
                ),
                (
                    "replacement_order_item",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="replacement_correction",
                        to="ordering.orderitem",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_corrections_requested",
                        to="access.staffmember",
                    ),
                ),
                (
                    "venue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_corrections",
                        to="venue.venue",
                    ),
                ),
            ],
            options={"ordering": ("created_at", "id")},
        ),
        migrations.CreateModel(
            name="WasteMarker",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("PREPARED_NOT_SERVED", "Prepared not served"),
                            ("REMAKE_DISCARDED", "Remake discarded"),
                            ("SPOILAGE", "Spoilage"),
                            ("OTHER", "Other"),
                        ],
                        max_length=32,
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                ("reason", models.CharField(blank=True, max_length=400)),
                ("occurred_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "correction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="waste_markers",
                        to="corrections.ordercorrection",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="waste_markers_created",
                        to="access.staffmember",
                    ),
                ),
                (
                    "order_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="waste_markers",
                        to="ordering.orderitem",
                    ),
                ),
                (
                    "venue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="waste_markers",
                        to="venue.venue",
                    ),
                ),
            ],
            options={"ordering": ("occurred_at", "id")},
        ),
        migrations.AddIndex(
            model_name="ordercorrection",
            index=models.Index(
                fields=["venue", "original_order_item", "created_at"],
                name="correction_origin_time_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ordercorrection",
            index=models.Index(
                fields=["replacement_order_item"], name="correction_replacement_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="ordercorrection",
            constraint=models.UniqueConstraint(
                condition=~Q(idempotency_key=""),
                fields=("original_order_item", "idempotency_key"),
                name="correction_item_idempotency_unique",
            ),
        ),
        migrations.AddIndex(
            model_name="wastemarker",
            index=models.Index(
                fields=["venue", "order_item", "occurred_at"],
                name="correction_waste_item_time_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="wastemarker",
            constraint=models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="correction_waste_quantity_positive",
            ),
        ),
    ]
