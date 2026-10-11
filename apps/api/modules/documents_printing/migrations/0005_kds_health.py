from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("documents_printing", "0004_immutable_document_postgres"),
        ("access", "0003_access_invalidation_event"),
    ]

    operations = [
        migrations.CreateModel(
            name="KdsStationHealth",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("station", models.CharField(choices=[("BAR", "Bar"), ("KITCHEN", "Kitchen")], max_length=16)),
                ("version", models.PositiveIntegerField(default=1)),
                ("heartbeat_ttl_seconds", models.PositiveIntegerField(default=30)),
                ("failure_threshold_seconds", models.PositiveIntegerField(default=90)),
                ("recovery_threshold_seconds", models.PositiveIntegerField(default=60)),
                ("state", models.CharField(choices=[("HEALTHY", "Healthy"), ("SUSPECT", "Suspect"), ("UNHEALTHY", "Unhealthy"), ("RECOVERING", "Recovering")], default="SUSPECT", max_length=16)),
                ("monitoring_started_at", models.DateTimeField()),
                ("last_queue_observed_at", models.DateTimeField(null=True)),
                ("suspect_since", models.DateTimeField(null=True)),
                ("recovery_since", models.DateTimeField(null=True)),
                ("recovery_observed_at", models.DateTimeField(null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="venue.venue")),
            ],
            options={"constraints": [
                models.UniqueConstraint(fields=("venue", "station"), name="printing_kds_station_unique"),
                models.CheckConstraint(condition=models.Q(station__in=("BAR", "KITCHEN")), name="printing_kds_station_valid"),
                models.CheckConstraint(condition=models.Q(heartbeat_ttl_seconds__gte=5, heartbeat_ttl_seconds__lte=300, failure_threshold_seconds__gte=30, failure_threshold_seconds__lte=3600, recovery_threshold_seconds__gte=30, recovery_threshold_seconds__lte=3600), name="printing_kds_thresholds_valid"),
            ]},
        ),
        migrations.CreateModel(
            name="KdsDeviceHeartbeat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("station", models.CharField(choices=[("BAR", "Bar"), ("KITCHEN", "Kitchen")], max_length=16)),
                ("seen_at", models.DateTimeField()),
                ("queue_observed_at", models.DateTimeField(null=True)),
                ("client_version", models.CharField(blank=True, max_length=64)),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="access.deviceregistration")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="access.staffsession")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="venue.venue")),
            ],
            options={"constraints": [
                models.UniqueConstraint(fields=("venue", "station", "device"), name="printing_kds_device_unique"),
                models.CheckConstraint(condition=models.Q(station__in=("BAR", "KITCHEN")), name="printing_kds_device_station_valid"),
            ]},
        ),
    ]
