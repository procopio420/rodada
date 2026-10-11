from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("venue", "0005_operationalalertpolicy_guest_request_danger_seconds_and_more")]

    operations = [migrations.CreateModel(
        name="StationConfiguration",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("station", models.CharField(choices=[("BAR", "Bar"), ("KITCHEN", "Kitchen")], max_length=16)),
            ("enabled", models.BooleanField(default=True)),
            ("version", models.PositiveIntegerField(default=1)),
            ("label", models.CharField(blank=True, max_length=120)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="venue.venue")),
        ],
        options={"constraints": [
            models.UniqueConstraint(fields=("venue", "station"), name="venue_station_unique"),
            models.CheckConstraint(condition=models.Q(station__in=("BAR", "KITCHEN")), name="venue_station_valid"),
            models.CheckConstraint(condition=models.Q(version__gte=1), name="venue_station_version_positive"),
        ]},
    )]
