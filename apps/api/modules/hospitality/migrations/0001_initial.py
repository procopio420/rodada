import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q

from modules.hospitality.models import generate_public_token


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access", "0003_access_invalidation_event"),
        ("ordering", "0002_order_idempotency"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Table",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("label", models.CharField(max_length=80)),
                (
                    "public_token",
                    models.CharField(default=generate_public_token, max_length=64, unique=True),
                ),
                ("access_generation", models.PositiveIntegerField(default=1)),
                (
                    "guest_ordering_mode",
                    models.CharField(
                        choices=[
                            ("DISABLED", "Disabled"),
                            ("JOIN_ACTIVE", "Join active"),
                            ("DIRECT", "Direct"),
                        ],
                        default="DISABLED",
                        max_length=16,
                    ),
                ),
                ("guest_ordering_blocked", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("AVAILABLE", "Available"),
                            ("OCCUPIED", "Occupied"),
                            ("DIRTY", "Dirty"),
                            ("CLEANING", "Cleaning"),
                            ("OUT_OF_SERVICE", "Out of service"),
                        ],
                        default="AVAILABLE",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "venue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tables",
                        to="venue.venue",
                    ),
                ),
            ],
            options={"ordering": ("label", "id")},
        ),
        migrations.CreateModel(
            name="TableOccupancy",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("generation", models.PositiveIntegerField()),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("cleaning_started_at", models.DateTimeField(blank=True, null=True)),
                ("ready_at", models.DateTimeField(blank=True, null=True)),
                (
                    "cleaning_started_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="table_occupancies_cleaning_started",
                        to="access.staffmember",
                    ),
                ),
                (
                    "ready_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="table_occupancies_ready",
                        to="access.staffmember",
                    ),
                ),
                (
                    "released_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="table_occupancies_released",
                        to="access.staffmember",
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="occupancies",
                        to="hospitality.table",
                    ),
                ),
            ],
            options={"ordering": ("-started_at", "id")},
        ),
        migrations.CreateModel(
            name="TabOccupancyAssignment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tab_occupancy_assignments",
                        to="access.staffmember",
                    ),
                ),
                (
                    "occupancy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tab_assignments",
                        to="hospitality.tableoccupancy",
                    ),
                ),
                (
                    "tab",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="occupancy_assignments",
                        to="ordering.tab",
                    ),
                ),
            ],
            options={"ordering": ("assigned_at", "id")},
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(fields=["venue", "status"], name="hospitality_table_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="table",
            constraint=models.UniqueConstraint(
                fields=("venue", "label"), name="hospitality_table_venue_label_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="tableoccupancy",
            index=models.Index(
                fields=["table", "started_at"], name="hospitality_occ_table_time_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="tableoccupancy",
            constraint=models.UniqueConstraint(
                condition=Q(("released_at__isnull", True)),
                fields=("table",),
                name="hospitality_one_active_occupancy",
            ),
        ),
        migrations.AddIndex(
            model_name="taboccupancyassignment",
            index=models.Index(
                fields=["occupancy", "released_at"], name="hospitality_assignment_occ_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="taboccupancyassignment",
            constraint=models.UniqueConstraint(
                condition=Q(("released_at__isnull", True)),
                fields=("occupancy", "tab"),
                name="hospitality_one_tab_per_active_occ",
            ),
        ),
        migrations.AddConstraint(
            model_name="taboccupancyassignment",
            constraint=models.UniqueConstraint(
                condition=Q(("released_at__isnull", True)),
                fields=("tab",),
                name="hospitality_one_active_occ_per_tab",
            ),
        ),
    ]
