# ruff: noqa: RUF012
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("hospitality", "0002_tab_assignment_allows_guest_actor"),
        ("ordering", "0002_order_idempotency"),
    ]

    operations = [
        migrations.CreateModel(
            name="GuestSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("generation", models.PositiveIntegerField()),
                ("token_digest", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_reason", models.CharField(blank=True, max_length=120)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "occupancy",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="guest_sessions",
                        to="hospitality.tableoccupancy",
                    ),
                ),
                (
                    "tab",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="guest_sessions",
                        to="ordering.tab",
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="guest_sessions",
                        to="hospitality.table",
                    ),
                ),
            ],
            options={"ordering": ("-created_at", "id")},
        ),
        migrations.AddIndex(
            model_name="guestsession",
            index=models.Index(fields=["table", "generation"], name="guest_session_table_gen_idx"),
        ),
        migrations.AddIndex(
            model_name="guestsession",
            index=models.Index(
                fields=["occupancy", "revoked_at"], name="guest_session_occ_rev_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="guestsession",
            index=models.Index(fields=["expires_at"], name="guest_session_expiry_idx"),
        ),
    ]
