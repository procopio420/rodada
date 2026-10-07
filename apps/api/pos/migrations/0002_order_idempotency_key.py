from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("pos", "0001_initial")]
    operations = [
        migrations.AddField(model_name="order", name="idempotency_key", field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddConstraint(model_name="order", constraint=models.UniqueConstraint(condition=Q(idempotency_key__isnull=False), fields=("tab", "idempotency_key"), name="unique_order_command_per_tab")),
    ]
