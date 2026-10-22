from typing import ClassVar
from django.db import migrations

class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("venue", "0012_attendance_telemetry"),
        ("venue", "0012_venue_print_agents_enabled"),
    ]
    operations: ClassVar = []
