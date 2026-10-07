from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0003_backfill_legacy_payment_confirmed_at"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(status__in=("CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED"))
                    | models.Q(confirmed_at__isnull=False)
                ),
                name="ledger_confirmed_payment_has_timestamp",
            ),
        ),
    ]
