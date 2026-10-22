from typing import ClassVar
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies: ClassVar = [("venue", "0011_venue_table_service_rollout")]
    operations: ClassVar = [
        migrations.CreateModel(name="AttendanceTelemetryDaily", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("business_date", models.DateField()),
            ("platform", models.CharField(max_length=8)),
            ("event", models.CharField(max_length=24)),
            ("count", models.PositiveIntegerField(default=0)),
            ("duration_total_ms", models.PositiveBigIntegerField(default=0)),
            ("duration_observed", models.PositiveIntegerField(default=0)),
            ("venue", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="venue.venue")),
        ], options={"constraints": [models.UniqueConstraint(fields=["venue", "business_date", "platform", "event"], name="ux2_telemetry_daily_unique")]}),
        migrations.CreateModel(name="AttendanceTelemetryReceipt", fields=[
            ("id", models.UUIDField(primary_key=True, serialize=False)),
            ("received_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ("venue", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="venue.venue")),
        ]),
    ]
