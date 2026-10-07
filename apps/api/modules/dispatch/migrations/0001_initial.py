import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access", "0003_access_invalidation_event"),
        ("hospitality", "0001_initial"),
        ("ordering", "0002_order_idempotency"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DispatchTask",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "task_type",
                    models.CharField(
                        choices=[
                            ("SERVICE_REQUEST", "Service request"),
                            ("DELIVERY", "Delivery"),
                            ("BILL_REQUEST", "Bill request"),
                            ("EXCEPTION", "Exception"),
                        ],
                        max_length=24,
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("OPEN", "Open"),
                            ("CLAIMED", "Claimed"),
                            ("DONE", "Done"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="OPEN",
                        max_length=16,
                    ),
                ),
                ("destination_label", models.CharField(blank=True, max_length=160)),
                ("priority", models.SmallIntegerField(default=0)),
                ("claimed_at", models.DateTimeField(blank=True, null=True)),
                ("ready_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "completion_source",
                    models.CharField(
                        blank=True,
                        choices=[("MANUAL", "Manual")],
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "claimed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="claimed_dispatch_tasks",
                        to="access.staffmember",
                    ),
                ),
                (
                    "completed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="completed_dispatch_tasks",
                        to="access.staffmember",
                    ),
                ),
                (
                    "destination_occupancy",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatch_tasks",
                        to="hospitality.tableoccupancy",
                    ),
                ),
                (
                    "destination_table",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatch_tasks",
                        to="hospitality.table",
                    ),
                ),
                (
                    "order_item",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="delivery_task",
                        to="ordering.orderitem",
                    ),
                ),
                (
                    "venue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatch_tasks",
                        to="venue.venue",
                    ),
                ),
            ],
            options={"ordering": ("-priority", "ready_at", "created_at", "id")},
        ),
        migrations.AddIndex(
            model_name="dispatchtask",
            index=models.Index(
                fields=["venue", "task_type", "state", "priority", "ready_at"],
                name="dispatch_queue_idx",
            ),
        ),
    ]
