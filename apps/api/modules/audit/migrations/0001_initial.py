import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("access", "0001_initial"),
        ("venue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=100)),
                ("entity_type", models.CharField(blank=True, max_length=100)),
                ("entity_id", models.CharField(blank=True, max_length=100)),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("actor_session", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="access.staffsession")),
                ("actor_staff", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="access.staffmember")),
                ("device", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="access.deviceregistration")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="venue.venue")),
            ],
            options={"ordering": ("occurred_at", "id")},
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["venue", "occurred_at"], name="audit_v_occurred_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["event_type", "occurred_at"], name="audit_type_occ_idx"),
        ),
    ]
