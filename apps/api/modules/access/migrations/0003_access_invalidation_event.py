import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0002_session_tokens_and_pin_throttle"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessInvalidationEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=64)),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invalidation_events",
                        to="access.deviceregistration",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invalidation_events",
                        to="access.staffsession",
                    ),
                ),
                (
                    "staff_member",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_invalidation_events",
                        to="access.staffmember",
                    ),
                ),
                (
                    "venue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_invalidation_events",
                        to="venue.venue",
                    ),
                ),
            ],
            options={"ordering": ("id",)},
        ),
        migrations.AddIndex(
            model_name="accessinvalidationevent",
            index=models.Index(fields=["venue", "id"], name="access_inv_venue_id_idx"),
        ),
        migrations.AddIndex(
            model_name="accessinvalidationevent",
            index=models.Index(fields=["staff_member", "id"], name="access_inv_staff_id_idx"),
        ),
        migrations.AddIndex(
            model_name="accessinvalidationevent",
            index=models.Index(fields=["session", "id"], name="access_inv_session_id_idx"),
        ),
        migrations.AddIndex(
            model_name="accessinvalidationevent",
            index=models.Index(fields=["device", "id"], name="access_inv_device_id_idx"),
        ),
    ]
