# ruff: noqa: RUF012
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("ledger", "0004_payment_confirmation_timestamp_invariant")]

    operations = [
        migrations.CreateModel(
            name="PaymentAttempt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("idempotency_key", models.CharField(max_length=120)),
                ("provider", models.CharField(max_length=80)),
                ("provider_attempt_id", models.CharField(blank=True, max_length=160)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("CREATED", "Created"),
                            ("PROCESSING", "Processing"),
                            ("CONFIRMATION_PENDING", "Confirmation pending"),
                            ("CONFIRMED", "Confirmed"),
                            ("FAILED", "Failed"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="CREATED",
                        max_length=24,
                    ),
                ),
                ("error_code", models.CharField(blank=True, max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "payment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_attempts",
                        to="ledger.payment",
                    ),
                ),
            ],
            options={"ordering": ("started_at", "id")},
        ),
        migrations.CreateModel(
            name="ProviderEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("provider", models.CharField(max_length=80)),
                ("provider_event_id", models.CharField(max_length=160)),
                ("payload_hash", models.CharField(max_length=64)),
                ("event_type", models.CharField(max_length=100)),
                (
                    "processing_status",
                    models.CharField(
                        choices=[
                            ("RECEIVED", "Received"),
                            ("APPLIED", "Applied"),
                            ("IGNORED", "Ignored"),
                            ("FAILED", "Failed"),
                        ],
                        default="RECEIVED",
                        max_length=16,
                    ),
                ),
                ("processing_error", models.CharField(blank=True, max_length=160)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "attempt",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_events",
                        to="payment_provider.paymentattempt",
                    ),
                ),
                (
                    "payment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_events",
                        to="ledger.payment",
                    ),
                ),
            ],
            options={"ordering": ("received_at", "id")},
        ),
        migrations.AddConstraint(
            model_name="paymentattempt",
            constraint=models.UniqueConstraint(
                fields=("payment", "idempotency_key"), name="provider_attempt_payment_key_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="paymentattempt",
            index=models.Index(
                fields=["provider", "provider_attempt_id"], name="provider_attempt_ref_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="paymentattempt",
            index=models.Index(fields=["payment", "status"], name="payprov_attempt_stat_idx"),
        ),
        migrations.AddConstraint(
            model_name="providerevent",
            constraint=models.UniqueConstraint(
                fields=("provider", "provider_event_id"), name="provider_event_provider_id_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="providerevent",
            index=models.Index(fields=["payment", "received_at"], name="payprov_event_time_idx"),
        ),
    ]
