from typing import ClassVar
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("venue", "0015_attendance_telemetry_steps"),
        ("ordering", "0006_orderitem_customization_snapshot_and_more"),
    ]
    operations: ClassVar = [
        migrations.AddField(
            model_name="attendancetelemetryreceipt",
            name="event",
            field=models.CharField(max_length=24, default=""),
        ),
        migrations.CreateModel(
            name="ProductionScreenReceipt",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("station", models.CharField(max_length=8, choices=[("BAR", "Bar"), ("KITCHEN", "Kitchen")])),
                ("observed_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="venue.venue")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="ordering.order")),
            ],
            options={"constraints": [models.UniqueConstraint(
                fields=["venue", "order", "station"], name="ux2_screen_first_order_station",
            )]},
        ),
    ]
