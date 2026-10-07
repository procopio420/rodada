from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("ordering", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="order",
            name="request_fingerprint",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.UniqueConstraint(
                condition=~Q(idempotency_key=""),
                fields=("tab", "idempotency_key"),
                name="ordering_order_tab_idempotency_unique",
            ),
        ),
    ]
