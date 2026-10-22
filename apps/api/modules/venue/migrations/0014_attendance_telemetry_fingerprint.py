from typing import ClassVar
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies: ClassVar = [("venue", "0013_merge_attendance_print")]
    operations: ClassVar = [
        migrations.AddField(
            model_name="attendancetelemetryreceipt",
            name="fingerprint",
            field=models.CharField(default="", max_length=64),
        ),
    ]
