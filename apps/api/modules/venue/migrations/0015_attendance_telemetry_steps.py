from typing import ClassVar
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: ClassVar = [("venue", "0014_attendance_telemetry_fingerprint")]
    operations: ClassVar = [
        migrations.AddField(
            model_name="attendancetelemetrydaily",
            name="essential_steps_total",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="attendancetelemetrydaily",
            name="essential_steps_observed",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="attendancetelemetryreceipt",
            name="intent_ref",
            field=models.CharField(db_index=True, default="", max_length=64),
        ),
    ]
