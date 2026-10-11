from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("venue", "0006_stationconfiguration")]
    operations = [
        migrations.AddField(model_name="venue", name="guest_mutations_blocked", field=models.BooleanField(default=False, db_default=False)),
        migrations.AddField(model_name="venue", name="guest_policy_version", field=models.PositiveIntegerField(default=1, db_default=1)),
    ]
