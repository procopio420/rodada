from typing import ClassVar

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: ClassVar = [("venue", "0010_domain_database_lifecycle")]
    operations: ClassVar = [
        migrations.AddField(model_name="venue", name="table_service_enabled", field=models.BooleanField(default=False, db_default=False)),
        migrations.AddField(model_name="venue", name="table_service_version", field=models.PositiveIntegerField(default=1, db_default=1)),
    ]
